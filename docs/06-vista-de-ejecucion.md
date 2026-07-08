<div align="center">
  <img src="images/VARIACION%203%20NEGRO.png" alt="FONBEC Logo" width="250">
</div>

# 6. Vista de Ejecución

Esta sección documenta los flujos del sistema en tiempo de ejecución a través de los escenarios más representativos. Los diagramas de secuencia muestran cómo interactúan los bloques de construcción (capa web, casos de uso, dominio, infraestructura y servicios externos) durante la ejecución de cada caso de uso.

---

## 6.1 Escenario: Login de Usuario

**Descripción:** Un usuario con cuenta activa inicia sesión con email y contraseña. El sistema valida la identidad contra Supabase Auth y verifica que el perfil local exista en la base de datos antes de establecer la sesión.

```mermaid
sequenceDiagram
    actor Usuario as Usuario (Navegador)
    participant Web as Capa Web<br/>(auth.py)
    participant UC as LoginUseCase
    participant AuthSvc as SupabaseAuthService
    participant SupaAuth as Supabase Auth
    participant Repo as SQLAlchemyUsuarioRepository
    participant DB as Supabase PostgreSQL

    Usuario->>Web: POST /auth/login {email, password}
    Web->>Web: before_request → g.db_session = SessionLocal()
    Web->>UC: LoginUseCase(auth_service, repo)
    UC->>UC: Validar email/password no vacíos
    UC->>AuthSvc: login(email, password)
    AuthSvc->>SupaAuth: sign_in_with_password({email, password})
    SupaAuth-->>AuthSvc: {access_token, refresh_token, user}
    AuthSvc-->>UC: {access_token, refresh_token, user}
    UC->>UC: Extraer rol de user_metadata
    UC->>Repo: obtener_por_email(email)
    Repo->>DB: SELECT FROM [tabla_por_rol] WHERE email = ?
    DB-->>Repo: Usuario entity
    Repo-->>UC: usuario_db (objeto de dominio)

    alt Perfil no encontrado en BD local
        UC->>AuthSvc: logout(access_token)
        AuthSvc->>SupaAuth: sign_out()
        UC-->>Web: raise ValueError("perfil eliminado localmente")
        Web-->>Usuario: redirect /auth/login + flash error
    else Login exitoso
        UC-->>Web: {access_token, refresh_token, rol, usuario}
        Web->>Web: session["access_token"] = ...<br/>session["rol"] = ...<br/>session["user_id"] = ...
        Web-->>Usuario: redirect /[rol]/dashboard
    end

    Web->>Web: teardown → db_session.commit() + close()
```

**Notas:**
- El rol se obtiene de `user_metadata` de Supabase Auth, no de la base de datos local, para mantener la fuente de verdad de identidad en Supabase.
- Si el perfil no existe en la BD local (cuenta eliminada localmente), se aplica el patrón Saga: se invalida la sesión en Supabase Auth antes de rechazar el login.

---

## 6.2 Escenario: Invitación de Usuario y Completar Registro (PKCE)

**Descripción:** El Administrador invita a un nuevo usuario. El candidato recibe un email con enlace de activación, completa su perfil y establece su contraseña.

```mermaid
sequenceDiagram
    actor Admin as Administrador
    actor Candidato as Candidato (Navegador)
    participant Web as Capa Web<br/>(admin.py / auth.py)
    participant InvitarUC as InvitarUsuarioUseCase
    participant CompletarUC as CompletarRegistroUseCase
    participant AuthSvc as SupabaseAuthService
    participant SupaAuth as Supabase Auth
    participant EmailSvc as Servicio de Email (SMTP)
    participant Repo as SQLAlchemyUsuarioRepository
    participant DB as Supabase PostgreSQL

    Admin->>Web: POST /admin/invitar {email, rol}
    Web->>InvitarUC: execute(actor_admin, email, rol)
    InvitarUC->>InvitarUC: Verificar que actor_admin es Administrador
    InvitarUC->>Repo: obtener_por_email(email)
    Repo->>DB: SELECT WHERE email = ?
    DB-->>Repo: None (email no registrado)
    InvitarUC->>AuthSvc: invitar_usuario(email, rol)
    AuthSvc->>SupaAuth: admin.invite_user_by_email(email, {rol, redirect_to})
    SupaAuth->>EmailSvc: Enviar email de invitación con enlace PKCE
    EmailSvc-->>Candidato: Email con enlace de activación
    SupaAuth-->>AuthSvc: user_id
    AuthSvc-->>InvitarUC: user_id
    InvitarUC-->>Web: user_id
    Web-->>Admin: redirect /admin/directorio + flash success

    Note over Candidato,Web: El candidato hace clic en el enlace del email

    Candidato->>Web: GET /auth/callback?code=PKCE_CODE
    Web->>AuthSvc: intercambiar_codigo(code)
    AuthSvc->>SupaAuth: exchange_code_for_session({auth_code})
    SupaAuth-->>AuthSvc: {access_token, refresh_token}
    AuthSvc-->>Web: {access_token, refresh_token}
    Web->>Web: session["temp_access_token"] = access_token
    Web-->>Candidato: render_template("auth/completar_registro.html")

    Candidato->>Web: POST /auth/set-password {nombre, apellido, password, ...}
    Web->>CompletarUC: ejecutar(access_token, password, datos_usuario)
    CompletarUC->>AuthSvc: obtener_usuario(access_token)
    AuthSvc->>SupaAuth: get_user(access_token)
    SupaAuth-->>AuthSvc: {user_id, email, user_metadata.rol}
    CompletarUC->>AuthSvc: establecer_contrasena(access_token, password, refresh_token)
    AuthSvc->>SupaAuth: update_user({password})
    CompletarUC->>Repo: guardar(nuevo_usuario_dominio)
    Repo->>DB: INSERT INTO [tabla_por_rol]
    DB-->>Repo: OK
    CompletarUC-->>Web: OK
    Web-->>Candidato: redirect / + flash "Registro completado"
```

