<div align="center">
  <img src="images/VARIACION%203%20NEGRO.png" alt="FONBEC Logo" width="250">
</div>

# 2. Restricciones de la Arquitectura

Las restricciones que se documentan en esta sección son decisiones previas al diseño, condiciones del entorno o marcos de referencia organizacionales que limitan las opciones disponibles para la arquitectura del sistema. Su origen se encuentra en el código fuente, en las dependencias declaradas y en las reglas de desarrollo formalizadas en `AGENTS.md`.

---

## 2.1 Restricciones Técnicas

| ID | Restricción | Descripción | Fundamento |
| :--- | :--- | :--- | :--- |
| TC-01 | **Intérprete Python 3.14.4** | El sistema está desarrollado y ejecutado exclusivamente sobre Python 3.14.4. El código utiliza `from __future__ import annotations`, type hints modernos y características del lenguaje no disponibles en versiones anteriores. | `requirements.txt`, `openspec/config.yaml` |
| TC-02 | **PostgreSQL como único motor de base de datos** | El esquema físico (`src/infrastructure/schema.py`) utiliza el tipo `ARRAY(String)` para las columnas `materias_a_cursar` y `materias_adeudadas`. Este tipo es una extensión nativa de PostgreSQL sin equivalente en SQLite, MySQL o SQL Server. El sistema no puede migrarse a otro motor de base de datos sin reescribir el esquema y los repositorios. | `schema.py:131-132` |
| TC-03 | **Supabase como plataforma exclusiva de infraestructura cloud** | El sistema depende de tres servicios de Supabase de forma obligatoria: (1) **PostgreSQL** para persistencia relacional, (2) **Supabase Auth** para gestión de identidad y sesiones, (3) **Supabase Storage** para almacenamiento de documentos PDF. La pérdida de acceso a cualquiera de estos servicios implica la pérdida parcial o total de funcionalidad del sistema. | `database.py`, `auth_service.py`, `supabase_storage.py` |
| TC-04 | **Variables de entorno obligatorias en tiempo de arranque** | El sistema falla con `sys.exit(1)` en el arranque si `SUPABASE_DATABASE_URL` no está disponible. Las siguientes variables son requeridas para operación completa: `SUPABASE_DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_ANON_KEY`, `SECRET_KEY`, `BASE_URL`. | `database.py:16-18` |
| TC-05 | **Mapeo ORM imperativo con SQLAlchemy 2.x** | Las clases de dominio son Python puras (`@dataclass`) que no heredan de ninguna clase de SQLAlchemy. El vínculo entre clases de dominio y tablas relacionales se establece exclusivamente mediante `map_imperatively()` en `src/infrastructure/mapping.py`. Esta decisión garantiza el desacoplamiento entre el Dominio y la infraestructura de persistencia. | `mapping.py:32-119` |
| TC-06 | **Carga ansiosa (`lazy="joined"`) en las colecciones del Aggregate Root** | Todas las relaciones relevantes del `Becario` (colecciones y punteros) están configuradas con `lazy="joined"` o `lazy="selectin"`. Esta restricción es no negociable para evitar `DetachedInstanceError` al acceder a los objetos relacionados fuera del contexto de la sesión SQLAlchemy. Aplica a: `lista_tutorias`, `lista_envios_cartas`, `puntero_tutor`, `puntero_mediador`, `puntero_padrino`. | `mapping.py:90-118` |
| TC-07 | **Renderizado exclusivo en el servidor (SSR); sin endpoints JSON** | En el alcance del MVP, el sistema no expone ningún endpoint que retorne JSON para consumo de clientes SPA o aplicaciones móviles. Todas las respuestas HTTP son documentos HTML completos generados por Jinja2 (`render_template`) o redirecciones HTTP (`url_for()`). | `AGENTS.md §5, regla 4`; `src/web/routes/` |
| TC-08 | **Solo documentos PDF en el almacenamiento de archivos** | El bucket `documentos_academicos` en Supabase Storage impone `content-type: application/pdf` en todas las operaciones de carga. El sistema no soporta otros formatos de archivo para documentación académica. La ruta de almacenamiento sigue la convención determinista: `becarios/{becario_id}/{tipo_documento}_{nombre_completo}.pdf`. | `supabase_storage.py:88,94-97` |
| TC-09 | **Sesiones con expiración de 30 minutos y cookies protegidas** | Las sesiones de usuario tienen un lifetime máximo de 30 minutos. Las cookies de sesión están configuradas con los atributos `HttpOnly=True` y `SameSite=Lax`. Esta configuración es una restricción de seguridad para proteger el manejo de datos sensibles de menores de edad. | `app.py:37-39` |
| TC-10 | **Gunicorn como servidor WSGI de producción** | El modo `debug=True` de Flask (puerto 5000) está reservado exclusivamente para el entorno de desarrollo local. El despliegue en producción requiere Gunicorn como servidor WSGI. | `requirements.txt:gunicorn==26.0.0`, `run.py:13` |

