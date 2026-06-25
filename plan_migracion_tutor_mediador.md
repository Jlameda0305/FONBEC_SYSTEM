# Plan de Migración de Roles — Tutor ↔ Mediador (FONBEC)

> Plan de implementación estructurado por **fases** y **capas**. Deriva del análisis técnico previo y de la actualización de `AOO - DOO/AOO_FONBEC.md`.
>
> **Alcance:** planificación y trazabilidad de tareas. No contiene código de aplicación; incluye únicamente el script SQL de migración de datos (Fase B) como referencia transaccional.
>
> **Stack de referencia:** Flask + SQLAlchemy (mapeo imperativo) + Supabase (Postgres + Auth) + Jinja2/Argon. Test runner: `python3.14 -m unittest discover`.

---

## 0. Asignación Canónica de Responsabilidades

| Rol (`rol`) | Responsabilidades tras la migración | Origen de la lógica |
|---|---|---|
| **`Mediador`** (`"mediador"`) | Auditoría de datos académicos (CU-08) **+** envío de cartas (CU-13..15, futuro) | CU-08 se **transfiere** desde `Tutor` (cuerpo intacto). CU-13..15 ya vivían en `Mediador`. |
| **`Tutor`** (`"tutor"`) | Gestión de tutorías (CU-09..12, futuro) **+** visualización de datos académicos *sin* auditoría | CU-09..12 ya vivían en `Tutor`. Pierde `auditar_*` y las opciones Aprobar/Rechazar. |

**Invariantes preservados:** `Becario` como Aggregate Root; `puntero_tutor`/`puntero_mediador` y FKs `tutor_id`/`mediador_id` mantienen sus nombres (RN-01, RN-03); máquina de estados de `DatosAcademicos` **intacta**; mecanismo de auth (JWT + sesión Flask + `@requiere_rol`) **sin rediseño**.

**Nueva regla de negocio:** **RN-09** — la auditoría de datos académicos es responsabilidad exclusiva del `Mediador` (ya incorporada en `AOO_FONBEC.md`).

---

## 1. Cómo leer este plan

- **Fase A — Código** (sin impacto en datos): editable y desplegable de forma aislada.
- **Fase B — Datos y Acceso** (ventana de mantenimiento): swap de filas + claims + sesiones.
- **Fase C — Cierre y Documentación**: regresión, docs, diseño RLS futuro.

Dentro de cada fase, las tareas se agrupan por **capa** (Dominio, Aplicación, Infraestructura, Web, Presentación, Datos, Auth, Tests, Docs). Cada tarea indica `archivo:línea` y su criterio de aceptación.

### 1.1 Matriz de dependencias entre fases

```
Fase A (código)  ──►  Fase B (datos+auth, mantenimiento)  ──►  Fase C (cierre)
   E1→E5                  E6 + E7 (atómicas)                   E8 + E9
```

- Fase A **no depende** de Fase B: compila y pasa tests con mocks.
- Fase B **requiere** Fase A desplegada (los nuevos endpoints/clases deben existir antes de mover claims).
- Fase C **requiere** Fase B completada.

### 1.2 Convenciones

- `[RA]` = Criterio de Aceptación de la tarea.
- `[VER]` = Comando de verificación.
- `[RIESGO]` = Riesgo específico de la tarea.

---

## ASEO → Fase A — Código (sin impacto en datos)

> Objetivo: reasignar responsabilidades en dominio/aplicación/infra/web/UI y validar con tests sobre mocks. Desplegable sin tocar la base de datos ni Auth.

### A.1 Capa de Dominio

