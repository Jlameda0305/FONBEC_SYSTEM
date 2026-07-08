# 4. Estrategia de Solución

Esta sección documenta las decisiones tecnológicas y arquitectónicas fundamentales que determinan la estructura del sistema FONBEC. Cada decisión responde a una o más metas de calidad identificadas en la Sección 1 (§1.2).

---

## 4.1 Decisiones Tecnológicas

### D-01 — Python + Flask como stack principal

**Decisión:** El sistema está implementado en Python 3.14.4 con Flask como framework web.

**Motivación:**
- Python es el lenguaje dominante en el equipo de desarrollo y permite implementar Clean Architecture sin fricción tecnológica.
- Flask es un microframework que no impone estructura de proyecto, permitiendo que la arquitectura de capas surja del diseño propio y no de convenciones del framework.
- El SSR con Jinja2 elimina la complejidad de un frontend separado (SPA), reduciendo la superficie de desarrollo y el riesgo en el MVP.

**Consecuencias:**
- Toda la lógica de presentación se genera en el servidor. No existen endpoints JSON en el MVP (TC-07).
- Flask no provee inyección de dependencias; esta responsabilidad es explícita en cada controlador de la capa web.

**Meta de calidad asociada:** Mantenibilidad (§1.2, prioridad 2).

---

### D-02 — Supabase como plataforma de infraestructura cloud

**Decisión:** Se utilizan tres servicios de Supabase: PostgreSQL (base de datos), Auth (identidad) y Storage (archivos).

**Motivación:**
- Supabase ofrece los tres servicios de infraestructura necesarios bajo una única plataforma gestionada, eliminando la necesidad de operar servidores de base de datos, SMTP o almacenamiento de objetos.
- La Admin API de Supabase Auth permite el modelo de invitaciones controladas (RN-ADM-01): ningún usuario puede registrarse de forma autónoma.
- Supabase Storage provee almacenamiento de objetos con URLs públicas deterministas, necesario para los documentos académicos PDF.

**Consecuencias:**
- El sistema tiene una dependencia de disponibilidad rígida con Supabase (TC-03). Un fallo de la plataforma implica pérdida de funcionalidad total.
- Las variables de entorno `SUPABASE_DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` y `SUPABASE_ANON_KEY` son obligatorias en tiempo de arranque (TC-04).

**Meta de calidad asociada:** Seguridad de acceso (§1.2, prioridad 3).

---

### D-03 — SQLAlchemy 2.x con mapeo ORM imperativo

**Decisión:** El ORM es SQLAlchemy en modo imperativo (`map_imperatively()`). Las clases de dominio son Python puras (`@dataclass`) sin herencia de ninguna clase de SQLAlchemy.

**Motivación:**
- El mapeo declarativo estándar de SQLAlchemy (con `Base`) contamina las clases de dominio con artefactos de infraestructura, violando el principio de Clean Architecture.
- El mapeo imperativo permite definir el esquema en `schema.py` y el binding en `mapping.py`, manteniendo las entidades de dominio completamente libres de dependencias de ORM.
- Es posible reemplazar SQLAlchemy por cualquier otro mecanismo de persistencia modificando únicamente la capa de infraestructura; las clases de dominio no requieren ningún cambio.

**Consecuencias:**
- El mapeo se inicializa una única vez al arranque de la aplicación (`iniciar_mapeo()` en `mapping.py`), protegido por un flag `_mapped` para evitar doble inicialización.
- La carga ansiosa (`lazy="joined"`) es obligatoria para las colecciones del Aggregate Root para evitar `DetachedInstanceError` (TC-06).
- El esquema usa `Concrete Table Inheritance`: cada actor del dominio (`Becario`, `Tutor`, `Mediador`, `Administrador`) tiene su propia tabla física sin tabla padre compartida. Esto simplifica las consultas pero requiere que el rol sea conocido al momento de consultar.

**Meta de calidad asociada:** Mantenibilidad (§1.2, prioridad 2).

---

### D-04 — Bootstrap / Argon Dashboard vía CDN para el frontend

**Decisión:** La interfaz web usa el tema Argon Dashboard de Bootstrap, cargado a través de activos estáticos o CDN. No se utiliza ningún gestor de paquetes frontend (npm, yarn).