---

## 2.2 Restricciones Organizacionales

| ID | Restricción | Descripción | Fuente |
| :--- | :--- | :--- | :--- |
| OC-01 | **Clean Architecture con separación estricta de capas** | La estructura del proyecto se organiza en cuatro capas con responsabilidades no negociables: `domain/` (reglas de negocio puras), `application/` (casos de uso y protocolos), `infrastructure/` (implementaciones técnicas concretas) y `web/` (capa HTTP/presentación). Ningún artefacto de Flask, SQLAlchemy o Supabase puede aparecer en la capa de Dominio. | `AGENTS.md §2, §3` |
| OC-02 | **`Becario` como único Aggregate Root del modelo** | Toda navegación o persistencia hacia las entidades operativas del sistema (`DatosAcademicos`, `Tutoria`, `EnvioCarta`) pasa exclusivamente a través de la instancia `Becario`. No existen referencias directas entre `Tutor` y `Mediador` (RN-03): toda interacción entre referentes se materializa a través del Becario que los vincula. | `AGENTS.md §5, regla 1`; `becario.py` |
| OC-03 | **Máquinas de estado reactivas en el Dominio** | La capa de Aplicación no asigna estados directamente sobre las entidades de dominio. El modelo de Dominio evalúa y transiciona su propio estado de forma autónoma al recibir mutaciones de datos o de sus colecciones (método `revaluar_estado()` en `DatosAcademicos`). | `AGENTS.md §5, regla 2`; `datos_academicos.py:87-98` |
| OC-04 | **Protección de datos aprobados (RN-02)** | Un becario cuyo `estado_verificacion` sea `APROBADO` no puede modificar sus `DatosAcademicos` ni agregar o eliminar documentos. Esta restricción está implementada en la capa de Dominio como guardia en cuatro métodos independientes, lo que la hace estructuralmente imposible de omitir desde capas superiores. | `AGENTS.md §5, regla 3`; `datos_academicos.py` |
| OC-05 | **Patrón Saga en operaciones transversales de infraestructura** | Toda operación de caso de uso que involucre simultáneamente una escritura en Supabase Storage y en la base de datos debe implementar un mecanismo de compensación: si la persistencia en BD falla después de que el archivo fue subido a Storage, el caso de uso debe intentar eliminar el archivo subido para prevenir recursos huérfanos. | `AGENTS.md §5, regla 6` |
| OC-06 | **Testing de dominio obligatorio y aislado** | Las reglas de negocio complejas implementadas en `domain/` deben contar con cobertura de tests unitarios que se ejecuten sin base de datos real ni servicios externos, mediante inyección de mocks a través de los protocolos definidos en `application/protocols.py`. | `AGENTS.md §6` |
| OC-07 | **Los diagramas `.puml` son la especificación funcional de referencia** | Para cualquier decisión de diseño de clases, máquinas de estado o flujos del sistema, los diagramas UML en `docs/` (`.puml`) constituyen la especificación funcional de referencia. Toda implementación debe ceñirse bidireccionalmente a esos diagramas. | `AGENTS.md §4` |

---

## 2.3 Convenciones

| ID | Convención | Descripción |
| :--- | :--- | :--- |
| CON-01 | **Nomenclatura de casos de uso** | Los archivos de casos de uso siguen el patrón `CU{número}_{Actor}_{Acción}.py` (ejemplo: `CU08_Mediador_AuditarDatosAcademicos.py`). Los casos de uso administrativos se prefijan con `CU-ADM`. |
| CON-02 | **Protocolos como contratos de dependencia** | Todos los contratos de acceso a infraestructura se definen como `Protocol` en `src/application/protocols.py`. Los casos de uso dependen exclusivamente de estos protocolos, nunca de implementaciones concretas (Principio de Inversión de Dependencias). |
| CON-03 | **Nomenclatura de repositorios** | Los repositorios concretos siguen el patrón `SQLAlchemy{Entidad}Repository` e implementan el protocolo `{Entidad}RepositoryProtocol` correspondiente. |
| CON-04 | **Idioma en artefactos** | Los identificadores de entidades de dominio, métodos de negocio y variables de dominio se nombran en español (`puntero_tutor`, `lista_becarios`, `guardar`, `obtener_por_id`). Los artefactos de infraestructura, configuración y decoradores de Flask siguen convenciones en inglés. |
| CON-05 | **Inyección de dependencias explícita** | Las dependencias de infraestructura (repositorios, servicios de auth, storage) se inyectan explícitamente en los constructores de los casos de uso. No se utiliza ningún contenedor de inyección de dependencias automatizado. |

---

*Sección anterior: [01 — Introducción y Metas](./01-introduccion-y-metas.md)*  
*Sección siguiente: [03 — Alcance y Contexto del Sistema](./03-alcance-y-contexto.md)*
