<div align="center">
  <img src="images/VARIACION%203%20NEGRO.png" alt="FONBEC Logo" width="250">
</div>

# 5. Vista de Bloques

Esta sección describe la descomposición estática del sistema FONBEC en bloques de construcción. Se presentan tres niveles de zoom: el sistema completo como caja blanca (Nivel 1), cada capa arquitectónica con sus componentes internos (Nivel 2) y los componentes más complejos con su estructura interna (Nivel 3).

---

## 5.1 Nivel 1 — Sistema General (Caja Blanca)

El sistema FONBEC se descompone en cuatro capas arquitectónicas con dependencias estrictamente unidireccionales. Ninguna capa puede importar artefactos de una capa de mayor jerarquía.

### Diagrama de Nivel 1

```mermaid
graph TD
    subgraph Navegador["Navegador Web del Usuario"]
        browser["HTTP/HTTPS — Forms HTML"]
    end

    subgraph FONBEC["Sistema FONBEC"]
        direction TB
        web["Capa Web<br/><code>src/web/</code><br/><i>Blueprints Flask, parseo de requests,<br/>inyección de dependencias</i>"]
        app["Capa de Aplicación<br/><code>src/application/</code><br/><i>23 Casos de Uso + Protocolos DIP</i>"]
        domain["Capa de Dominio<br/><code>src/domain/</code><br/><i>Actores, Entidades, Enums<br/>— Python puro, sin dependencias externas</i>"]
        infra["Capa de Infraestructura<br/><code>src/infrastructure/</code><br/><i>Repositorios SQLAlchemy, Auth Service,<br/>Storage Service</i>"]

        web -->|"Instancia y ejecuta"| app
        app -->|"Invoca métodos de dominio"| domain
        app -->|"Depende de protocolos<br/>(nunca de implementaciones)"| infra
    end

    subgraph Supabase["Supabase Cloud"]
        db[("PostgreSQL")]
        auth["Auth Service<br/>(Admin API + PKCE)"]
        storage["Storage<br/>(bucket documentos_academicos)"]
    end

    browser -->|"GET / POST (HTML Forms)"| web
    web -->|"HTML renderizado (Jinja2)"| browser
    infra -->|"TCP/IP — psycopg2"| db
    infra -->|"HTTPS REST — supabase-py"| auth
    infra -->|"HTTPS REST — supabase-py"| storage
```

### Bloques de construcción del Nivel 1

| Bloque | Responsabilidad | Ubicación |
| :--- | :--- | :--- |
| **Capa Web** | Recibir requests HTTP, parsear formularios, gestionar sesiones, inyectar dependencias y devolver respuestas HTML o redirecciones. | `src/web/` |
| **Capa de Aplicación** | Orquestar los flujos de negocio a través de casos de uso. Depende de protocolos (interfaces) para acceder a infraestructura. No contiene lógica de negocio propia. | `src/application/` |
| **Capa de Dominio** | Contener todas las reglas de negocio del sistema. Entidades puras de Python sin dependencias de framework, ORM ni servicios externos. | `src/domain/` |
| **Capa de Infraestructura** | Implementar los protocolos de la capa de aplicación: acceso a BD, autenticación y almacenamiento de archivos. | `src/infrastructure/` |

---

## 5.2 Nivel 2 — Capa de Dominio (Caja Blanca)

La capa de dominio es el núcleo del sistema. Contiene las reglas de negocio en forma de clases Python puras, organizadas en actores y entidades de dominio.

### Diagrama de Nivel 2 — Dominio