| Tarea | Archivo:línea | Detalle | `[RA]` |
|---|---|---|---|
| A.1.1 Trasladar `auditar_datos_academicos_becario` de `Tutor` a `Mediador` | `src/domain/actors/tutor.py:74-109` → `src/domain/actors/mediador.py` | Mover el método **con su cuerpo intacto** (no reescribir lógica). Conserva la validación de `Pendiente_Revision` y el seteo de `observaciones`/`fecha_observacion`. | `Mediador.auditar_datos_academicos_becario(becario, decision, obs)` aprueba/rechaza igual que antes; `Tutor` ya no expone el método. |
| A.1.2 Trasladar `visualizar_datos_academicos` (con opciones) a `Mediador` | `tutor.py:38-72` → `mediador.py` | Mover la implementación que expone `["aprobar","rechazar"]` en `Pendiente_Revision` (`tutor.py:67-68`). | `Mediador.visualizar_datos_academicos` muestra opciones; `Tutor` no. |
| A.1.3 Redefinir `Tutor.visualizar_datos_academicos` | `tutor.py:38-72` | Reemplazar por una versión **sin** opciones de auditoría (solo visualiza estado y datos). | En `Pendiente_Revision`, `Tutor` retorna `opciones=[]`. |
| A.1.4 Implementar `Mediador.seleccionar_becario` | `mediador.py:20-22` | Reemplazar el `NotImplementedError` por la selección real: carga datos del becario + calendario envíos + padrino + contacto tutor. | Devuelve el `Becario` si está en `lista_becarios`, else `ValueError`. |
| A.1.5 Conservar en `Tutor` | `tutor.py:23-36,122-131` | `seleccionar_becario`, `contactar_mediador_becario`, `get_datos_contacto`, métodos de tutorías (si existen como stub). | Sin cambios funcionales. |
| A.1.6 Revisar `Becario` | `src/domain/actors/becario.py:126-166` | `contacto_tutor`/`contacto_mediador`, `asignar_tutor`/`asignar_mediador` y punteros **sin cambios**. | Sin modificación. |

`[VER]` `python3.14 -m unittest discover -s tests -p "test_becario.py"`
`[RIESGO]` Si se reescribe (en vez de mover) el cuerpo de `auditar_*`, se pierde la garantía de "lógica intacta". Usar movimiento textual.

### A.2 Capa de Aplicación

| Tarea | Archivo:línea | Detalle | `[RA]` |
|---|---|---|---|
| A.2.1 Crear `MediadorRepositoryProtocol` | `src/application/protocols.py:15` (junto a `TutorRepositoryProtocol`) | Espejo del protocol de Tutor: `obtener_por_id(mediador_id) -> Optional[Mediador]`, `guardar(mediador) -> None`. Importar `Mediador` de `domain/actors/mediador.py`. | Protocol definido e importable. |
| A.2.2 Renombrar y reasignar CU-08 | `src/application/use_cases/CU08_Tutor_AuditarDatosAcademicos.py` | Renombrar a `CU08_Mediador_AuditarDatosAcademicos.py`. Cambiar dependencia de `TutorRepositoryProtocol` a `MediadorRepositoryProtocol`. El cuerpo del UC (invocar `actor.auditar_datos_academicos_becario`) se conserva. | UC depende de `MediadorRepositoryProtocol`; `Tutor` ya no se referencia. |
| A.2.3 Verificar CU-05 y CU-06 (Tutor) | `CU05_Tutor_ListarBecarios.py`, `CU06_Tutor_ObtenerDatosBecario.py` | **Sin cambio de actor**: el `Tutor` sigue listando becarios y obteniendo datos. Confirmar que el contacto empaquetado es `becario.puntero_mediador` (ya lo es, `CU06:58-66`). | Tests de CU-05/06 pasan sin cambios. |
| A.2.4 Verificar UC transversales | `CU02_ContactarReferente.py`, `CU03_Admin_GestionarVinculaciones.py`, `CU06_Admin_ObtenerDatosBecario.py`, `completar_registro.py:72-75` | Sin cambio lógico: usan `puntero_tutor`/`puntero_mediador` (conservados) e instanciación por string de rol. | Sin modificación; tests en verde. |

`[VER]` `python3.14 -m unittest discover -s tests -p "test_cu08_*"`

### A.3 Capa de Infraestructura

