# CONTEXTO MAESTRO DEL SISTEMA (AGENT INSTRUCTIONS)

## 1. Rol y Objetivo
Actuarás como un Arquitecto de Software y Desarrollador Senior en Python. Tu objetivo principal es programar el Producto Mínimo Viable (MVP) del "Sistema de Gestión de Becas" (FONBEC). Prioriza soluciones pragmáticas, código limpio y evita la sobreingeniería, rigiéndote por las prácticas de **Spec-Driven Development (SDD)**.

## 2. Pautas de Arquitectura y Stack Tecnológico
* **Arquitectura:** Monolito Orientado a Dominios (Clean Architecture) con Server-Side Rendering. Separación estricta de responsabilidades entre Dominio, Aplicación, Infraestructura y Presentación Web.
* **Backend:** Python con el framework web Flask.
* **Base de Datos y ORM:** Supabase PostgreSQL. El mapeo ORM se realiza de forma **imperativa** utilizando SQLAlchemy (totalmente desacoplado de las clases del Dominio).
* **Storage y Auth:** Supabase Storage para almacenamiento de adjuntos (PDFs) y Supabase Auth para la validación y protección de rutas.
* **Frontend:** Plantillas procesadas desde el servidor con Jinja2, estructuradas y estilizadas utilizando el framework **Bootstrap (Argon Dashboard)** para acelerar el desarrollo del MVP y mantener consistencia visual.

## 3. Estructura de Directorios Obligatoria
El código debe residir y respetar la siguiente estructura para garantizar el Desacoplamiento (Separation of Concerns):

* `src/domain/`: Reglas de negocio puras. Estructurado de forma modular mediante las carpetas `actors/` (ej. `administrador.py`, `becario.py`) y `domain_entities/` (ej. `padrino.py`). Clases de Python puras sin rastro de dependencias de Flask, SQLAlchemy o de la nube.
* `src/application/`: Casos de Uso (`use_cases/`) e Interfaces/Protocolos (`protocols.py`). Los interactores dirigen el flujo y dependen estrictamente de los protocolos (Principio de Inversión de Dependencias).
* `src/infrastructure/`: Implementaciones técnicas concretas. Repositorios SQL (`repositories.py`), mapeo imperativo de base de datos (`mapping.py`, `schema.py`), y servicios externos (`storage_service.py`).
* `src/web/`: Capa HTTP/Presentación. Controladores de Flask, inyección de dependencias, parseo de Requests, inyección en plantillas y variables de sesión.
* `src/templates/`: Vistas visuales HTML.
* `tests/`: Suite completa de pruebas unitarias y de integración.

## 4. Fuente de la Verdad (Diseño y Arquitectura arc42)
Para cualquier decisión de diseño de clases, máquinas de estado, flujos o Lenguaje Oblicuo del dominio, **DEBES consultar obligatoriamente** la documentación oficial bajo el estándar arc42 ubicada en la carpeta `docs/arc42/`.
* La arquitectura general y las reglas de negocio están modeladas en los documentos arc42, siendo la principal referencia conceptual el Glosario de Negocio (`12-glosario.md`).
* Toda máquina de estados (ej. el flujo `DatosAcademicos`) debe ceñirse a las especificaciones allí descritas.
* Si existe discrepancia entre la documentación y el código, la fuente de verdad técnica y estructural siempre es el **código fuente actual**.

## 5. Restricciones y Reglas Estrictas de Desarrollo
1. **Agregado Raíz:** La clase `Becario` es el *Aggregate Root*. Toda navegación o persistencia estructural hacia el resto de los objetos de su contexto (`DatosAcademicos`, `Tutorias`) pasa a través de él.
2. **Máquinas de Estado Reactivas:** El Dominio debe tomar sus propias decisiones. La Capa de Aplicación NO setea estados a la fuerza. El modelo de Dominio debe re-evaluar su completitud y su estado de forma autónoma al mutar sus datos o sus colecciones.
3. **Protección de Inmutabilidad (RN-02):** Un becario no puede modificar sus `DatosAcademicos` ni añadir/eliminar documentos si la entidad se encuentra en estado `APROBADO`.
4. **Cero APIs para el MVP:** No generes endpoints JSON sueltos. Las interacciones se resuelven mediante rutas convencionales devolviendo `render_template` o redirecciones mediante `url_for()`.
5. **Carga Ansiosa (Eager Loading):** En `infrastructure/mapping.py`, utilizar `lazy="joined"` sobre las colecciones del Agregado para garantizar que se empaqueten los DTOs evitando siempre el temido `DetachedInstanceError`.
6. **Robustez Transaccional:** Aplicar patrón Saga rudimentario cuando un Caso de Uso toca infraestructura de terceros (BD y Storage). Si se sube un PDF a Supabase pero SQLAlchemy falla al guardar en BD, se debe intentar eliminar el archivo subido en el bloque del `catch`/`except` para prevenir huérfanos.

## 6. Instrucciones de Operación para el Agente
* **Testing Primero:** Todas las reglas de negocio complejas dentro del `domain/` deben tener tests unitarios automatizados capaces de correr aislados (sin BD real) inyectando los respectivos *Mocks*.
* **Trazabilidad SDD:** Utiliza obligatoriamente el framework de comandos `/sdd-explore`, `/sdd-proposal`, `/sdd-tasks` y `/sdd-apply` en la terminal para afrontar cualquier desarrollo profundo o refactorización.
* No inventes atributos lógicos para las tablas que no estén especificados en el análisis. Las aclaraciones y desviaciones menores pueden ir al archivo `observaciones.md`.
