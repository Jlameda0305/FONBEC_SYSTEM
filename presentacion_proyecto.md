# Informe Ejecutivo y Presentación Técnica de Avances
**Sistema de Gestión de Becas (FONBEC)**

---

## 1. Contexto y Evolución: El Salto Cualitativo del Proyecto

El requerimiento original planteaba la creación de flujos de trabajo automatizados utilizando la herramienta `n8n`. Esta aproximación es útil para tareas operativas aisladas (por ejemplo, mover un dato de un formulario a una hoja de cálculo). Sin embargo, tras analizar en profundidad los requerimientos de la fundación, el volumen de información, la sensibilidad de los datos manejados (datos de menores, información académica, documentación personal) y la necesidad de una interfaz unificada para distintos tipos de usuarios (Administradores, Padrinos, Becarios), se hizo evidente que `n8n` presentaba limitaciones severas.

**Por qué se descartó la solución simple y se apostó por un desarrollo profesional:**
*   **Seguridad:** Los flujos básicos no proporcionan un control de acceso granular (quién puede ver qué).
*   **Escalabilidad:** Mantener cientos de reglas de negocio en flujos visuales se vuelve inmanejable a medida que la fundación crece.
*   **Experiencia de Usuario (UX):** La fundación necesitaba una plataforma web real (un portal), donde cada usuario tuviera su propio panel de control (*dashboard*), algo imposible de lograr solo con automatizaciones en segundo plano.

En consecuencia, el proyecto evolucionó hacia la construcción de una **Plataforma Web Empresarial Integral**, desarrollada a medida, garantizando que la fundación cuente con una infraestructura propia, independiente de plataformas de terceros y libre de licencias restrictivas.

---

## 2. Los Cimientos: Análisis y Diseño Orientado a Objetos (AOO / DOO)

En la ingeniería de software profesional, no se programa por intuición. Antes de escribir la primera línea de código, se invirtieron semanas en la fase de Análisis y Diseño para modelar computacionalmente la realidad de FONBEC.

### 2.1. Modelado de Entidades del Dominio
Se identificaron y tradujeron a código las entidades clave de la organización:
*   **El Becario (Agregado Raíz):** Es el centro del sistema. Todas las acciones, como subir boletines de calificaciones, asignar un tutor o recibir un pago, orbitan y se validan a través del perfil del becario.
*   **Padrinos y Tutores:** Se modelaron sus relaciones. Un padrino no es solo un nombre, es una entidad que tiene un historial de aportes y una vinculación temporal con uno o múltiples ahijados.
*   **Documentación Académica:** Se estandarizó cómo el sistema entiende un "boletín" o un "certificado de alumno regular", dándole validez y fechas de expiración.

### 2.2. Máquinas de Estado
Se implementaron algoritmos de control de estado para gobernar el ciclo de vida. Un becario no pasa de "Postulante" a "Aprobado" mágicamente; el sistema evalúa (mediante código) si cumple todos los requisitos (documentos completos, entrevista realizada, tutor asignado) antes de permitir la transición. Esto **elimina el error humano** y garantiza la transparencia en las asignaciones.

### 2.3. Reglas de Negocio Estrictas
Se codificaron barreras lógicas inquebrantables. Ejemplo: *Protección de Inmutabilidad*. Si un becario ya se encuentra en estado `APROBADO`, el sistema bloquea automáticamente la posibilidad de que elimine o altere los documentos académicos que sirvieron para su aprobación, protegiendo así la integridad de la auditoría.

---

## 3. Arquitectura del Sistema: Ingeniería de Nivel "Enterprise"

El nivel de dificultad de este proyecto es sustancialmente alto. Para asegurar que la plataforma dure años y no deba ser reescrita en el corto plazo, se utilizó un patrón de diseño avanzado conocido como **Clean Architecture (Arquitectura Limpia)**. 

Este diseño divide el sistema en capas estrictas, funcionando como bóvedas de seguridad:

1.  **Capa de Dominio (El Corazón):** Contiene las reglas puras de FONBEC. No sabe nada de internet ni de bases de datos. Si mañana internet deja de existir, las reglas de cómo se aprueba una beca siguen intactas aquí.
2.  **Capa de Casos de Uso (La Aplicación):** Son los directores de orquesta. Coordinan las acciones ("Registrar Usuario", "Asignar Padrino", "Subir Comprobante").
3.  **Capa de Infraestructura (La Tecnología):** Aquí es donde el sistema se conecta con el mundo exterior: bases de datos PostgreSQL, almacenamiento de archivos, servidores de correo.
4.  **Capa de Presentación (La Web):** Lo que el usuario ve. Diseñado con **Bootstrap (Argon Dashboard)** para proveer una interfaz visual moderna, limpia, responsiva (adaptable a celulares) y altamente profesional.