```mermaid
graph TD
    subgraph Domain["Capa de Dominio — src/domain/"]
        direction TB

        subgraph Actors["actors/"]
            usuario["Usuario (ABC)<br/><i>Base abstracta de todos los actores</i><br/>id_usuario, nombre, apellido, email<br/>telefono, edad, sexo, direccion, rol"]
            referente["Referente (ABC)<br/><i>Base abstracta de Tutor y Mediador</i><br/>lista_becarios<br/>listar_becarios_asignados()"]
            becario["Becario ⬡<br/><i>Aggregate Root</i><br/>nivel_cursado, puntero_tutor<br/>puntero_mediador, puntero_padrino<br/>lista_tutorias, lista_envios_cartas"]
            tutor["Tutor<br/>rol = 'tutor'<br/>seleccionar_becario()<br/>visualizar_datos_academicos()<br/>get_datos_contacto()"]
            mediador["Mediador<br/>rol = 'mediador'<br/>seleccionar_becario()<br/>auditar_datos_academicos_becario()<br/>get_datos_contacto()"]
            admin["Administrador<br/>rol = 'administrador'"]
        end

        subgraph Entities["domain_entities/"]
            datos_ac["DatosAcademicos<br/><i>Máquina de estados reactiva</i><br/>estado_verificacion (EstadoVerificacion)<br/>revaluar_estado()<br/>actualizar_datos()<br/>agregar_documento()<br/>eliminar_documento()"]
            doc_ac["DocumentoAcademico<br/>tipo_documento<br/>ruta_archivo, fecha_carga"]
            tutoria["Tutoria<br/>estado (EstadoTutoria)<br/>fecha_hora<br/>cambiar_estado()"]
            envio["EnvioCarta<br/>estado (EstadoEnvioCarta)<br/>fecha_envio<br/>actualizar_estado_envio()"]
            padrino["Padrino<br/><i>Sin acceso al sistema</i><br/>nombre, apellido<br/>email, telefono, direccion"]
        end

        subgraph Enums["enums.py"]
            ev["EstadoVerificacion<br/>VACIO | INCOMPLETO<br/>PENDIENTE_REVISION<br/>PENDIENTE_MODIFICAR | APROBADO"]
            et["EstadoTutoria<br/>PROGRAMADA | REALIZADA<br/>AUSENTE | CANCELADA"]
            ec["EstadoEnvioCarta<br/>PROGRAMADA | REPROGRAMADA<br/>CANCELADA | ENVIADA"]
            nc["NivelCursado<br/>PRIMARIO | SECUNDARIO<br/>TERCIARIO | UNIVERSITARIO"]
        end

        usuario -->|hereda| referente
        usuario -->|hereda| becario
        usuario -->|hereda| admin
        referente -->|hereda| tutor
        referente -->|hereda| mediador

        becario -->|"composición (1:1)"| datos_ac
        datos_ac -->|"composición (1:N)"| doc_ac
        becario -->|"colección (1:N)"| tutoria
        becario -->|"colección (1:N)"| envio
        becario -->|"puntero (0..1)"| tutor
        becario -->|"puntero (0..1)"| mediador
        becario -->|"puntero (0..1)"| padrino

        datos_ac -->|usa| ev
        tutoria -->|usa| et
        envio -->|usa| ec
        becario -->|usa| nc
    end
```

### Descripción de los componentes del Dominio

