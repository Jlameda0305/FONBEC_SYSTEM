# Documentación Arquitectónica FONBEC — arc42

**Versión:** 1.0  
**Fecha:** 2026-07-07  
**Estado:** En revisión  
**Fuente de verdad:** Código fuente del proyecto (`src/`)  
**Plantilla base:** arc42 v7.0 ES

---

# 1. Introducción y Metas

## 1.1 Vista de Requerimientos

**Sistema:** Plataforma Web de Gestión de Becas — FONBEC

FONBEC es una plataforma web empresarial desarrollada a medida para gestionar el programa de becas de la Fundación FONBEC. El sistema reemplaza un conjunto de automatizaciones basadas en herramientas de terceros (n8n) que presentaban limitaciones severas en materia de control de acceso granular, escalabilidad ante el crecimiento de reglas de negocio, y experiencia de usuario unificada para los distintos actores del programa.

El sistema gestiona el ciclo de vida académico de los becarios y las relaciones entre los actores involucrados: Becarios, Tutores, Mediadores, Padrinos y el Administrador. El **Becario** es el *Aggregate Root* del modelo de dominio: toda navegación y persistencia estructural hacia las entidades operativas del sistema (`DatosAcademicos`, `Tutoria`, `EnvioCarta`) se realiza exclusivamente a través de él. No existe relación directa entre `Tutor` y `Mediador`; toda interacción entre referentes se materializa a través del `Becario` (RN-03).

### Funcionalidades principales

| ID | Funcionalidad | Actor(es) principal(es) |
| :--- | :--- | :--- |
| CU-ADM-01 | Invitación de usuarios con rol predefinido (el autoregistro está prohibido) | Administrador |
| CU-ADM-02 | Eliminación de usuarios con preservación de datos históricos | Administrador |
| CU-ADM-03 | Gestión de vinculaciones: asignación y desasignación de Tutor, Mediador y Padrino al Becario | Administrador |
| CU-ADM-04 | ABM de Padrinos (entidad sin acceso al sistema) | Administrador |
| CU-ADM-05 | Listado global de todos los actores del sistema | Administrador |
| CU-ADM-06 | Visualización de datos académicos en estado `Aprobado` | Administrador |
| CU-03 | Carga y actualización del formulario de datos académicos con máquina de estados reactiva | Becario |
| CU-04 | Visualización de datos académicos con comportamiento diferenciado por rol y estado | Becario, Tutor, Mediador |
| CU-08 | Auditoría de datos académicos: aprobación y rechazo con observaciones | Mediador |
| CU-05 | Listado de becarios asignados | Tutor, Mediador |
| CU-06 | Selección de becario y carga de su contexto completo | Tutor, Mediador |
| CU-02 | Contacto directo entre actores mediante enlaces (WhatsApp / teléfono) | Becario, Tutor, Mediador |
| CU-10/11/12 | Gestión del calendario de tutorías: crear, actualizar y cancelar (soft delete) | Tutor |
| CU-14/15 | Gestión del calendario de envíos de cartas | Mediador |

> **Nota de alcance futuro:** La integración del estado `Enviada` en `EnvioCarta` mediante un actor externo, el sistema de notificaciones ante cambios de estado y la transmisión de datos al sistema externo FONBEC tras la aprobación académica se encuentran fuera del alcance del MVP actual y están documentados en `docs/AOO_FONBEC.md §5`.

---

## 1.2 Metas de Calidad

Las siguientes metas de calidad se derivan de la arquitectura implementada y de las reglas de negocio formalizadas en el código fuente. Se presentan en orden de prioridad decreciente.