| Tarea | Archivo:línea | Detalle | `[RA]` |
|---|---|---|---|
| A.3.1 Crear `SQLAlchemyMediadorRepository` | `src/infrastructure/repositories.py:22-52` (junto a `SQLAlchemyTutorRepository`) | Espejo contra `tabla_mediadores`: `obtener_por_id` con `joinedload(Mediador.lista_becarios).joinedload(Becario.datos_academicos)`; `guardar` con `flush`. | Hidrata `Mediador` desde `mediadores` con eager loading (evita `DetachedInstanceError`). |
| A.3.2 Verificar mapeo | `src/infrastructure/mapping.py:48-64` | El mapeo `Mediador→tabla_mediadores` con `back_populates="puntero_mediador"` **se mantiene**. Confirmar tras A.1.4 que la relación sigue resolviendo. | `iniciar_mapeo()` sin errores; `test_mapping.py` en verde. |
| A.3.3 Ajustar `default` de `rol` (cosmético) | `src/infrastructure/schema.py:63,93` | Opcional: el `default` de la columna `rol` en `tutores`/`mediadores` ya coincide con el nombre de tabla. Sin cambio obligatorio. | — |
| A.3.4 Verificar repos genéricos | `repositories.py:124-138,174-180,203-218` | `obtener_por_id_y_rol`, `listar_usuarios`, `desvincular_referente` ya mapean ambos roles. **Sin cambios.** | — |

`[VER]` `python3.14 -m unittest discover -s tests -p "test_mapping.py"`

### A.4 Capa Web / Endpoints

| Tarea | Archivo:línea | Detalle | `[RA]` |
|---|---|---|---|
| A.4.1 Crear blueprint `mediador_bp` | nuevo `src/web/routes/mediador.py` | Migrar la **ruta de auditoría** (`tutor.py:84-108`) a `/mediador/becario/<id_becario>/auditoria` con `@requiere_rol("mediador")`. El handler construye `AuditarDatosAcademicosUseCase(SQLAlchemyMediadorRepository(...))`. | POST con sesión `mediador` → 200/302; con `tutor` → 403. |
| A.4.2 Ajustar `tutor.py` | `src/web/routes/tutor.py:84-108` | Eliminar la ruta de auditoría del blueprint tutor. Conservar `dashboard`, `mis_becarios`, `becario_detalle` (el Tutor sigue siendo referente con becarios). | `/tutor/...` sin ruta de auditoría. |
| A.4.3 Registrar blueprint | `src/web/app.py:82,87` | Importar y registrar `mediador_bp` junto a `tutor_bp`. | App inicia con los 5 blueprints. |
| A.4.4 Revisar redirect por rol | `src/web/routes/auth.py:62-63` | `rol == "tutor"` → `tutor.dashboard` **se mantiene** (el Tutor sigue teniendo dashboard). Agregar rama `rol == "mediador"` → `mediador.dashboard` (o reutilizar vista). | Login redirige al dashboard correcto por rol. |
| A.4.5 Revisar admin | `src/web/routes/admin.py:273-292` | Sin cambio: sigue listando `tutores` y `mediadores` por separado. | — |

`[VER]` `python3.14 -m unittest discover -s tests -p "test_web_*"`

### A.5 Capa de Presentación / Templates

| Tarea | Archivo:línea | Detalle | `[RA]` |
|---|---|---|---|
| A.5.1 Migrar bloque de auditoría | `src/templates/shared/becario_detalle.html:30,57` | `{% if g.usuario_actual.rol == 'tutor' %}` → `== 'mediador'`; `url_for('tutor.procesar_auditoria_academica', ...)` → `url_for('mediador.procesar_auditoria_academica', ...)`. | Las opciones Aprobar/Rechazar solo aparecen a `mediador`. |
| A.5.2 Revisar navegación | `includes/sidenav.html:43-49,62-69`; `includes/navigation.html:29-42` | Los redirects `url_for('tutor.dashboard')` por `rol=='tutor'` **se mantienen**. Agregar entrada/redirect para `mediador`. | Nav correcta por rol. |
| A.5.3 Revisar perfil | `auth/perfil.html:127-128` | Rama `rol == 'tutor'` se mantiene; agregar `mediador`. | — |
| A.5.4 Verificar tarjetas referentes | `becario/dashboard.html:57-84`; `becario/academico.html:49-81` | Las tarjetas "Tutor/Mediador Asignado" **sin cambio de etiqueta** (los nombres de rol se conservan). | — |
| A.5.5 Revisar `_actor_card.html` y `actores_lista.html` | `shared/partials/_actor_card.html:16-23`; `admin/actores_lista.html:9,23-26` | Sin cambio: los labels `Tutor`/`Mediador` se conservan. | — |