| Componente | Tipo | Responsabilidad |
| :--- | :--- | :--- |
| `Usuario` | Clase abstracta | Define la identidad base de todos los actores del sistema. Declara `visualizar_datos_academicos()` como método abstracto, garantizando que cada actor concrete su propia vista. |
| `Referente` | Clase abstracta | Extiende `Usuario` con `lista_becarios` y `seleccionar_becario()`. Base compartida de `Tutor` y `Mediador`. |
| `Becario` ⬡ | **Aggregate Root** | Entidad central del modelo. Contiene por composición `DatosAcademicos` y por colección `Tutoria` y `EnvioCarta`. Expone los punteros hacia `Tutor`, `Mediador` y `Padrino`. Toda navegación al resto del agregado pasa por `Becario`. |
| `Tutor` | Clase concreta | Referente responsable de las tutorías. Puede visualizar datos académicos pero no tiene potestad de auditoría. |
| `Mediador` | Clase concreta | Referente con potestad de auditoría académica (CU-08: aprobar/rechazar). Gestiona el calendario de envíos de cartas. |
| `Administrador` | Clase concreta | Actor de gestión global. No hereda de `Referente`; tiene visibilidad sobre todos los actores del sistema. |
| `DatosAcademicos` | Entidad de dominio | Implementa la máquina de estados del proceso de verificación académica. Valida sus propias transiciones y guarda RN-02 en cuatro puntos de control independientes. |
| `DocumentoAcademico` | Entidad de dominio | Representa un archivo PDF adjunto. Tiene `tipo_documento` como clave de identificación dentro del agregado. |
| `Tutoria` | Entidad de dominio | Registro de una sesión de tutoría con su estado y fecha. |
| `EnvioCarta` | Entidad de dominio | Registro de un envío de carta al Padrino con su estado y fecha. |
| `Padrino` | Entidad de dominio | Entidad de referencia sin acceso al sistema. Gestionada íntegramente por el Administrador. |

---

## 5.3 Nivel 2 — Capa de Aplicación (Caja Blanca)

La capa de aplicación orquesta los flujos de negocio. Contiene los casos de uso y los protocolos (interfaces) que desacoplan el dominio de la infraestructura.

### Diagrama de Nivel 2 — Aplicación

```mermaid
graph LR
    subgraph App["Capa de Aplicación — src/application/"]
        subgraph UC["use_cases/ — 23 casos de uso"]
            uc_auth["Autenticación<br/>login<br/>completar_registro<br/>recuperar_contrasena<br/>cambiar_contrasena<br/>actualizar_perfil"]
            uc_admin["Administrador<br/>invitar_usuario<br/>eliminar_becario<br/>eliminar_referente<br/>CU03_Admin_GestionarVinculaciones<br/>CU04_Admin_GestionarPadrinos<br/>CU05_Admin_ListarActores<br/>CU06_Admin_ObtenerDatosBecario<br/>CU06_Admin_VerDatosAcademicos"]
            uc_bec["Becario<br/>CU03_LlenarActualizarFormulario<br/>CU03_EliminarDocumentoAcademico<br/>cu04_visualizar_datos_academicos"]
            uc_ref["Tutor / Mediador<br/>CU02_ContactarReferente<br/>CU05_Tutor_ListarBecarios<br/>CU05_Mediador_ListarBecarios<br/>CU06_Tutor_ObtenerDatosBecario<br/>CU06_Mediador_ObtenerDatosBecario<br/>CU08_Mediador_AuditarDatosAcademicos"]
        end

        subgraph Protocols["protocols.py — Contratos DIP"]
            p_bec["BecarioRepositoryProtocol"]
            p_tutor["TutorRepositoryProtocol"]
            p_med["MediadorRepositoryProtocol"]
            p_usr["UsuarioRepositoryProtocol"]
            p_pad["PadrinoRepositoryProtocol"]
            p_auth["AuthServiceProtocol"]
            p_stor["IStorageServiceProtocol"]
        end

        subgraph DTO["dto_mapper.py"]
            dto["usuario_to_dict()<br/>datos_academicos_to_dict()"]
        end
    end

    uc_auth --> p_auth
    uc_auth --> p_usr
    uc_admin --> p_usr
    uc_admin --> p_auth
    uc_admin --> p_pad
    uc_bec --> p_bec
    uc_bec --> p_stor
    uc_ref --> p_tutor
    uc_ref --> p_med
    uc_auth --> dto
    uc_bec --> dto
    uc_ref --> dto
```

---

## 5.4 Nivel 2 — Capa de Infraestructura (Caja Blanca)

La capa de infraestructura implementa los contratos definidos en los protocolos de la capa de aplicación.

### Diagrama de Nivel 2 — Infraestructura

