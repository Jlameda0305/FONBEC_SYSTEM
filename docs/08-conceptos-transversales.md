<div align="center">
  <img src="images/VARIACION%203%20NEGRO.png" alt="FONBEC Logo" width="250">
</div>

# 8. Conceptos Transversales

Esta sección documenta los enfoques generales, patrones de diseño y reglas transversales que aplican a múltiples partes del sistema FONBEC. Estos conceptos aseguran la coherencia conceptual y técnica en todo el código base.

---

## 8.1 Arquitectura y Patrones de Diseño

### Clean Architecture y Regla de Dependencia
El sistema sigue estrictamente los principios de Clean Architecture. La **Regla de Dependencia** establece que el código fuente de una capa solo puede depender del código de las capas más internas.
- El Dominio (`src/domain/`) no tiene dependencias.
- La Aplicación (`src/application/`) depende del Dominio.
- La Infraestructura (`src/infrastructure/`) depende de la Aplicación (Protocolos) y del Dominio.
- La Web (`src/web/`) coordina y depende de todas las anteriores para orquestar la inyección de dependencias.

### Principio de Inversión de Dependencias (DIP)
Implementado mediante el módulo `typing.Protocol`. Los casos de uso no instancian ni importan clases de infraestructura (`SQLAlchemyBecarioRepository`), sino que declaran sus dependencias a través de interfaces formales (`BecarioRepositoryProtocol`). Esto permite intercambiar la persistencia o inyectar mocks durante los tests sin tocar la lógica de negocio.

### Aggregate Root y Consistencia de Dominio
El modelo de dominio no es un grafo de objetos navegable libremente. Se aplica el concepto de *Aggregate Root* de DDD (Domain-Driven Design). `Becario` es la raíz de su agregado. Toda modificación a `DatosAcademicos`, `Tutoria` o `EnvioCarta` se realiza invocando métodos en la instancia del `Becario`. Esto garantiza que los invariantes del negocio (como RN-02) se protejan de forma centralizada.

### Patrón Repositorio y Unit of Work
Se aísla la lógica de acceso a datos utilizando el Patrón Repositorio. Un repositorio por cada raíz de agregado (y otros actores). SQLAlchemy maneja implícitamente el patrón *Unit of Work* a través de su objeto `Session`. Los repositorios utilizan `session.flush()` para sincronizar el estado con la base de datos dentro de la transacción, delegando el `commit` final al ciclo de vida del request HTTP.

### Patrón Saga (Compensación Manual)
Dado que no existe transaccionalidad distribuida entre PostgreSQL y Supabase Storage, se implementa una versión rudimentaria del patrón Saga. En operaciones compuestas (ej. subir un documento y actualizar la BD), si el paso de base de datos falla, el caso de uso captura la excepción e intenta eliminar de forma compensatoria el archivo previamente subido a Storage para evitar inconsistencias y recursos huérfanos.

---

## 8.2 Seguridad, Autenticación y Autorización

### Identidad Centralizada (Supabase Auth)
La autenticación no la maneja la base de datos relacional de forma directa. La validación de credenciales, gestión de tokens JWT, recuperación de contraseñas y envíos de emails son responsabilidad exclusiva de Supabase Auth. El sistema FONBEC actúa como un cliente (Relying Party) de este servicio.

### Modelo de Invitación Cerrada (Sin Registro Abierto)
El sistema no posee un formulario de registro público. La creación de cuentas sigue un flujo de invitación obligatoria:
1. Un `Administrador` emite una invitación desde el sistema (asignando un rol).
2. Supabase envía un email con un enlace seguro (flujo PKCE).
3. El usuario define su contraseña y completa sus datos personales en un formulario de activación.

### Autorización basada en Roles (RBAC) y Jerarquía
- **Roles:** El sistema soporta cuatro roles activos (`administrador`, `becario`, `tutor`, `mediador`). El rol se codifica en el `user_metadata` del JWT de Supabase Auth y se transfiere a la cookie de sesión de Flask tras el login exitoso.
- **Autorización a nivel de Ruta:** Los Blueprints de Flask agrupan endpoints por rol, limitando el acceso a áreas funcionales.
- **Autorización a nivel de Dominio:** Los referentes (`Tutor`, `Mediador`) solo pueden operar sobre becarios que forman parte de su `lista_becarios` asignada. El dominio valida activamente que el referente tenga permisos sobre el becario solicitado (`seleccionar_becario()`).

### Seguridad de Sesión Web
Las sesiones en el navegador están gestionadas por Flask.
- Las cookies están firmadas criptográficamente (`SECRET_KEY`).
- Atributos obligatorios: `HttpOnly=True` (mitiga XSS) y `SameSite=Lax` (mitiga CSRF).
- Expiración estricta de 30 minutos (riesgo de dispositivos compartidos o públicos).

---

## 8.3 Manejo de Excepciones y Notificaciones al Usuario

### Lanzamiento de Excepciones en el Core
El Dominio y la Aplicación utilizan excepciones nativas de Python (`ValueError`, `PermissionError`, `RuntimeError`) para señalar fallos en reglas de negocio o errores de estado. No utilizan constructos HTTP (códigos 400, 500) ni diccionarios de error estructurados, manteniendo la pureza del lenguaje.

### Captura y Notificación en la Capa Web
Los controladores (Flask Blueprints) son responsables de rodear las llamadas a casos de uso con bloques `try...except`. 
- Si capturan un `ValueError` (error de validación o regla de negocio), extraen el mensaje y lo exponen al usuario mediante la función `flash()` de Flask.
- Los mensajes `flash` se renderizan sistemáticamente en el frontend como alertas (toasts o banners) gracias a la plantilla base (`base.html`).

---

## 8.4 Interfaz de Usuario e Interacción

### Server-Side Rendering (SSR)
Toda la lógica de renderizado recae en el servidor mediante plantillas Jinja2. El cliente (navegador) recibe HTML estático o hidratado por scripts básicos. No se utilizan frameworks de Single Page Application (SPA) ni se desarrollan APIs RESTful/GraphQL consumibles desde el frontend.

### Framework Visual
La apariencia se estandariza utilizando el tema **Argon Dashboard** basado en **Bootstrap 4/5**. Se prioriza el uso intensivo de clases utilitarias (`card`, `btn`, `d-flex`, `text-center`) sobre la escritura de CSS personalizado para acelerar el desarrollo del MVP y mantener consistencia visual.

---

## 8.5 Testing y Calidad

### Aislamiento de Capas
El diseño fuertemente desacoplado facilita el testing unitario. La capa de Dominio se prueba de forma aislada sin requerir mocks complejos. La capa de Aplicación se prueba inyectando repositorios y servicios simulados (mocks que cumplen con los `Protocol`), garantizando que la lógica orquestada por los casos de uso sea correcta sin tocar la red ni la base de datos.

### Validación de Regresiones
Cualquier cambio estructural en los casos de uso, en la máquina de estados o en el ruteo web requiere pasar la suite de más de 100 pruebas (unitarias y de integración) antes de considerarse estable para despliegue.

---

*Sección anterior: [07 — Vista de Despliegue](./07-vista-de-despliegue.md)*  
*Sección siguiente: [09 — Decisiones de Diseño (ADRs)](./09-decisiones-de-diseno.md)*