**Motivación:**
- La prioridad del MVP es la funcionalidad backend y la solidez del dominio. Un framework visual preestablecido aceleró el desarrollo de la interfaz sin comprometer la arquitectura.
- Al no integrar un bundler de frontend, se elimina toda la complejidad de herramientas como Webpack o Vite del stack del MVP.

**Consecuencias:**
- Los activos de frontend no están versionados mediante un gestor de dependencias. Actualizaciones de Bootstrap requieren reemplazo manual de archivos.

---

## 4.2 Decisiones Arquitectónicas

### A-01 — Clean Architecture con 4 capas explícitas

**Decisión:** El proyecto se organiza en cuatro capas estrictas con dependencias unidireccionales: `domain/` ← `application/` ← `infrastructure/` ← `web/`.

```
src/
├── domain/          # Reglas de negocio puras (sin dependencias externas)
├── application/     # Casos de uso + protocolos (interfaces)
├── infrastructure/  # Repositorios SQL, Auth Service, Storage Service
└── web/             # Blueprints Flask, parseo de requests, inyección de dependencias
```

**Motivación:**
- El núcleo de reglas de negocio (dominio) debe ser verificable sin levantar ningún servicio externo. Esta es la premisa fundamental del testing unitario del sistema.
- Las decisiones tecnológicas (qué base de datos, qué proveedor de auth) deben ser reemplazables sin afectar las reglas de negocio.

**Consecuencias:**
- Las clases de dominio son Python puras, sin rastro de Flask, SQLAlchemy ni Supabase.
- La inyección de dependencias es explícita: cada controlador web instancia los repositorios y servicios concretos e inyecta una sesión de base de datos (obtenida de `g.db_session`) antes de construir el caso de uso.
- Los tests unitarios instancian los casos de uso con mocks que implementan los protocolos definidos en `protocols.py`.

**Meta de calidad asociada:** Testabilidad (§1.2, prioridad 4); Mantenibilidad (§1.2, prioridad 2).

---

### A-02 — `Becario` como único Aggregate Root del modelo de dominio

**Decisión:** La clase `Becario` es el único Aggregate Root del modelo. Toda navegación y persistencia hacia `DatosAcademicos`, `Tutoria` y `EnvioCarta` pasa exclusivamente a través de una instancia de `Becario`.

**Motivación:**
- El `Becario` es la entidad central del dominio: todas las operaciones académicas, de vinculación y de contacto requieren su contexto.
- La navegación a través del Aggregate Root garantiza que las reglas de negocio (como RN-02 — inmutabilidad en estado `APROBADO`) sean evaluadas en todo acceso, sin excepciones posibles desde capas superiores.
- No existe relación directa entre `Tutor` y `Mediador` (RN-03): toda interacción entre referentes se realiza navegando `becario.puntero_tutor` o `becario.puntero_mediador`.

**Consecuencias:**
- El `SQLAlchemyBecarioRepository.guardar()` persiste el agregado completo: al hacer `session.add(becario)`, el ORM sincroniza en cascada `DatosAcademicos`, `Tutoria` y `EnvioCarta`.
- El repositorio del `Mediador` también persiste el `Becario` asociado vía el grafo de objetos en memoria, aprovechando el Unit of Work implícito de SQLAlchemy.

**Meta de calidad asociada:** Integridad de datos (§1.2, prioridad 1).

---

### A-03 — Principio de Inversión de Dependencias mediante Protocolos (`typing.Protocol`)

**Decisión:** Las interfaces de acceso a infraestructura se definen como `Protocol` de Python en `src/application/protocols.py`. Los casos de uso dependen exclusivamente de estos protocolos.

**Motivación:**
- Python `Protocol` implementa structural subtyping (duck typing estático). No requiere que las implementaciones hereden de una clase base, lo que reduce el acoplamiento.
- Los mocks de test implementan el mismo `Protocol` sin herencia, lo que facilita la creación de stubs simples para cada suite de pruebas.

**Consecuencias:**
- Existen 6 protocolos activos: `BecarioRepositoryProtocol`, `TutorRepositoryProtocol`, `MediadorRepositoryProtocol`, `UsuarioRepositoryProtocol`, `PadrinoRepositoryProtocol`, `AuthServiceProtocol` e `IStorageServiceProtocol`.
- La capa web es responsable de instanciar las implementaciones concretas e inyectarlas en los casos de uso en cada request.

**Meta de calidad asociada:** Testabilidad (§1.2, prioridad 4).