---

## 6.3 Escenario: Carga del Formulario Académico con Documentos (Patrón Saga)

**Descripción:** Un Becario actualiza su formulario académico y adjunta uno o más documentos PDF. El sistema aplica el patrón Saga para garantizar que los archivos subidos a Storage sean revertidos si la persistencia en BD falla.

```mermaid
sequenceDiagram
    actor Becario as Becario (Navegador)
    participant Web as Capa Web<br/>(becario.py)
    participant UC as CU03_LlenarActualizar<br/>FormularioAcademico
    participant Repo as SQLAlchemyBecarioRepository
    participant StorSvc as SupabaseStorageServiceImpl
    participant Dom as Becario (Dominio)<br/>+ DatosAcademicos
    participant Storage as Supabase Storage
    participant DB as Supabase PostgreSQL

    Becario->>Web: POST /becario/academico/editar {campos + archivos PDF}
    Web->>Web: before_request → g.db_session = SessionLocal()
    Web->>UC: ejecutar(becario_id, datos, archivos)
    UC->>Repo: obtener_por_id(becario_id)
    Repo->>DB: SELECT (joinedload datos_academicos + documentos)
    DB-->>Repo: Becario entity completo
    Repo-->>UC: becario

    UC->>UC: Validar archivos (solo PDF, max 5MB)
    UC->>Dom: becario.llenar_actualizar_formulario_academico(datos)
    Dom->>Dom: actualizar_datos(**datos) — valida campos
    Dom->>Dom: revaluar_estado() — INCOMPLETO o PENDIENTE_REVISION

    loop Para cada archivo en archivos
        UC->>StorSvc: subir_documento(file, becario_id, tipo, nombre)
        StorSvc->>Storage: storage.upload(path, bytes, upsert=true)
        Storage-->>StorSvc: OK
        StorSvc-->>UC: public_url
        UC->>Dom: datos_academicos.agregar_documento(DocumentoAcademico)
        Dom->>Dom: revaluar_estado() — re-evalúa completitud
    end

    UC->>Repo: guardar(becario)
    Repo->>DB: session.add(becario) + flush()

    alt DB flush falla
        DB-->>Repo: Exception
        Repo-->>UC: Exception
        Note over UC: Patrón Saga — compensación
        loop Para cada URL subida
            UC->>StorSvc: eliminar_documento_por_url(url)
            StorSvc->>Storage: storage.remove([path])
        end
        UC-->>Web: raise Exception
        Web-->>Becario: redirect /becario/academico + flash error
    else Persistencia exitosa
        UC-->>Web: datos_academicos_to_dict(...)
        Web->>Web: teardown → db_session.commit() + close()
        Web-->>Becario: redirect /becario/academico + flash success
    end
```

**Notas:**
- El dominio se muta **antes** de subir archivos a Storage. Si la validación de negocio falla (ej. estado `APROBADO`), no se realiza ninguna operación en la nube.
- La compensación Saga es *best-effort*: si el rollback de Storage también falla, el error se silencia para no enmascarar el error original de BD.

---

## 6.4 Escenario: Auditoría de Datos Académicos por el Mediador (CU-08)

**Descripción:** El Mediador aprueba o rechaza los datos académicos de un Becario en estado `PENDIENTE_REVISION`. La máquina de estados del dominio valida la transición antes de persistirla.

