<div align="center">
  <img src="images/VARIACION%203%20NEGRO.png" alt="FONBEC Logo" width="250">
</div>

# Documentación Arquitectónica FONBEC — Resumen General

**Versión:** 1.0  
**Fecha:** 2026-07-07  
**Estado:** Activo  

---

## 1. Introducción

El presente documento actúa como punto de entrada unificado a la documentación del **Sistema de Gestión de Becas (FONBEC)**. Su objetivo es proporcionar un panorama general del modelo de dominio, los actores involucrados, y servir como índice para la documentación técnica elaborada bajo el estándar **arc42**.

FONBEC es una plataforma web desarrollada con **Clean Architecture** en **Python (Flask)** y respaldada por **Supabase (PostgreSQL, Auth, Storage)**. Su propósito es gestionar el ciclo de vida académico de los becarios, así como la vinculación y operaciones entre Tutores, Mediadores, Padrinos y el Administrador.

---

## 2. Índice de la Documentación Técnica (arc42)

La arquitectura profunda, componentes, decisiones y restricciones están detalladas en los siguientes documentos dentro de este directorio (`docs/`):

1. **`01-introduccion-y-metas.md`**: Metas del negocio y requerimientos fundamentales.
2. **`02-restricciones-arquitectura.md`**: Limitaciones tecnológicas, operativas y de convención.
3. **`03-alcance-y-contexto.md`**: Fronteras del sistema y comunicación con el exterior.
4. **`04-estrategia-solucion.md`**: Enfoque de Clean Architecture y decisiones fundamentales.
5. **`05-vista-de-bloques.md`**: Descomposición en capas y componentes (Niveles 1 al 3).
6. **`06-vista-de-ejecucion.md`**: Flujos de interacción, creación de usuarios y auditoría.
7. **`07-vista-de-despliegue.md`**: Topología de infraestructura (Flask + Supabase en la nube).
8. **`08-conceptos-transversales.md`**: Autenticación, manejo de errores, seguridad, inyección de dependencias.
9. **`09-decisiones-de-diseno.md`**: ADRs clave (ej. SSR con Jinja2, ORM Imperativo).
10. **`10-requerimientos-de-calidad.md`**: Árbol de calidad y escenarios principales.
11. **`11-riesgos-y-deuda-tecnica.md`**: Riesgos de seguridad, arquitectura y tareas pendientes.
12. **`12-glosario.md`**: Lenguaje ubicuo y definiciones del dominio.

---

## 3. Resumen del Modelo de Dominio y Orientación a Objetos

El dominio está estructurado alrededor del concepto de un **Agregado Raíz** (*Aggregate Root*).

### 3.1. Jerarquía Principal

```text
Usuario (abstracta)  
├── Becario                    ← Aggregate Root del modelo  
├── Administrador              ← Actor de gestión global
├── Referente (abstracta)  
│   ├── Tutor  
│   └── Mediador  
  
Padrino                        ← Entidad de dominio (sin acceso al sistema)  
DatosAcademicos                ← Entidad de dominio  
DocumentoAcademico             ← Entidad de dominio  
Tutoria                        ← Entidad de dominio  
EnvioCarta                     ← Entidad de dominio
```

### 3.2. El Becario como Aggregate Root
**Becario** es el eje natural del modelo de negocio. Todas las entidades operativas del sistema (`Tutoria`, `EnvioCarta`, `DatosAcademicos`) existen en el contexto de un becario y se navegan exclusivamente a través de él. La relación entre `Tutor` y `Mediador` tampoco es directa: siempre pasa por el becario que los conecta (RN-03).

---

## 4. Actores del Sistema y Responsabilidades

1. **Administrador:**
   - Actor de gestión central.
   - Crea, elimina y gestiona usuarios en la plataforma.
   - Establece las vinculaciones entre Becarios, Tutores, Mediadores y Padrinos (RN-01).

2. **Becario:**
   - Carga y actualiza sus datos académicos y documentos respaldatorios (PDFs).
   - Visualiza sus calendarios de tutorías y envíos de cartas.
   - Tiene exactamente 1 Tutor, 1 Mediador y 1 Padrino asignado (relación 1:1).

3. **Mediador:**
   - **Auditoría:** Es el único rol con potestad de auditar (Aprobar/Rechazar) los `DatosAcademicos` del becario (RN-09).
   - Gestiona (crea, actualiza) el calendario de *Envío de Cartas* hacia los padrinos.

4. **Tutor:**
   - **Acompañamiento:** Responsable de la gestión de *Tutorías* (crear, actualizar, cancelar) del becario.
   - Visualiza los datos académicos de su becario asignado, pero sin permisos de auditoría.

5. **Padrino:**
   - Entidad de referencia pura. Es el destinatario de las cartas gestionadas por el Mediador.
   - **No posee acceso al sistema**.

---

## 5. Reglas de Negocio Esenciales

A continuación se resumen las directrices inquebrantables del dominio:

- **RN-01:** Un becario tiene exactamente un tutor, un mediador y un padrino asignados (1:1).
- **RN-02 (Protección de Inmutabilidad):** Un becario no puede modificar sus `DatosAcademicos` si su `estado_verificacion` es `Aprobado`.
- **RN-03 (Aislamiento de Referentes):** No existe relación directa entre `Tutor` y `Mediador`. Toda navegación entre ellos pasa a través del `Becario`.
- **RN-04:** Eliminar una tutoría o envío de carta únicamente cambia su estado a `Cancelada`. El registro nunca se elimina físicamente (Soft Delete conceptual).
- **RN-09:** La auditoría de datos académicos es responsabilidad exclusiva del `Mediador`. Ningún otro actor puede ejecutarla.

---

## 6. Resumen de Casos de Uso (MVP)

La plataforma soporta las siguientes operaciones principales:

- **Autenticación:** Login, Logout, y restablecimiento de contraseñas.
- **Gestión Administrativa:** Invitación de usuarios y vinculación de perfiles (Admin).
- **Gestión Académica:** 
  - Llenado y actualización de formulario académico (Becario).
  - Visualización de datos (Todos los roles según vinculación).
  - Auditoría de datos académicos: Aprobar / Rechazar (Mediador).
- **Calendarios e Interacciones:**
  - Creación, actualización y eliminación lógica de Tutorías (Tutor).
  - Asignación y actualización de fechas de Envío de Cartas (Mediador).
  - Obtención de datos de contacto de referentes mediante enlaces directos a WhatsApp/Teléfono (Becario, Tutor, Mediador).

---

> **Nota:** Este documento consolida el Análisis Orientado a Objetos (AOO) original dentro del nuevo estándar de documentación arc42. Para decisiones de diseño concretas o detalles de implementación, referirse a los archivos numerados `01-` a `12-`.
