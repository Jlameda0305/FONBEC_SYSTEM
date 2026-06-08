Postcondición: Visualización del calendario seleccionado o mensaje informativo.
CU-02: Contactar
Actores: Becario, Tutor, Mediador
Precondiciones según actor:Becario: autenticado, con tutor y/o mediador asignado.
Mediador: autenticado, con becario seleccionado y tutor asignado a ese becario.
Tutor: autenticado, con becario seleccionado y mediador asignado a ese becario.
Flujos por actor:
Becario contacta a Tutor o Mediador:
El becario selecciona a quién contactar.
El sistema invoca puntero\_tutor.get\_datos\_contacto() o puntero\_mediador.get\_datos\_contacto().
Se presenta el enlace directo de contacto (wa.me / tel:).
Mediador contacta al becario seleccionado o tutor del becario:
Desde la vista del becario, el mediador selecciona “Contactar becario” o “Contactar Tutor”.
El sistema navega becario\_seleccionado.puntero\_tutor.get\_datos\_contacto() o
becario\_seleccionado.get\_datos\_contacto.
Se presenta el enlace directo.
Tutor contacta al Mediador del becario seleccionado:
Desde la vista del becario, el tutor selecciona “Contactar becario” o “Contactar Mediador”.
El sistema navega becario\_seleccionado.puntero\_mediador.get\_datos\_contacto() o
becario\_seleccionado.get\_datos\_contacto..
Se presenta el enlace directo.
Flujos alternativos:
Sin tutor/mediador asignado → mensaje “No posee tutor asignado” / “No posee mediador asignado”.
Sin número de contacto registrado → mensaje “Sin número de teléfono asociado”.
Postcondición: Apertura de enlace de contacto directo.
CU-03: Llenar / Actualizar Formulario Académico
Actor: Becario
Precondiciones:
Becario autenticado.
estado\_verificacion de sus DatosAcademicos ≠ Aprobado.
Flujo principal:
El becario solicita el formulario.
El sistema recupera los datos académicos actuales y los envía a la interfaz.
El becario completa o actualiza los campos.
El becario finaliza el llenado.
El sistema valida los datos ingresados.
El sistema asigna estado Pendiente\_Revision y persiste.
Flujos alternativos:
Datos inválidos (tipado incorrecto) → mensaje en los campos correspondientes; el becario corrige.
Campos obligatorios incompletos → bloqueo del envío; mensaje en el campo faltante.
Campos no obligatorios incompletos → el sistema asigna estado Incompleto y persiste.
Datos ya aprobados → mensaje “Los datos académicos han sido aprobados y no pueden modificarse”.
Postcondición: Datos persistidos con el estado correspondiente.CU-04: Visualizar Datos Académicos
Actores: Becario, Tutor, Mediador
Precondiciones:
Becario: autenticado; haber llenado datos con anterioridad.
Tutor / Mediador: autenticado; becario seleccionado.
Flujo principal:
El actor solicita la visualización de datos académicos.
El sistema recupera DatosAcademicos por id\_becario.
El sistema envía la información a la interfaz.
Comportamiento según estado y rol:Estado Becario TutorVacio Mensaje “debes llenar el formulario” Mensaje “el becario no ha cargado datos”Incompleto Visualiza datos con campos faltantes remarcados Visualiza con campos faltantes remarcadosPendiente\_Revision Visualiza con estado Visualiza + opciones Aprobar / RechazarPendiente\_Modificar Visualiza datos + observaciones del Tutor Visualiza datos + observacionesAprobado Visualiza con estado VisualizaPostcondición: Visualización de datos académicos con las opciones disponibles según rol y estado.
CU-05: Listar Becarios
Actores: Tutor, Mediador
Precondición: Actor autenticado.
Flujo principal:
El actor solicita su lista de becarios.
El sistema recupera lista\_becarios del actor y la envía a la interfaz.
Flujo alternativo:
Lista vacía → mensaje “Sin becarios asociados”.
Postcondición: Listado de becarios asignados al actor.
CU-06: Seleccionar Becario — Tutor
Actor: Tutor
Precondición: Haber ejecutado CU-05 (Listar Becarios).
Flujo principal:
El tutor selecciona un becario de la lista.
El sistema procesa la solicitud con el id\_becario.
El sistema recupera los datos y los envía a la interfaz.
Flujo alternativo:
id\_becario no encontrado → mensaje “El becario no se encuentra registrado, contactar al sistema fonbec”.
Dato sin asignar → etiqueta “Sin datos asignados” en el campo correspondiente.
Postcondición: Visualización del perfil del becario con los siguientes datos y accesos:Dato / Accesoid\_usuario, nombre, apellidoedad, sexo, direccion, nivel\_cursadoestado\_datos\_academicos + opción Ver datos académicosFecha de tutoría más cercana + opción Ver calendario de tutoríasemail, telefono del becario + opción ContactarMediador asignado: nombre, email, telefono + opción Contactar Mediador