`[VER]` Render manual de `/mediador/becario/<id>/auditoria` con sesión mediador.

### A.6 Capa de Tests (Fase A)

| Tarea | Archivo | Detalle | `[RA]` |
|---|---|---|---|
| A.6.1 Renombrar y adaptar CU-08 | `tests/test_cu08_tutor_auditar_datos_academicos.py` | Renombrar a `test_cu08_mediador_auditar_datos_academicos.py`. Reemplazar `MockTutorRepository` por `MockMediadorRepository`; instanciar `Mediador` en vez de `Tutor`. Conservar los casos de prueba. | Tests de CU-08 pasan con `Mediador`. |
| A.6.2 Ajustar dominio | `tests/test_becario.py:236-305` (CU-08) | Mover los casos de auditoría para invocar `mediador.auditar_datos_academicos_becario(...)`. `TestTutorContactarMediador` (337-356) **sin cambio**. | `test_becario.py` en verde. |
| A.6.3 Regresión CU-06 | `tests/test_cu06_tutor_obtener_datos_becario.py` | Sin cambio de actor; verificar que sigue empaquetando `mediador_asignado`. | En verde. |
| A.6.4 Regresión CU-05 | `tests/test_tutor_listar_becarios.py` | Sin cambio. | En verde. |
| A.6.5 Regresión vínculos/contacto | `tests/test_cu03_gestionar_vinculaciones.py`, `tests/test_cu02_contactar.py` | Sin cambio (usan punteros conservados). | En verde. |

`[VER]` `python3.14 -m unittest discover`

### A.7 Criterios de aceptación de Fase A

- [ ] `Mediador` expone `auditar_datos_academicos_becario` y `visualizar_datos_academicos` con opciones; `Tutor` no.
- [ ] `MediadorRepositoryProtocol` + `SQLAlchemyMediadorRepository` creados.
- [ ] CU-08 depende del repo de Mediador.
- [ ] Endpoint de auditoría bajo `@requiere_rol("mediador")`; `tutor` obtiene 403.
- [ ] `becario_detalle.html` muestra Aprobar/Rechazar solo a `mediador`.
- [ ] Suite completa en verde: `python3.14 -m unittest discover`.
- [ ] `DatosAcademicos` y su máquina de estados **sin cambios** (diff vacío en `datos_academicos.py`).

### A.8 Rollback de Fase A

Revert del merge/commit. Sin impacto en datos ni Auth.

---

## Fase B — Datos y Acceso (ventana de mantenimiento)

> Objetivo: alinear los datos y los claims con la nueva semántica. **Atómica**: E6 (DB) y E7 (Auth) se ejecutan en la misma ventana. Requiere Fase A desplegada.

### B.1 Capa de Base de Datos (Postgres/Supabase)

| Tarea | Detalle | `[RA]` |
|---|---|---|
| B.1.1 Backup | `pg_dump` de `tutores`, `mediadores`, `becarios`. Respaldo de `auth.users.user_metadata`. | Backup verificable. |
| B.1.2 Script de migración (transaccional) | Ejecutar en una sola transacción (`BEGIN/COMMIT`): (a) swap de filas entre `tutores` y `mediadores` (tablas estructuralmente idénticas); (b) swap de `becarios.tutor_id ↔ mediador_id` por becario; (c) `UPDATE` de la columna `rol` al nuevo valor en cada tabla. | Cada becario conserva exactamente 1 tutor + 1 mediador; `rol` coherente con la tabla. |
| B.1.3 Verificación post-migración | Query de control: contar becarios con 0 o 2 tutores/mediadores → debe ser 0. | Query devuelve 0 inconsistencias. |

**Script de referencia (transaccional, esquemático):**

