### CU-02: Contactar

**Actores:** Becario, Tutor, Mediador

**Precondiciones según actor:**

- Becario: autenticado, con tutor y/o mediador asignado.

- Mediador: autenticado, con becario seleccionado y tutor asignado a ese becario.

- Tutor: autenticado, con becario seleccionado y mediador asignado a ese becario.

**Flujos por actor:**

*Becario contacta a Tutor o Mediador:*

1. El becario selecciona a quién contactar.

2. El sistema invoca puntero\\\_tutor.get\\\_datos\\\_contacto() o puntero\\\_mediador.get\\\_datos\\\_contacto().

3. Se presenta el enlace directo de contacto (wa.me / tel:).

*Mediador contacta al becario seleccionado o tutor del becario:*

1. Desde la vista del becario, el mediador selecciona “Contactar becario” o "Contactar Tutor".

2. El sistema navega becario\\\_seleccionado.puntero\\\_tutor.get\\\_datos\\\_contacto() o becario\\\_seleccionado.get\\\_datos\\\_contacto.

3. Se presenta el enlace directo.

*Tutor contacta al Mediador del becario seleccionado:*

1. Desde la vista del becario, el tutor selecciona “Contactar becario” o "Contactar Mediador".

2. El sistema navega becario\\\_seleccionado.puntero\\\_mediador.get\\\_datos\\\_contacto() o becario\\\_seleccionado.get\\\_datos\\\_contacto..

3. Se presenta el enlace directo.

**Flujos alternativos:**

- Sin tutor/mediador asignado → mensaje "No posee tutor asignado" / "No posee mediador asignado".

- Sin número de contacto registrado → mensaje "Sin número de teléfono asociado".

**Postcondición:** Apertura de enlace de contacto directo.

### CU-03: Llenar / Actualizar Formulario Académico

**Actor:** Becario

**Precondiciones:**

- Becario autenticado.

- estado\\\_verificacion de sus DatosAcademicos ≠ Aprobado.

**Flujo principal:**

1. El becario solicita el formulario.

2. El sistema recupera los datos académicos actuales y los envía a la interfaz.

3. El becario completa o actualiza los campos.

4. El becario finaliza el llenado.

5. El sistema valida los datos ingresados.

6. El sistema asigna estado Pendiente\\\_Revision y persiste.

**Flujos alternativos:**

- Datos inválidos (tipado incorrecto) → mensaje en los campos correspondientes; el becario corrige.

- Campos obligatorios incompletos → bloqueo del envío; mensaje en el campo faltante.

- Campos no obligatorios incompletos → el sistema asigna estado Incompleto y persiste.

- Datos ya aprobados → mensaje "Los datos académicos han sido aprobados y no pueden modificarse".

**Postcondición:** Datos persistidos con el estado correspondiente.

### CU-04: Visualizar Datos Académicos

**Actores:** Becario, Tutor, Mediador

**Precondiciones:**

- Becario: autenticado; haber llenado datos con anterioridad.

- Tutor / Mediador: autenticado; becario seleccionado.

**Flujo principal:**

1. El actor solicita la visualización de datos académicos.

2. El sistema recupera DatosAcademicos por id\\\_becario.

3. El sistema envía la información a la interfaz.

**Comportamiento según estado y rol:**

| Estado | Becario | Tutor | Mediador |
| - | - | - | - |
| Vacio | Mensaje "debes llenar el formulario" | Mensaje "el becario no ha cargado datos" | Igual que Tutor |
| Incompleto | Visualiza datos con campos faltantes remarcados | Visualiza con campos faltantes remarcados | Visualiza |
| Pendiente\\\_Revision | Visualiza con estado | Visualiza + opciones **Aprobar** / **Rechazar** | Visualiza con estado |
| Pendiente\\\_Modificar | Visualiza datos + observaciones del Tutor | Visualiza datos + observaciones | Visualiza |
| Aprobado | Visualiza con estado | Visualiza | Visualiza |


**Postcondición:** Visualización de datos académicos con las opciones disponibles según rol y estado.

### CU-05: Listar Becarios

**Actores:** Tutor, Mediador

**Precondición:** Actor autenticado.

**Flujo principal:**

1. El actor solicita su lista de becarios.

2. El sistema recupera lista\\\_becarios del actor y la envía a la interfaz.

**Flujo alternativo:**

- Lista vacía → mensaje "Sin becarios asociados".

**Postcondición:** Listado de becarios asignados al actor.

### CU-06: Seleccionar Becario — Tutor

**Actor:** Tutor

**Precondición:** Haber ejecutado CU-05 (Listar Becarios).

**Flujo principal:**

1. El tutor selecciona un becario de la lista.

2. El sistema procesa la solicitud con el id\\\_becario.

3. El sistema recupera los datos y los envía a la interfaz.

**Flujo alternativo:**

- id\\\_becario no encontrado → mensaje "El becario no se encuentra registrado, contactar al sistema fonbec".

- Dato sin asignar → etiqueta "Sin datos asignados" en el campo correspondiente.

**Postcondición:** Visualización del perfil del becario con los siguientes datos y accesos:

| Dato / Acceso |
| - |
| id\\\_usuario, nombre, apellido |
| edad, sexo, direccion, nivel\\\_cursado |
| estado\\\_datos\\\_academicos + opción Ver datos académicos |
| Fecha de tutoría más cercana + opción Ver calendario de tutorías |
| email, telefono del becario + opción Contactar |
| Mediador asignado: nombre, email, telefono + opción Contactar Mediador |


CU-08: Auditar Datos Académicos (función principal del Tutor) Actor: Tutor Precondiciones: Becario seleccionado. Vista de datos académicos activa (CU-04). estado\_verificacion = Pendiente\_Revision. Flujo principal — Aprobación: El tutor verifica manualmente la información. El tutor selecciona “Aprobar”. El sistema invoca datos\_academicos.actualizar\_estado(Aprobado). El sistema persiste el nuevo estado. El sistema envía los datos al sistema externo Fonbec (mecanismo de integración: alcance futuro). Flujo alternativo — Rechazo: El tutor selecciona “Rechazar”. El sistema habilita un campo para cargar observaciones. El tutor ingresa las observaciones. El sistema invoca datos\_academicos.actualizar\_estado(Pendiente\_Modificar). El sistema persiste el nuevo estado y las observaciones. Flujo alternativo — Datos insuficientes: Estado Incompleto o Vacio → opciones Aprobar/Rechazar no disponibles → mensaje “Contactar al becario para completar los datos”. Postcondición: Estado de DatosAcademicos actualizado.