**Beneficio para la fundación:** Si en 5 años deciden cambiar de base de datos o hacer una aplicación móvil, **no hay que tirar el sistema a la basura**. El "Corazón" está protegido y es reutilizable.

---

## 4. Seguridad de Nivel Mundial: La Complejidad Invisible

Uno de los requerimientos aparentemente "simples" fue el de "Tener un Login". En la web moderna, un sistema de autenticación seguro requiere un trabajo de ingeniería profundo:

*   **Proveedor de Identidad:** Se integró **Supabase Auth**, una tecnología de grado mundial, para manejar la identidad de los usuarios.
*   **Criptografía y Sesiones:** Las contraseñas jamás se guardan legibles (texto plano). Se utilizan algoritmos de *Hashing* unidireccional. Las sesiones se mantienen mediante JWT (*JSON Web Tokens*), asegurando que ninguna página interna pueda ser visitada por alguien no autorizado.
*   **Gestión Integral de Credenciales:** 
    *   Se desarrolló el flujo seguro de **Recuperación de Contraseñas**.
    *   Configuración de servidores de correo (Módulo SMTP) para enviar correos electrónicos automatizados con enlaces seguros de recuperación, con tokens que expiran por seguridad.
*   **Transaccionalidad (Patrón Saga):** ¿Qué pasa si el sistema de registro de usuarios funciona, pero la base de datos se cae a mitad del proceso? Para evitar usuarios "fantasmas" o datos huérfanos, se programaron algoritmos transaccionales. Si una parte falla, el sistema automáticamente "rebobina" y deshace todo para mantener la base de datos 100% limpia.

---

## 5. Infraestructura en la Nube y Base de Datos

Se abandonó el concepto de hojas de cálculo o bases de datos frágiles. 
*   **Base de Datos Relacional (PostgreSQL):** Una base de datos estructurada que mapea relacionalmente toda la información. No hay datos repetidos ni desincronizados. El sistema utiliza mapeo ORM (*Object-Relational Mapping*) imperativo con SQLAlchemy para traducir objetos de Python en tablas complejas.
*   **Almacenamiento de Archivos (Supabase Storage):** Cuando un becario sube su DNI o un boletín, este no se guarda en una carpeta suelta. Se encripta, se asigna a un *Bucket* (repositorio de almacenamiento en la nube) con reglas estrictas de seguridad (RLS - *Row Level Security*). Nadie fuera de la fundación puede acceder a ese enlace.

---

## 6. Métricas de Esfuerzo y Volumen de Trabajo

Para dimensionar el tamaño real del producto que se está entregando:

*   **Volumen de Código:** El sistema cuenta con aproximadamente **20.000 líneas de código propio**, escritas desde cero, sin contar librerías de terceros.
    *   **Backend (Python):** Más de 13.000 líneas dedicadas exclusivamente a lógica de negocio, transacciones de base de datos, enrutamiento de seguridad y algoritmos.
    *   **Frontend (Plantillas HTML/Jinja2):** Más de 5.000 líneas de código para estructurar visualmente los paneles, formularios y tablas que utilizan los administradores y usuarios.
*   **Complejidad:** El desarrollo involucró conocimientos de bases de datos relacionales, programación orientada a objetos en Python, desarrollo web del lado del servidor (Flask), integración de APIs externas y maquetado frontend.

---

## 7. Próximos Pasos: A dos pasos del Producto Mínimo Viable (MVP)

Estamos en la recta final para el lanzamiento de la primera versión operativa (MVP). La infraestructura pesada, la seguridad y el modelado de datos ya están construidos. 

Las siguientes etapas son las más interactivas con la fundación:

1.  **Descubrimiento y Ajuste de Reglas de Negocio:** Es normal y esperado que, al empezar a utilizar las pantallas, la fundación detecte que ciertos procesos de la vida real funcionan ligeramente distinto a lo planificado. **La plataforma fue diseñada exactamente para soportar estos cambios.** Los ajustes a las reglas de negocio son rápidos gracias a la Arquitectura Limpia.
2.  **Pruebas Integrales y de Flujo (QA):** Simular el recorrido completo de cientos de perfiles para asegurar que la experiencia sea fluida.
3.  **Despliegue a Producción:** Puesta a punto final del servidor donde la plataforma quedará alojada de manera permanente para su acceso público.

---

### Conclusión
FONBEC no está recibiendo un "parche" tecnológico ni una automatización temporal. Está recibiendo una **Plataforma de Software a medida**, construida bajo los más altos estándares de ingeniería, diseñada para ser segura, escalable y el pilar tecnológico de la fundación para los próximos años.