```sql
BEGIN;

-- 1) Swap de filas entre tutores y mediadores (tablas idénticas en estructura).
--    Se asume tabla temporal de staging para el intercambio.
CREATE TEMP TABLE _swap_t AS TABLE tutores;
TRUNCATE tutores;
INSERT INTO tutores SELECT * FROM mediadores;
TRUNCATE mediadores;
INSERT INTO mediadores SELECT * FROM _swap_t;

-- 2) Swap de FKs en becarios (cada becario conserva 1 tutor + 1 mediador).
UPDATE becarios SET
    tutor_id    = mediador_id,
    mediador_id = (SELECT tutor_id FROM becarios b2 WHERE b2.id_usuario = becarios.id_usuario)
WHERE FALSE; -- placeholder: requiere columnas temporales para swap sin colisión
-- En la práctica: usar columnas _tmp_tutor_id / _tmp_mediador_id en dos pasos.

-- 3) Ajustar columna rol (los defaults ya coinciden con el nombre de tabla,
--    pero se fuerza el valor por si hubo filas con valor explícito).
UPDATE tutores    SET rol = 'tutor';
UPDATE mediadores SET rol = 'mediador';

COMMIT;
```

> ⚠️ El swap de FKs en `becarios` requiere columnas temporales (no se puede hacer en un solo `SET` sin colisión). El script final debe materializar ese detalle. **No ejecutar en producción sin probar en staging.**

`[RIESGO]` Si el script falla a mitad, el `ROLLBACK` automático restaura todo. Validar en staging antes.

### B.2 Capa de Supabase Auth (claims)

| Tarea | Detalle | `[RA]` |
|---|---|---|
| B.2.1 Listar usuarios afectados | Obtener `auth.users` con `user_metadata.rol` en `('tutor','mediador')` y cruzar con la tabla donde reside cada usuario post-swap. | Listado completo y diferencial. |
| B.2.2 Actualizar claims | Vía Admin API (`auth.admin.update_user_by_id`), setear `user_metadata={"rol": nuevo_rol}` para cada usuario afectado. `nuevo_rol` = rol opuesto al que tenía. | 100% de usuarios con `user_metadata.rol` coherente con su tabla. |
| B.2.3 Verificación | Script que compara `auth.users.user_metadata.rol` vs la tabla donde reside el usuario (`tutores`↔`'tutor'`, `mediadores`↔`'mediador'`). | 0 mismatches. |

`[RIESGO]` Si los claims no se migran, `login.py:42` lee el rol viejo del JWT y `obtener_por_id_y_rol` (`repositories.py:124-138`) hidrata la tabla equivocada → acceso roto. Es la tarea más crítica de la migración.

### B.3 Capa de Sesiones

| Tarea | Archivo:línea | Detalle | `[RA]` |
|---|---|---|---|
| B.3.1 Invalidar sesiones activas | `src/web/app.py:35` | Rotar `SECRET_KEY` (o introducir un flag de versión de sesión que invalide cookies previas). Las sesiones Flask guardan `session["rol"]` (`app.py:57-58`); las activas pre-migración tendrían el rol viejo. | Post-deploy, todo usuario debe re-loguearse. |
| B.3.2 Forzar re-login | — | Cualquier sesión pre-existente se rechaza; el usuario re-autentica y obtiene el nuevo `rol` desde el JWT actualizado. | Login refleja el rol migrado. |

`[RIESGO]` Sesiones con `rol` viejo producen 403/404 espurios hasta expirar (30 min, `app.py:37`). Rotar `SECRET_KEY` las invalida de inmediato.

### B.4 Criterios de aceptación de Fase B

- [ ] Script de migración ejecutado en una transacción; rollback disponible.
- [ ] 0 becarios con tutor/mediador faltante o duplicado.
- [ ] `user_metadata.rol` coherente con la tabla de cada usuario (0 mismatches).
- [ ] `SECRET_KEY` rotado; sesiones previas invalidadas.
- [ ] Login de un usuario migrado hidrata la clase correcta (`Mediador` si audita, `Tutor` si gestiona tutorías).

### B.5 Rollback de Fase B

