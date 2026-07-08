<div align="center">
  <img src="images/VARIACION%203%20NEGRO.png" alt="FONBEC Logo" width="250">
</div>

# 9. Decisiones de Diseño Arquitectónico (ADRs)

Esta sección documenta formalmente las decisiones de arquitectura más críticas, costosas de revertir o con mayor impacto en el ciclo de vida del sistema FONBEC. Se utiliza el formato ADR (Architecture Decision Record) para capturar el contexto, la decisión y sus consecuencias.

---

## ADR-001: Adopción de Clean Architecture Estricta

**Estado:** Aceptado  
**Fecha de registro:** (Documentado retroactivamente para el MVP)

### Contexto
El sistema debía gestionar reglas de negocio complejas (auditorías, máquinas de estado, restricciones de mutabilidad) orquestadas por distintos actores (Becario, Tutor, Mediador). Utilizar el patrón MVC tradicional de Flask (donde los modelos heredan del ORM y los controladores mezclan lógica HTTP con lógica de negocio) habría resultado en un código fuertemente acoplado, difícil de probar sin levantar bases de datos, y propenso a regresiones ante cambios en las reglas institucionales.

### Decisión
Se decidió organizar el proyecto bajo el patrón **Clean Architecture** (Arquitectura Limpia) con 4 capas explícitas y dependencias unidireccionales concéntricas:
1. `domain/`: Reglas puras, sin dependencias.
2. `application/`: Casos de uso y Protocolos de inversión de dependencias (DIP).
3. `infrastructure/`: Implementaciones técnicas (Repositorios, Auth, Storage).
4. `web/`: Controladores Flask (Blueprints).

### Consecuencias
- **Positivas:** 
  - La lógica de negocio (`domain`) y los casos de uso (`application`) pueden testearse al 100% mediante pruebas unitarias rápidas y asiladas.
  - El Dominio no tiene "contaminación" de decoradores de bases de datos ni lógicas de ruteo, lo que facilita razonar sobre él.
- **Negativas / Riesgos:**
  - Aumenta la fricción inicial para desarrolladores no familiarizados con el patrón (curva de aprendizaje pronunciada).
  - Requiere verbosidad adicional: los datos deben serializarse/deserializarse en los bordes de la capa de aplicación (DTO mapping) en vez de pasar objetos del ORM directamente a la vista.

---

## ADR-002: Supabase como Único Proveedor de Infraestructura Cloud

**Estado:** Aceptado  

### Contexto
El MVP requería implementar rápidamente una base de datos relacional robusta, gestión segura de identidades (con invitaciones y recuperación de contraseñas) y almacenamiento de archivos binarios (PDFs). Configurar servidores independientes para PostgreSQL, un servidor SMTP para correos, un proveedor OAuth2/JWT y un bucket S3 habría consumido gran parte del presupuesto temporal del MVP.

### Decisión
Se decidió delegar **toda la infraestructura cloud a Supabase**, utilizando tres de sus servicios interconectados:
- Supabase PostgreSQL
- Supabase Auth (Admin API + flujos PKCE)
- Supabase Storage

### Consecuencias
- **Positivas:**
  - Desarrollo acelerado al usar una única plataforma y SDK (`supabase-py`).
  - No hubo necesidad de desarrollar lógica criptográfica de hash de contraseñas, envío de correos, ni validación de tokens JWT en el core de la aplicación; todo se delegó.
- **Negativas / Riesgos:**
  - **Vendor Lock-in extremo:** El sistema no puede funcionar sin Supabase. Migrar a otro proveedor requeriría reescribir gran parte de la capa de infraestructura y los flujos de autenticación.
  - La disponibilidad del sistema depende del SLA de un único tercero. Un fallo en Supabase Auth inutiliza toda la aplicación web, aunque la BD esté operativa.

---

## ADR-003: Mapeo Imperativo con SQLAlchemy

**Estado:** Aceptado  

### Contexto
SQLAlchemy 2.x promueve por defecto el uso del mapeo declarativo (donde las clases heredan de una clase `Base` y declaran columnas como atributos). Sin embargo, este enfoque entra en conflicto directo con la decisión ADR-001 (Clean Architecture), ya que obliga a la capa de dominio a importar y depender de la biblioteca del ORM.

### Decisión
Se decidió utilizar el mecanismo de **Mapeo Imperativo** de SQLAlchemy (`registry.map_imperatively()`). 
1. El modelo de Dominio se implementa como clases puras (`@dataclass`).
2. El esquema físico se define usando SQLAlchemy Core (`Table`, `Column`) en `schema.py`.
3. El binding entre ambos mundos se configura en un archivo puente (`mapping.py`) que pertenece estrictamente a la capa de infraestructura.

### Consecuencias
- **Positivas:**
  - Las entidades de dominio se mantienen 100% "limpias" e ignorantes de cómo serán persistidas (Separation of Concerns puro).
  - Fue posible implementar un diseño de base de datos de *Concrete Table Inheritance* para los distintos actores, mapeándolos correctamente hacia sus respectivas clases de dominio.
- **Negativas / Riesgos:**
  - El mapeo imperativo es menos idiomático en la comunidad actual de Python/SQLAlchemy, dificultando la búsqueda de documentación o ejemplos en línea.
  - Cualquier adición de un campo en el dominio requiere modificar tres lugares: la dataclass, la tabla en `schema.py` y, potencialmente, la definición del mapeo en `mapping.py`.

---

## ADR-004: Aggregate Root Centralizado en `Becario`

**Estado:** Aceptado  

### Contexto
El modelo de datos incluye entidades operativas como `DatosAcademicos`, `Tutoria` y `EnvioCarta`. Permitir que la capa de aplicación recupere y modifique estas entidades directamente desde la base de datos podría derivar en inconsistencias, eludiendo reglas de negocio dependientes del estado general (ej. RN-02: bloqueo de documentos en estado APROBADO).

### Decisión
Se designó a la clase `Becario` como el único **Aggregate Root** (Raíz de Agregado) para todas las operaciones académicas y de vinculación. Ningún caso de uso instancia un repositorio directo de `DatosAcademicos` o `Tutoria`. Toda persistencia se realiza llamando a `SQLAlchemyBecarioRepository.guardar(becario)`.

### Consecuencias
- **Positivas:**
  - Integridad transaccional y de estado garantizada en el dominio.
  - Facilita el caché o la optimización en consultas (e.g. `lazy="joined"`).
- **Negativas / Riesgos:**
  - Operaciones menores (ej. cambiar el estado de una tutoría aislada) requieren cargar el objeto `Becario` completo en memoria y persistir todo el grafo de objetos asociados, lo que es ineficiente en escenarios de alto volumen de datos concurrentes.

---

*Sección anterior: [08 — Conceptos Transversales](./08-conceptos-transversales.md)*  
*Sección siguiente: [10 — Requerimientos de Calidad](./10-requerimientos-de-calidad.md)*
