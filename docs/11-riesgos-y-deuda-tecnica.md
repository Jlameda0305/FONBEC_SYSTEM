# 11. Riesgos y Deuda Técnica

Esta sección documenta los riesgos de seguridad y la deuda técnica estructural identificados en el sistema FONBEC, derivados de auditorías estáticas forenses y análisis de arquitectura (Domain-Driven Design).

### 11.1 Riesgos

| ID | Riesgo | Impacto | Probabilidad | Mitigación |
| --- | --- | --- | --- | --- |
| R-1 | **Compromiso de Autenticación y Sesiones:** Vulnerabilidades severas por uso de `SECRET_KEY` hardcodeado como fallback, uso de cookies sin re-validación de roles contra la DB, y falta de verificación de tokens JWT contra Supabase por request. | Alto | Alta | Forzar uso de variables de entorno, implementar validación de JWT server-side y consultar roles directamente desde el repositorio en cada request validado. |
| R-2 | **Falta de Protección CSRF:** Ausencia total de tokens CSRF en endpoints mutacionales (POST/DELETE), permitiendo ataques dirigidos de escalada de privilegios y alteración de datos (ej. eliminar becarios). | Alto | Alta | Implementar librería `Flask-WTF` con protección `CSRFProtect` global y tokens explícitos en todos los formularios Jinja2. |
| R-3 | **IDOR y Riesgos en Carga de Archivos:** Endpoints vulnerables a referencias directas (IDOR) y falta de validación MIME/tamaño en el proceso de upload hacia Supabase Storage. | Medio | Media | Re-evaluar autorizaciones en Casos de Uso y validar estrictamente cabeceras y extensiones antes del procesamiento. |
| R-4 | **Incertidumbre en Políticas Supabase RLS:** Falta de verificación estricta de políticas Row Level Security (RLS) directamente a nivel de Supabase, lo que delega toda la responsabilidad a la aplicación web. | Alto | Baja | Auditar el esquema en Supabase para asegurar que se implementen políticas RLS que coincidan con la lógica de negocio. |

### 11.2 Deuda Técnica

| ID | Elemento de Deuda | Impacto | Prioridad |
| --- | --- | --- | --- |
| TD-1 | **Violación de Capa Anticorrupción (ACL):** Filtración sistemática de entidades del Dominio (ej. `Usuario`) hacia la Capa Web. Uso directo de campos en lugar de Data Transfer Objects (DTOs) aislando el núcleo. | Alto | Alta |
| TD-2 | **Ausencia de Unit of Work y Transaccionalidad:** Uso del anti-patrón de auto-commit general en el hook `teardown_appcontext`, destruyendo la atomicidad de los Casos de Uso y la integridad de las Sagas. | Alto | Alta |
| TD-3 | **Patrón Service Locator Inapropiado:** Extensa dependencia en la variable global `g.usuario_actual` para resolver la autenticación en los controladores, en lugar de utilizar inyección de dependencias pura hacia Aplicación. | Medio | Media |
| TD-4 | **Incertidumbre en Implementación de Repositorios:** Abstracciones SQL en capa de infraestructura (`obtener_por_id_y_rol`) que no han sido debidamente auditadas, asumiendo validaciones que pueden estar incompletas. | Medio | Media |