```mermaid
graph TD
    subgraph Infra["Capa de Infraestructura — src/infrastructure/"]
        subgraph Repos["Repositorios"]
            rb["SQLAlchemyBecarioRepository<br/>implements BecarioRepositoryProtocol"]
            rt["SQLAlchemyTutorRepository<br/>implements TutorRepositoryProtocol"]
            rm["SQLAlchemyMediadorRepository<br/>implements MediadorRepositoryProtocol"]
            ru["SQLAlchemyUsuarioRepository<br/>implements UsuarioRepositoryProtocol"]
            rp["SQLAlchemyPadrinoRepository<br/>implements PadrinoRepositoryProtocol"]
        end

        subgraph Auth["Autenticación"]
            auth_svc["SupabaseAuthService<br/>implements AuthServiceProtocol<br/>invitar_usuario()<br/>intercambiar_codigo()<br/>login() / logout()<br/>eliminar_usuario_auth()"]
        end

        subgraph Storage["Almacenamiento"]
            stor_svc["SupabaseStorageServiceImpl<br/>implements IStorageServiceProtocol<br/>subir_documento()<br/>eliminar_documento_por_url()<br/>bucket: documentos_academicos"]
        end

        subgraph Schema["Esquema y Mapeo"]
            schema["schema.py<br/>Tablas SQLAlchemy Core<br/>7 tablas — Concrete Table Inheritance"]
            mapping["mapping.py<br/>map_imperatively()<br/>Binding dominio ↔ tablas<br/>cascade + lazy='joined'"]
            db_mod["database.py<br/>create_engine() — pool_pre_ping<br/>SessionLocal — sessionmaker<br/>init_db() — arranca el mapeo"]
        end

        rb & rt & rm & ru & rp -->|"SQLAlchemy Session"| db_mod
        schema -->|"define tablas"| mapping
        mapping -->|"registra"| db_mod
    end

    db_mod -->|"TCP/IP psycopg2"| ext_db[("Supabase PostgreSQL")]
    auth_svc -->|"HTTPS REST supabase-py"| ext_auth["Supabase Auth"]
    stor_svc -->|"HTTPS REST supabase-py"| ext_stor["Supabase Storage"]
```

### Descripción del esquema de base de datos (Concrete Table Inheritance)

| Tabla física | Entidad de dominio | Descripción |
| :--- | :--- | :--- |
| `becarios` | `Becario` | Todos los campos de `Usuario` + `nivel_cursado`, `tutor_id`, `mediador_id`, `padrino_id` (FKs). |
| `tutores` | `Tutor` | Campos de `Usuario` + `rol`. |
| `mediadores` | `Mediador` | Campos de `Usuario` + `rol`. |
| `administradores` | `Administrador` | Campos de `Usuario` + `rol`. |
| `padrinos` | `Padrino` | `id_padrino`, `nombre`, `apellido`, `email`, `telefono`, `direccion`. |
| `datos_academicos` | `DatosAcademicos` | FK a `becarios`. `ARRAY(String)` para `materias_a_cursar` y `materias_adeudadas`. `unique=True` en `becario_id` (relación 1:1). |
| `documentos_academicos` | `DocumentoAcademico` | FK a `datos_academicos`. `cascade="all, delete-orphan"`. |
| `tutorias` | `Tutoria` | FK a `becarios`. `cascade="all, delete-orphan"`. |
| `envios_cartas` | `EnvioCarta` | FK a `becarios`. `cascade="all, delete-orphan"`. |

---

## 5.5 Nivel 2 — Capa Web (Caja Blanca)

La capa web expone la interfaz HTTP del sistema mediante Flask Blueprints. Cada Blueprint agrupa las rutas de un actor específico.

### Blueprints registrados