- Restaurar `pg_dump` de `tutores`/`mediadores`/`becarios`.
- Restaurar `user_metadata` de Auth desde respaldo (re-aplicar `update_user_by_id` con rol original).
- Restaurar `SECRET_KEY` previo.
- Revertir Fase A si el rollback de datos expone incompatibilidad de código.

---

## Fase C — Cierre y Documentación

> Objetivo: regresión completa, sincronización documental y diseño de RLS futuro. Requiere Fase B completada.

### C.1 Capa de Tests (regresión integral)

| Tarea | Detalle | `[RA]` |
|---|---|---|
| C.1.1 Suite completa | `python3.14 -m unittest discover` sobre entorno con datos migrados (staging). | 100% verde. |
| C.1.2 Test E2E de auditoría | Flujo completo: login mediador → seleccionar becario → aprobar/rechazar. | Transición de estados correcta. |
| C.1.3 Test de autorización | Auditar con `tutor` → 403; con `mediador` → OK. | 403 emitido por `@requiere_rol`. |
| C.1.4 Regresión `DatosAcademicos` | `tests/test_datos_academicos.py` sin cambios. | Máquina de estados intacta. |

### C.2 Capa de Documentación

| Tarea | Archivo | Detalle | `[RA]` |
|---|---|---|---|
| C.2.1 Sincronizar diagrama de clases | `AOO - DOO/Diagrama de clases.puml:141-161` | Mover `auditar_datos_academicos_becario` y la anotación de auditoría de la clase `Tutor` a `Mediador`. Ajustar `visualizar_datos_academicos`. | Diagrama coincide con §1.4/1.5 del AOO. |
| C.2.2 Sincronizar diagrama de estados | `AOO - DOO/Diag_Est_DatosA.puml:61,73,74,105` | Reemplazar "Tutor" por "Mediador" en las acciones de auditoría (CU-08). | Transiciones reflejan actor `Mediador`. |
| C.2.3 Sincronizar `Administrador.md` | `AOO - DOO/Administrador.md:23,28,143,147,292,347,348,394` | Actualizar RN-ADM-06 y RN-ADM-07: la auditoría exclusiva pasa del `Tutor` al `Mediador`. Ajustar menciones en §1, §3.4, §6, §7. | Documento coherente con RN-09. |
| C.2.4 Revisar `.puml` de casos de uso | `AOO - DOO/Casos de uso/CU8_Auditar_Da_*.puml` | Cambiar `:Tutor: as t` → `:Mediador: as m` en los diagramas de CU-08. | Actor correcto. |

> **Nota:** `AOO_FONBEC.md` ya fue actualizado en la sesión previa (RN-09, §1.4/1.5, CU-04/CU-08, CRC, nota final). No requiere reedición.

### C.3 Capa de Seguridad (RLS — diseño futuro)

| Tarea | Detalle | `[RA]` |
|---|---|---|
| C.3.1 Documentar premisa RLS | Las policies futuras deben asumir: `rol="mediador"` audita y gestiona cartas; `rol="tutor"` gestiona tutorías. Las policies se basarán en `auth.jwt() ->> 'user_metadata' ->> 'rol'`. | Documento de diseño RLS actualizado. |
| C.3.2 No implementar en esta migración | RLS no está implementada hoy; queda como hoja de ruta. | — |

### C.4 Criterios de aceptación de Fase C

- [ ] Suite completa verde sobre datos migrados.
- [ ] `Diagrama de clases.puml`, `Diag_Est_DatosA.puml`, `Administrador.md` y `.puml` de CU-08 sincronizados.
- [ ] Documento de diseño RLS futuro refleja la nueva semántica de roles.

---

## 2. Matriz resumen Fase × Capa

| Capa \ Fase | A (Código) | B (Datos+Auth) | C (Cierre) |
|---|---|---|---|
| Dominio | A.1 reasigna métodos | — | — |
| Aplicación | A.2 crea protocol, renombra CU-08 | — | — |
| Infraestructura | A.3 crea repo Mediador | — | — |
| Web/Endpoints | A.4 crea `mediador_bp` | — | — |
| Presentación | A.5 migra bloque auditoría | — | — |
| Base de Datos | — | B.1 swap filas + FKs + rol | — |
| Supabase Auth | — | B.2 migra claims | — |
| Sesiones | — | B.3 rota `SECRET_KEY` | — |
| Tests | A.6 adapta CU-08 | — | C.1 regresión integral |
| Documentación | — | — | C.2 sincroniza `.puml`/`Administrador.md` |
| Seguridad (RLS) | — | — | C.3 diseño futuro |