```mermaid
sequenceDiagram
    actor Mediador as Mediador (Navegador)
    participant Web as Capa Web<br/>(mediador.py)
    participant UC as AuditarDatosAcademicosUseCase
    participant MedRepo as SQLAlchemyMediadorRepository
    participant Dom as Mediador (Dominio)
    participant BecDom as Becario.DatosAcademicos (Dominio)
    participant DB as Supabase PostgreSQL

    Mediador->>Web: POST /mediador/becario/{id}/auditoria {decision, observaciones}
    Web->>Web: before_request → g.db_session = SessionLocal()
    Web->>UC: execute(id_mediador, id_becario, decision, observaciones)

    UC->>MedRepo: obtener_por_id(id_mediador)
    MedRepo->>DB: SELECT mediador + joinedload(lista_becarios → datos_academicos)
    DB-->>MedRepo: Mediador + Becarios completos
    MedRepo-->>UC: mediador

    UC->>Dom: mediador.seleccionar_becario(id_becario)
    Dom->>Dom: Verificar que id_becario ∈ lista_becarios
    Dom-->>UC: becario (o ValueError "sin permisos")

    alt Rechazar sin observaciones
        UC-->>Web: raise ValueError("observaciones obligatorias al rechazar")
        Web-->>Mediador: redirect + flash error
    end

    UC->>Dom: mediador.auditar_datos_academicos_becario(becario, decision, observaciones)
    Dom->>BecDom: Verificar estado == PENDIENTE_REVISION
    
    alt Aprobar
        Dom->>BecDom: actualizar_estado(APROBADO)
        Dom->>BecDom: observaciones = None; fecha_observacion = None
    else Rechazar
        Dom->>BecDom: actualizar_estado(PENDIENTE_MODIFICAR)
        Dom->>BecDom: observaciones = texto; fecha_observacion = now()
    end

    UC->>MedRepo: guardar(mediador)
    MedRepo->>DB: session.add(mediador) + flush()
    Note over DB: SQLAlchemy cascadea el cambio de estado<br/>en datos_academicos del Becario asociado
    DB-->>MedRepo: OK

    UC-->>Web: datos_academicos_to_dict(becario.datos_academicos)
    Web->>Web: teardown → db_session.commit() + close()
    Web-->>Mediador: redirect /mediador/becario/{id} + flash success
```

**Notas:**
- La autorización de acceso al Becario se realiza **en el dominio** (`mediador.seleccionar_becario()`): si el Becario no está en `lista_becarios` del Mediador, se lanza `ValueError` sin llegar a consultar la BD directamente.
- El cambio de estado en `DatosAcademicos` se propaga a la BD gracias a la relación de cascada configurada en el mapeo imperativo (`cascade="all, delete-orphan"`).

---

## 6.5 Escenario: Ciclo de Vida de la Sesión de Base de Datos (middleware)

**Descripción:** Muestra cómo el middleware de `app.py` gestiona el ciclo de vida de la sesión SQLAlchemy en cada request HTTP.

```mermaid
sequenceDiagram
    participant Flask as Flask Runtime
    participant MW as Middleware<br/>(before_request / teardown)
    participant Session as SQLAlchemy Session
    participant Controller as Controlador (Blueprint)
    participant UC as Caso de Uso
    participant DB as Supabase PostgreSQL

    Flask->>MW: before_request
    MW->>Session: SessionLocal() — nueva sesión
    Session-->>MW: g.db_session
    MW->>Session: query(Usuario).filter_by(user_id)
    Session->>DB: SELECT usuario actual desde sesión Flask
    DB-->>Session: usuario entity
    MW-->>Flask: g.usuario_actual disponible

    Flask->>Controller: Despachar request a Blueprint
    Controller->>Controller: Instanciar repositorio(g.db_session)
    Controller->>UC: ejecutar(...)
    UC->>Session: session.add() / session.query() / session.flush()
    Session->>DB: SQL DML/DQL
    DB-->>Session: resultado
    UC-->>Controller: DTO resultado
    Controller-->>Flask: render_template() / redirect()

    Flask->>MW: teardown_appcontext
    alt Sin excepción
        MW->>Session: commit()
        Session->>DB: COMMIT
    else Con excepción
        MW->>Session: rollback()
        Session->>DB: ROLLBACK
    end
    MW->>Session: close()
    Session-->>MW: Sesión liberada al pool
```

**Notas:**
- `session.flush()` en los repositorios pre-valida los cambios sin cerrar la transacción. El `commit()` final lo realiza el middleware al cerrar el request.
- Si el controlador lanza una excepción no manejada, `teardown_appcontext` realiza automáticamente el `rollback()`, garantizando la consistencia de la BD.

---

*Sección anterior: [05 — Vista de Bloques](./05-vista-de-bloques.md)*  
*Sección siguiente: [07 — Vista de Despliegue](./07-vista-de-despliegue.md)*
