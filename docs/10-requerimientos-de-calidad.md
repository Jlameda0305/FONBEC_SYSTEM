# 10. Requerimientos de Calidad

Esta sección profundiza en las metas de calidad identificadas en la Sección 1.2, definiendo escenarios concretos (Quality Scenarios) que especifican cómo debe reaccionar el sistema FONBEC ante situaciones determinadas para asegurar que la arquitectura cumpla con su propósito.

---

## 10.1 Árbol de Calidad

El árbol de calidad estructura y prioriza los atributos de calidad del sistema:

1. **Integridad de Datos** (Prioridad 1)
   - Prevención de mutaciones ilegales (Reglas de negocio).
   - Aislamiento del Dominio.
2. **Seguridad y Acceso** (Prioridad 2)
   - Privacidad de información de menores.
   - Restricción estricta por roles (RBAC).
3. **Mantenibilidad y Testabilidad** (Prioridad 3)
   - Cobertura de pruebas sin dependencias externas.
   - Sustituibilidad de capas de infraestructura.
4. **Consistencia Transaccional** (Prioridad 4)
   - Resiliencia ante fallos parciales (Storage vs BD).

---

## 10.2 Escenarios de Calidad

Los escenarios de calidad se describen con el formato estándar: *Fuente del estímulo → Estímulo → Artefacto → Entorno → Respuesta → Medida de respuesta*.

### Escenarios de Integridad de Datos

| ID | Escenario de Calidad |
| :--- | :--- |
| **Q1.1** | **Estímulo:** Un Becario intenta eliminar un documento académico mediante un request POST (manipulando la interfaz web).<br/>**Entorno:** Operación normal.<br/>**Respuesta:** El controlador invoca el caso de uso, el cual recupera el agregado `Becario`. El dominio rechaza la operación en `DatosAcademicos.eliminar_documento()` porque el `estado_verificacion` es `APROBADO`.<br/>**Medida:** El sistema lanza `ValueError` antes de ejecutar cualquier borrado en BD o Storage. Los datos permanecen inmutables (cumplimiento de RN-02). |
| **Q1.2** | **Estímulo:** El Mediador intenta auditar (aprobar) datos académicos que se encuentran en estado `INCOMPLETO`.<br/>**Entorno:** Operación normal.<br/>**Respuesta:** El método `auditar_datos_academicos_becario()` del Mediador en el Dominio valida el estado actual de los datos del Becario y rechaza la orden.<br/>**Medida:** La transición es denegada, lanzando `ValueError`, impidiendo inconsistencias lógicas. |

### Escenarios de Seguridad y Acceso

| ID | Escenario de Calidad |
| :--- | :--- |
| **Q2.1** | **Estímulo:** Un usuario no autenticado intenta acceder directamente a una ruta protegida (ej. `/becario/academico`).<br/>**Entorno:** Operación normal.<br/>**Respuesta:** El decorador de autorización en la capa web intercepta el request antes de iniciar el Unit of Work, verifica la ausencia de token válido en la sesión.<br/>**Medida:** El request es denegado (HTTP 302 Redirection) hacia la pantalla de login con un mensaje flash de advertencia. |
| **Q2.2** | **Estímulo:** Un Tutor intenta visualizar los datos académicos de un becario que no forma parte de su lista de becarios asignados (modificando parámetros en la URL).<br/>**Entorno:** Operación normal.<br/>**Respuesta:** El caso de uso llama a `tutor.seleccionar_becario(id_falso)`. El Dominio itera su `lista_becarios` cargada por el repositorio, no encuentra coincidencia y rechaza la acción.<br/>**Medida:** El sistema lanza `ValueError("No posee permisos")` impidiendo la fuga de información entre referentes (cumplimiento de RN-03/Aislamiento). |

### Escenarios de Mantenibilidad y Testabilidad

| ID | Escenario de Calidad |
| :--- | :--- |
| **Q3.1** | **Estímulo:** El equipo de desarrollo necesita agregar una nueva regla de negocio para la transición de estados en `DatosAcademicos`.<br/>**Entorno:** Tiempo de desarrollo.<br/>**Respuesta:** El desarrollador escribe la regla y un test unitario instanciando las clases de Dominio directamente en memoria, sin levantar Flask, PostgreSQL ni usar librerías de Mock.<br/>**Medida:** El test unitario se ejecuta en menos de 5 milisegundos. |
| **Q3.2** | **Estímulo:** Se decide reemplazar la librería `supabase-py` por llamadas REST directas mediante `requests` o HTTPX debido a una actualización mayor (breaking change) en el SDK.<br/>**Entorno:** Tiempo de desarrollo/mantenimiento.<br/>**Respuesta:** Se crea una nueva clase que implemente `AuthServiceProtocol` y `IStorageServiceProtocol`. Se modifica el punto de inyección en la capa Web.<br/>**Medida:** Cero (0) líneas de código modificadas en las capas de Aplicación y Dominio. Cero tests unitarios rotos. |

### Escenarios de Consistencia Transaccional

| ID | Escenario de Calidad |
| :--- | :--- |
| **Q4.1** | **Estímulo:** Durante la subida de un formulario académico con dos PDFs, el primer PDF se sube a Supabase Storage con éxito, pero la escritura en PostgreSQL falla (ej. caída de red o constraint violation).<br/>**Entorno:** Operación bajo fallo de infraestructura.<br/>**Respuesta:** El caso de uso captura la excepción de base de datos. Se activa la compensación del Patrón Saga, el caso de uso solicita a `SupabaseStorageServiceImpl` la eliminación del archivo previamente subido a través de su URL.<br/>**Medida:** Se previene la generación de archivos huérfanos en Storage, manteniendo el sistema consistente (el Becario puede reintentar la operación completa sin conflictos). |
| **Q4.2** | **Estímulo:** Se detecta que un usuario ha sido eliminado directamente desde el panel de control de la base de datos (PostgreSQL), pero su sesión en Supabase Auth sigue activa.<br/>**Entorno:** Operación anómala.<br/>**Respuesta:** Al intentar iniciar sesión en FONBEC, el `LoginUseCase` autentica contra Auth exitosamente pero falla al recuperar el perfil en el repositorio local. Automáticamente revoca la sesión activa en Auth.<br/>**Medida:** Se invalida el token JWT en el proveedor de identidad, forzando la sincronización de la eliminación local (previniendo logins fantasma). |

---

*Sección anterior: [09 — Decisiones de Diseño (ADRs)](./09-decisiones-de-diseno.md)*  
*Sección siguiente: [11 — Riesgos y Deuda Técnica](./11-riesgos-y-deuda-tecnica.md)*