---

### A-04 — Máquina de estados reactiva en `DatosAcademicos`

**Decisión:** El estado de verificación académica (`EstadoVerificacion`) se gestiona mediante una máquina de estados reactiva implementada directamente en la clase de dominio `DatosAcademicos`. Las transiciones se validan contra un grafo explícito (`TRANSICIONES_VALIDAS`) y el estado se re-evalúa automáticamente al mutar datos o documentos.

**Motivación:**
- Centralizar la lógica de estado en el dominio garantiza que ninguna capa superior pueda forzar una transición inválida.
- La re-evaluación automática (`revaluar_estado()`) asegura que el estado es siempre coherente con la completitud de los datos, sin necesidad de que la capa de aplicación tome decisiones sobre el estado resultante.

**Consecuencias:**
- RN-02 (inmutabilidad en estado `APROBADO`) está implementado como guardia en cuatro métodos independientes: `actualizar_datos()`, `agregar_documento()`, `eliminar_documento()` y en el `Becario` con `llenar_actualizar_formulario_academico()` y `visualizar_formulario_academico()`.
- El estado `APROBADO` es un estado terminal: su entrada en `TRANSICIONES_VALIDAS` es un conjunto vacío (`set()`).

**Meta de calidad asociada:** Integridad de datos (§1.2, prioridad 1).

---

### A-05 — Patrón Saga rudimentario para consistencia transaccional

**Decisión:** Las operaciones que involucran simultáneamente Supabase Storage y la base de datos aplican un mecanismo de compensación: si la persistencia en BD falla después de que un archivo fue subido a Storage, el caso de uso intenta eliminar el archivo subido para evitar recursos huérfanos.

**Motivación:**
- No existe un mecanismo de transacción distribuida entre un sistema de almacenamiento de objetos (Storage) y una base de datos relacional. La única garantía disponible es una compensación manual a nivel de aplicación.

**Consecuencias:**
- El patrón se aplica al menos en `CU03_EliminarDocumentoAcademico`: primero se elimina el archivo en Storage, luego se actualiza el dominio y se persiste en BD. Si el paso en BD falla, el fallo en Storage ya ocurrió y no puede revertirse automáticamente (compensación best-effort).
- Los errores de Storage que indican que el archivo no existe (`not found`) se tratan como no-críticos, permitiendo que el flujo continúe para limpiar registros huérfanos en BD.

**Meta de calidad asociada:** Consistencia transaccional (§1.2, prioridad 5).

---

### A-06 — Gestión del ciclo de vida de la sesión de BD por request

**Decisión:** Una sesión SQLAlchemy se crea al inicio de cada request HTTP (`before_request`) y se cierra al final (`teardown_appcontext`). El commit se realiza automáticamente si no hay excepción; el rollback se aplica en caso contrario.

**Motivación:**
- Este patrón (Session-per-request) garantiza que cada request HTTP opera en un contexto transaccional aislado. No hay sesiones compartidas entre requests concurrentes.
- La sesión se expone en `flask.g.db_session` y es inyectada explícitamente por los controladores en los repositorios.

**Consecuencias:**
- Los repositorios usan `session.flush()` en lugar de `session.commit()` para pre-validar cambios sin cerrar la transacción. El commit final es responsabilidad del middleware de la capa web.
- El usuario autenticado se carga también en `before_request` y se expone en `g.usuario_actual`, evitando consultas redundantes dentro del mismo request.

**Meta de calidad asociada:** Integridad de datos (§1.2, prioridad 1); Mantenibilidad (§1.2, prioridad 2).

---

## 4.3 Resumen de Correspondencia entre Decisiones y Metas de Calidad

| Meta de Calidad (§1.2) | Decisiones que la satisfacen |
| :--- | :--- |
| **Integridad de datos** (prioridad 1) | A-02, A-04, A-06 |
| **Mantenibilidad** (prioridad 2) | D-01, D-03, A-01, A-06 |
| **Seguridad de acceso** (prioridad 3) | D-02 |
| **Testabilidad** (prioridad 4) | A-01, A-03 |
| **Consistencia transaccional** (prioridad 5) | A-05 |

---

*Sección anterior: [03 — Alcance y Contexto del Sistema](./03-alcance-y-contexto.md)*  
*Sección siguiente: [05 — Vista de Bloques](./05-vista-de-bloques.md)*