| Blueprint | URL prefix | Rutas clave | Actor |
| :--- | :--- | :--- | :--- |
| `auth_bp` | `/auth` | `/login`, `/logout`, `/callback`, `/set-password`, `/recuperar-contrasena`, `/nueva-contrasena`, `/perfil` | Todos |
| `admin_bp` | `/admin` | `/dashboard`, `/directorio/<rol>`, `/padrinos`, `/padrinos/nuevo`, `/invitar`, `/becarios/<id>/detalle`, `/becarios/<id>/vinculaciones/vincular` | Administrador |
| `becario_bp` | `/becario` | `/dashboard`, `/academico`, `/academico/editar`, `/academico/documento/eliminar` | Becario |
| `tutor_bp` | `/tutor` | `/dashboard`, `/mis-becarios`, `/becario/<id>` | Tutor |
| `mediador_bp` | `/mediador` | `/dashboard`, `/mis-becarios`, `/becario/<id>`, `/becario/<id>/auditoria` | Mediador |

### Middleware de ciclo de vida (app.py)

```
before_request:
    g.db_session = SessionLocal()          ← sesión fresca por request
    g.usuario_actual = cargar_usuario()    ← usuario autenticado desde sesión Flask

teardown_appcontext:
    if sin excepción → db_session.commit()
    if con excepción → db_session.rollback()
    db_session.close()
```

---

## 5.6 Nivel 3 — `DatosAcademicos` (Caja Blanca interna)

`DatosAcademicos` es el componente de mayor complejidad interna del dominio. Implementa una máquina de estados con validación de transiciones y reevaluación reactiva del estado.

### Diagrama de la máquina de estados de `DatosAcademicos`

```mermaid
stateDiagram-v2
    [*] --> VACIO : instanciación inicial

    VACIO --> INCOMPLETO : revaluar_estado() — datos incompletos
    VACIO --> PENDIENTE_REVISION : revaluar_estado() — datos completos

    INCOMPLETO --> INCOMPLETO : actualizar_datos() — sigue incompleto
    INCOMPLETO --> PENDIENTE_REVISION : actualizar_datos() — datos completos

    PENDIENTE_REVISION --> APROBADO : Mediador.auditar() — aprobar
    PENDIENTE_REVISION --> PENDIENTE_MODIFICAR : Mediador.auditar() — rechazar
    PENDIENTE_REVISION --> INCOMPLETO : revaluar_estado() — datos incompletos
    PENDIENTE_REVISION --> PENDIENTE_REVISION : revaluar_estado() — datos completos

    PENDIENTE_MODIFICAR --> INCOMPLETO : Becario actualiza — sigue incompleto
    PENDIENTE_MODIFICAR --> PENDIENTE_REVISION : Becario actualiza — datos completos

    APROBADO --> APROBADO : estado terminal (RN-02)
    note right of APROBADO : Ninguna mutación es posible.<br/>4 guardias en el dominio.
```

### Condición de completitud (`validar_completitud()`)

El estado `PENDIENTE_REVISION` solo se alcanza si se cumplen **todas** las condiciones siguientes:

| Condición | Campo |
| :--- | :--- |
| `nombre_carrera` no nulo | Campo texto |
| `anio_ingreso` no nulo | Año válido entre 1900 y el año actual |
| `anio_en_curso` no nulo | Valor entre 1 y 15 |
| `materias_a_cursar` no vacío | Lista con al menos un elemento |
| Documento `Programa` adjunto | `lista_documentos` contiene tipo `"Programa"` |
| Documento `CartaCompromiso` adjunto | `lista_documentos` contiene tipo `"CartaCompromiso"` |
| Documento `Inscripcion` adjunto | `lista_documentos` contiene tipo `"Inscripcion"` |

Si alguna condición no se cumple → estado `INCOMPLETO`.

---

*Sección anterior: [04 — Estrategia de Solución](./04-estrategia-solucion.md)*  
*Sección siguiente: [06 — Vista de Ejecución](./06-vista-de-ejecucion.md)*