| Prioridad | Meta de Calidad | Escenario representativo |
| :---: | :--- | :--- |
| 1 | **Integridad de datos y consistencia del modelo de dominio** | Los datos académicos de un Becario cuyo `estado_verificacion` es `APROBADO` no pueden ser modificados, reemplazados ni eliminados bajo ninguna circunstancia. El sistema rechaza cualquier intento de mutación en cuatro puntos de control independientes dentro de la capa de Dominio (RN-02). La máquina de estados de `DatosAcademicos` valida cada transición contra un grafo explícito (`TRANSICIONES_VALIDAS`) antes de permitirla. |
| 2 | **Mantenibilidad y extensibilidad** | Es posible reemplazar el motor de base de datos o incorporar un nuevo tipo de actor sin modificar ninguna clase de la capa de Dominio. La separación estricta en cuatro capas (Dominio, Aplicación, Infraestructura, Web) y el mapeo ORM imperativo —completamente desacoplado de las clases de dominio— garantizan que el núcleo de reglas de negocio permanezca independiente de la tecnología subyacente. |
| 3 | **Seguridad de acceso y control de identidad** | Ningún usuario puede obtener acceso al sistema de forma autónoma. El modelo de invitaciones controladas (Administrador → Supabase Auth → candidato) es la única vía de ingreso. Las sesiones se gestionan en el servidor con cookies `HttpOnly` y `SameSite=Lax`. Las contraseñas nunca se almacenan en la base de datos local; su gestión es responsabilidad exclusiva de Supabase Auth. |
| 4 | **Testabilidad y verificabilidad del dominio** | Los casos de uso son verificables de forma aislada, sin dependencia de base de datos real ni de servicios externos. El sistema de protocolos (interfaces abstractas en `src/application/protocols.py`) permite la inyección de mocks en la suite de tests unitarios, desacoplando la lógica de negocio de su implementación de infraestructura. |
| 5 | **Consistencia transaccional ante fallos de infraestructura** | Las operaciones que involucran simultáneamente almacenamiento en la nube (Supabase Storage) y persistencia en base de datos aplican un patrón Saga rudimentario: si la persistencia en base de datos falla después de que un archivo fue subido a Storage, el sistema intenta eliminar el archivo subido para prevenir la acumulación de recursos huérfanos en la nube. |

---

## 1.3 Partes Interesadas (Stakeholders)

| Rol | Acceso al sistema | Expectativas |
| :--- | :--- | :--- |
| **Administrador** | Sí (invitado, rol `administrador`) | Gestionar el ciclo de vida completo de usuarios mediante invitaciones controladas; administrar todas las vinculaciones entre actores del dominio; supervisar el estado académico global de todos los becarios; mantener el registro de Padrinos. |
| **Becario** | Sí (invitado por el Administrador, rol `becario`) | Cargar y actualizar el formulario de datos académicos; adjuntar la documentación requerida (Programa, Carta de Compromiso, Inscripción); consultar el estado de verificación de sus datos; visualizar el calendario de tutorías asignadas; contactar directamente a su Tutor y Mediador. |
| **Tutor** | Sí (invitado por el Administrador, rol `tutor`) | Visualizar la lista de becarios asignados; gestionar el calendario de tutorías del becario seleccionado (crear, actualizar, cancelar); visualizar los datos académicos del becario sin capacidad de auditoría; contactar al Mediador del becario. |
| **Mediador** | Sí (invitado por el Administrador, rol `mediador`) | Auditar los datos académicos de los becarios asignados (aprobar o rechazar con observaciones); gestionar el calendario de envíos de cartas; contactar al Tutor del becario seleccionado. |
| **Padrino** | No (sin acceso al sistema) | Figura como destinatario en el programa de envío de cartas. Su registro, modificación y eliminación son responsabilidad exclusiva del Administrador mediante el ABM de Padrinos. |
| **Fundación FONBEC** | No (operadora del sistema) | Plataforma web propia e independiente para la gestión integral del programa de becas; trazabilidad completa del ciclo académico de cada becario; seguridad en el manejo de datos sensibles de menores; escalabilidad ante el crecimiento del programa. |

---

*Sección siguiente: [02 — Restricciones de la Arquitectura](./02-restricciones-arquitectura.md)*