---

## 3. Checklist global de aceptación

- [ ] `Mediador` es el único actor que audita (RN-09); `Tutor` no expone `auditar_*`.
- [ ] `DatosAcademicos` y su máquina de estados **sin cambios** (diff vacío).
- [ ] `MediadorRepositoryProtocol` + `SQLAlchemyMediadorRepository` operativos.
- [ ] Endpoint de auditoría bajo `@requiere_rol("mediador")`.
- [ ] `becario_detalle.html` muestra Aprobar/Rechazar solo a `mediador`.
- [ ] Datos migrados: 0 becarios con referente faltante/duplicado; `rol` coherente por fila.
- [ ] Claims `user_metadata.rol` coherentes con la tabla de cada usuario (0 mismatches).
- [ ] Sesiones previas invalidadas; re-login obligatorio.
- [ ] Suite `python3.14 -m unittest discover` en verde.
- [ ] `.puml` y `Administrador.md` sincronizados con el AOO.

---

## 4. Riesgos transversales y mitigaciones

| Riesgo | Fase | Mitigación |
|---|---|---|
| Claims no migrados → login hidrata tabla equivocada | B | Script de verificación pre-deploy: comparar `user_metadata.rol` vs tabla; abortar si mismatch. |
| Sesiones con rol viejo → 403/404 espurios | B | Rotar `SECRET_KEY` y forzar re-login. |
| Swap de FKs con error a mitad → huérfanos | B | Transacción única con `BEGIN/COMMIT`; rollback automático. Probar en staging. |
| Reescribir (en vez de mover) `auditar_*` → pierde garantía de lógica intacta | A | Movimiento textual del método; diff del cuerpo debe ser nulo. |
| Endpoint de auditoría no migrado en templates → 404 | A | Test E2E de CU-08 con rol mediador. |
| `.puml`/`Administrador.md` desactualizados → inconsistencia documental | C | Etapa C.2 explícita. |
| RLS futura diseñada sobre semántica vieja → brecha | C | Documentar en C.3 que policies asumen Mediador=auditor. |
| Confusión operativa: personas cambian de función | B | Comunicar a usuarios; el admin reasigna vinculaciones si una persona no encaja en el nuevo rol. |

---

## 5. Comandos de verificación

```bash
# Tests unitarios y de integración (suite completa)
python3.14 -m unittest discover

# Tests focalizados por fase
python3.14 -m unittest discover -s tests -p "test_becario.py"        # A.1 dominio
python3.14 -m unittest discover -s tests -p "test_cu08_*"            # A.2 aplicación
python3.14 -m unittest discover -s tests -p "test_mapping.py"        # A.3 infra
python3.14 -m unittest discover -s tests -p "test_web_*"             # A.4 web

# Lint / typecheck (según configuración del proyecto — verificar requirements.txt)
# ruff check . && mypy src   (si están configurados)
```

---

## 6. Origen y trazabilidad

- **Decisión arquitectónica:** persistida en Engram (`architecture/roles-tutor-mediador`, obs-b4ed16524a9b5172).
- **Especificación funcional:** `AOO - DOO/AOO_FONBEC.md` (actualizado con RN-09, §1.4/1.5, CU-04/CU-08, CRC).
- **Inventario de impacto:** 326 referencias a `tutor`/`mediador` mapeadas en `src/`, `tests/`, `templates/`, `AOO - DOO/`.
- **Premisa corregida:** el "rename puro" no es viable por el mapeo `claim rol ↔ tabla ↔ clase` (`repositories.py:124-138` + `login.py:42`); la migración real es reasignación de métodos + migración de personas/claims. El mecanismo de auth se preserva; los valores de los claims no.
