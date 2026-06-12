# Observaciones y Excepciones de Arquitectura

## Excepción al Estándar CSS Vainilla
*   **Fecha de aprobación:** 2026-06-12
*   **Contexto:** El estándar técnico original (reflejado en `AGENTS.md`) estipulaba el uso exclusivo de CSS Vainilla y prohibía frameworks de utilidades.
*   **Resolución:** Se aprueba formalmente el uso de la plantilla **Argon Dashboard Flask** (basada en Bootstrap 4) para la capa de presentación (UI). Las plantillas Jinja2 utilizarán las clases de utilidad y componentes de Argon (`bg-gradient-primary`, `container-fluid`, `card shadow`, `table-flush`, etc.) para agilizar el desarrollo y unificar el diseño. La estilización propia se limitará a sobrescribir variables en `fonbec-custom.css` (tokens de la marca).
