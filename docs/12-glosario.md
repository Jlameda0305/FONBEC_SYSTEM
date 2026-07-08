# 12. Glosario

Este glosario define el *Ubiquitous Language* (Lenguaje Oblicuo) del Dominio del sistema FONBEC, garantizando que el equipo de desarrollo, los arquitectos y los expertos del negocio utilicen los mismos términos técnicos y conceptuales sin ambigüedades.

| Término | Definición |
| --- | --- |
| **Usuario** | Entidad abstracta que define el contrato base de autenticación, autorización y perfil para todos los actores que poseen acceso interactivo al sistema. |
| **Becario** | *Aggregate Root* y eje central del modelo de negocio. Todas las entidades operativas (Tutorías, Envíos de Cartas, Datos Académicos) existen estrictamente en su contexto y se navegan exclusivamente a través de él. |
| **Administrador** | Actor de gestión global encargado del alta, baja, modificación (CRUD) de usuarios y de las vinculaciones entre Becarios, Tutores, Mediadores y Padrinos. |
| **Referente** | Abstracción arquitectónica que agrupa el comportamiento y estado común de los actores (Tutor y Mediador) que tienen una lista de becarios a cargo. |
| **Tutor** | Referente responsable exclusivo de la programación, gestión y seguimiento de las *Tutorías* del becario asignado. A diferencia del mediador, no posee permisos para aprobar o rechazar datos académicos. |
| **Mediador** | Referente con potestad exclusiva para auditar (Aprobar/Rechazar) los *Datos Académicos* y gestionar el calendario de *Envío de Cartas* al padrino del becario. |
| **Padrino** | Entidad pasiva de dominio puro **sin acceso al sistema**. Actúa únicamente como destinatario referencial en el flujo de envío de cartas. Es fundamental comprender que no hereda de *Usuario*. |
| **Datos Académicos** | Entidad de composición directa de un Becario que encapsula su carrera, nivel de avance y materias. Su ciclo de vida está gobernado por una máquina de estados estricta (Vacio, Incompleto, Pendiente_Revision, Pendiente_Modificar, Aprobado). |
| **Documento Académico** | Representación de un archivo físico (ej. PDF alojado en Supabase Storage) que respalda y valida la situación académica cargada por un becario. |
| **Tutoría** | Entidad transaccional de calendario que representa un encuentro programado entre el Tutor y el Becario. Su persistencia y navegación dependen del Becario. |
| **Envío de Carta** | Entidad transaccional de calendario que representa la programación del envío físico/digital de una misiva del Becario hacia su Padrino, gestionada y supervisada operativamente por el Mediador. |
