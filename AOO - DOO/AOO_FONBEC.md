# Análisis Orientado a Objetos


## 1. Modelo de Clases

### Jerarquía general

```
Usuario (abstracta)  
├── Becario                    ← Aggregate Root del modelo  
├── Referente (abstracta)  
│   ├── Tutor  
│   └── Mediador  
  
Padrino                        ← Entidad de dominio (sin acceso al sistema)  
DatosAcademicos                ← Entidad de dominio  
DocumentoAcademico             ← Entidad de dominio  
Tutoria                        ← Entidad de dominio  
EnvioCarta                     ← Entidad de dominio
```


### 1.1 Superclase Abstracta: `Usuario`

Todos los actores del sistema con acceso comparten esta base.

- **Atributos:**

  - `id\_usuario`

  - `nombre`

  - `apellido`\\

  - `email`

  - `telefono`

  - `edad`

  - `sexo`

  - `direccion`

  - `password\_hash`

  - `rol`

- **Métodos:**

  - `login()`

  - `logout()`

  - `actualizar\_datos\_personales()`

  - `restablecer\_contrasena()`

  - `visualizar\_datos\_academicos()` *(abstracto)*

> **Nota de diseño — `visualizar\_datos\_academicos()`:** Se declara abstracto en `Usuario` porque el comportamiento difiere según el actor: `Becario` visualiza sus propios datos; `Tutor` y `Mediador` visualizan los de un becario seleccionado. Cada subclase provee su implementación concreta, respetando el Principio Abierto/Cerrado.


### 1.2 Subclase: `Becario`

> **Nota de diseño — Becario como Aggregate Root:** `Becario` es el eje natural del modelo de negocio. Todas las entidades operativas del sistema (`Tutoria`, `EnvioCarta`, `DatosAcademicos`) existen en el contexto de un becario y se navegan exclusivamente a través de él. La relación entre `Tutor` y `Mediador` tampoco es directa: siempre pasa por el becario que los conecta.

- **Atributos:**

  - `rol = "becario"`

  - `nivel\_cursado` *(Enum: `Primario`, `Secundario`, `Terciario`, `Universitario`)*

  - `datos\_academicos` *(Composición directa de `DatosAcademicos`)*

- **Relaciones:**

  - `puntero\_tutor` — referencia al `Tutor` asignado *(1:1)*

  - `puntero\_mediador` — referencia al `Mediador` asignado *(1:1)*

  - `puntero\_padrino` — referencia al `Padrino` asignado *(1:1)*

  - `lista\_tutorias` — colección de `Tutoria`

  - `lista\_envios\_cartas` — colección de `EnvioCarta`

- **Métodos:**

  - `visualizar\_datos\_academicos()` *(visualiza sus propios datos)*

  - `visualizar\_formulario\_academico()`

  - `llenar\_actualizar\_formulario\_academico()`

  - `ver\_calendario\_tutorias()`

  - `ver\_calendario\_envio()`

  - get\_datos\_contacto()

  - `contacto\_mediador()` *(invoca `puntero\_mediador.get\_datos\_contacto()`)*

  - `contacto\_tutor()` *(invoca `puntero\_tutor.get\_datos\_contacto()`)*


### 1.3 Subclase Abstracta: `Referente`

Agrupa el comportamiento y el estado común a `Tutor` y `Mediador`.

> **Nota de diseño:** Ambas subclases comparten el atributo `lista\_becarios` y el comportamiento de `listar\_becarios\_asignados()`, que son idénticos. `seleccionar\_becario()` se declara abstracto porque cada subclase recupera datos distintos de la base: el `Tutor` carga el calendario de tutorías y el contacto del mediador; el `Mediador` carga el calendario de envíos, el padrino y el contacto del tutor. La firma es la misma; la implementación no.

- **Atributos:**

  - `lista\_becarios` — colección de referencias a los `Becario` a cargo

- **Métodos:**

  - `listar\_becarios\_asignados()` *(comportamiento compartido; implementado en esta clase)*

  - `seleccionar\_becario()` *(abstracto; implementación en cada subclase)*

  - `visualizar\_datos\_academicos()` *(abstracto; heredado de `Usuario`)*


### 1.4 Subclase: `Tutor`

- **Atributos:**

  - `rol = "tutor"`

- **Métodos:**

  - `seleccionar\_becario()` *(carga: datos del becario + calendario tutorias + contacto mediador)*

  - `visualizar\_datos\_academicos()` *(visualiza datos del becario seleccionado)*

  - `auditar\_datos\_academicos\_becario()` *(delega la transición de estado a `DatosAcademicos.actualizar\_estado()`)*

  - `visualizar\_calendario\_tutoria()`

  - `crear\_tutoria()`

  - `actualizar\_tutoria()`

  - `eliminar\_tutoria()` *(cambia el estado de la `Tutoria` a `Cancelada`; no elimina el registro)*

  - `contactar\_mediador\_becario()` *(navega `becario\_seleccionado.puntero\_mediador.get\_datos\_contacto()`)*

  - `get\_datos\_contacto()` *(retorna `\{email, telefono\}`; invocado por `Becario` y `Mediador`)*


### 1.5 Subclase: `Mediador`

- **Atributos:**

  - `rol = "mediador"`

- **Métodos:**

  - `seleccionar\_becario()` *(carga: datos del becario + calendario envíos + padrino + contacto tutor)*

  - `visualizar\_datos\_academicos()` *(visualiza datos del becario seleccionado)*

  - `ver\_calendario\_envio\_cartas()` *(siempre en contexto del becario seleccionado)*

  - `crear\_envio\_carta()`

  - `actualizar\_envio\_carta()`

  - `contactar\_tutor\_becario()` *(navega `becario\_seleccionado.puntero\_tutor.get\_datos\_contacto()`)*

  - `get\_datos\_contacto()` *(retorna `\{email, telefono\}`; invocado por `Becario` y `Tutor`)*


### 1.6 Entidad de Dominio: `Padrino`

Sin acceso al sistema. Es una entidad de referencia pura utilizada como destinatario en el flujo de envío de cartas.

- **Atributos:**

  - `id\_padrino`

  - `nombre`

  - `apellido`

  - `email`

  - `telefono`

  - `direccion`


### 1.7 Entidad de Dominio: `DatosAcademicos`

Instancia de composición directa dentro de `Becario`. No existe de forma independiente.

- **Atributos:**

  - `nombre\_carrera` *(obligatorio)*

  - `anio\_ingreso` *(obligatorio)*

  - `anio\_en\_curso` *(obligatorio)*

  - `materias\_a\_cursar` *(lista; obligatorio)*

  - `materias\_adeudadas` *(lista; puede estar vacía)*

  - `lista\_documentos` *(colección de `DocumentoAcademico`; no restrictivo)*

  - `estado\_verificacion` *(Enum: `Vacio`, `Incompleto`, `Pendiente\_Revision`, `Pendiente\_Modificar`, `Aprobado`)*

- **Métodos:**

  - `actualizar\_estado(nuevo\_estado)` *(valida la transición antes de actualizar)*

  - `validar\_completitud()` *(determina si el estado corresponde a `Incompleto` o `Pendiente\_Revision`)*

  - `actualizar\_datos()` *(valida que `estado\_verificacion` ≠ `Aprobado` antes de permitir modificación)*


### 1.8 Entidad de Dominio: `DocumentoAcademico`

Representa un archivo PDF adjunto a los datos académicos de un becario.

- **Atributos:**

  - `tipo\_documento` *(ej.: Inscripción, Carta de compromiso, Programa)*

  - `ruta\_archivo`

  - `fecha\_carga`


### 1.9 Entidad de Dominio: `Tutoria`

Navegación exclusiva a través de `Becario.lista\_tutorias`. No contiene referencias de retorno.

- **Atributos:**

  - `id\_tutoria`

  - `fecha\_hora`

  - `estado` *(Enum: `Programada` (default), `Realizada`, `Ausente`, `Cancelada`)*

- **Métodos:**

  - `cambiar\_estado(nuevo\_estado)`

  - `reprogramar(nueva\_fecha\_hora)`


### 1.10 Entidad de Dominio: `EnvioCarta`

Navegación exclusiva a través de `Becario.lista\_envios\_cartas`. No contiene referencias de retorno.

- **Atributos:**

  - `id\_envio`

  - `fecha\_envio`

  - `estado` *(Enum: `Programada` (default), `Reprogramada`, `Cancelada`, `Enviada`)*

> - El estado `Enviada` es asignado por un actor externo al sistema. Mecanismo de integración: alcance futuro.

- **Métodos:**

  - `actualizar\_estado\_envio(nuevo\_estado)`

  - `actualizar\_fecha\_envio(nueva\_fecha)`


## 2. Casos de Uso

### Actores del sistema

- **Becario**

- **Tutor**

- **Mediador**


### CU-01: Ver Calendarios

**Actor:** Becario

**Precondiciones:**

- Becario autenticado.

- Padrino asociado *(para calendario de envíos)*.

- Tutor asociado *(para calendario de tutorías)*.

**Flujo principal:**

1. El becario selecciona entre calendario de envío de cartas o calendario de tutorías.

2. El sistema recupera los datos correspondientes por `id\_becario`.

3. El sistema envía la información a la interfaz gráfica.

**Flujos alternativos:**

- Calendario vacío → mensaje "Sin envíos programados" o "Sin tutorías programadas".

- Sin tutor asignado → mensaje "No posees tutor asignado".

- Sin padrino asignado → mensaje "No posees padrino asignado".

**Postcondición:** Visualización del calendario seleccionado o mensaje informativo.


### CU-02: Contactar

**Actores:** Becario, Tutor, Mediador

**Precondiciones según actor:**

- `Becario`: autenticado, con tutor y/o mediador asignado.

- `Mediador`: autenticado, con becario seleccionado y tutor asignado a ese becario.

- `Tutor`: autenticado, con becario seleccionado y mediador asignado a ese becario.

**Flujos por actor:**

*Becario contacta a Tutor o Mediador:*

1. El becario selecciona a quién contactar.

2. El sistema invoca `puntero\_tutor.get\_datos\_contacto()` o `puntero\_mediador.get\_datos\_contacto()`.

3. Se presenta el enlace directo de contacto (wa.me / tel:).

*Mediador contacta al becario seleccionado o tutor del becario:*

1. Desde la vista del becario, el mediador selecciona “Contactar becario” o "Contactar Tutor".

2. El sistema navega `becario\_seleccionado.puntero\_tutor.get\_datos\_contacto() o becario\_seleccionado.get\_datos\_contacto`.

3. Se presenta el enlace directo.

*Tutor contacta al Mediador del becario seleccionado:*

1. Desde la vista del becario, el tutor selecciona “Contactar becario” o "Contactar Mediador".

2. El sistema navega `becario\_seleccionado.puntero\_mediador.get\_datos\_contacto() o becario\_seleccionado.get\_datos\_contacto.`.

3. Se presenta el enlace directo.

**Flujos alternativos:**

- Sin tutor/mediador asignado → mensaje "No posee tutor asignado" / "No posee mediador asignado".

- Sin número de contacto registrado → mensaje "Sin número de teléfono asociado".

**Postcondición:** Apertura de enlace de contacto directo.


### CU-03: Llenar / Actualizar Formulario Académico

**Actor:** Becario

**Precondiciones:**

- Becario autenticado.

- `estado\_verificacion` de sus `DatosAcademicos` ≠ `Aprobado`.

**Flujo principal:**

1. El becario solicita el formulario.

2. El sistema recupera los datos académicos actuales y los envía a la interfaz.

3. El becario completa o actualiza los campos.

4. El becario finaliza el llenado.

5. El sistema valida los datos ingresados.

6. El sistema asigna estado `Pendiente\_Revision` y persiste.

**Flujos alternativos:**

- Datos inválidos (tipado incorrecto) → mensaje en los campos correspondientes; el becario corrige.

- Campos obligatorios incompletos → bloqueo del envío; mensaje en el campo faltante.

- Campos no obligatorios incompletos → el sistema asigna estado `Incompleto` y persiste.

- Datos ya aprobados → mensaje "Los datos académicos han sido aprobados y no pueden modificarse".

**Postcondición:** Datos persistidos con el estado correspondiente.


### CU-04: Visualizar Datos Académicos

**Actores:** Becario, Tutor, Mediador

**Precondiciones:**

- `Becario`: autenticado; haber llenado datos con anterioridad.

- `Tutor` / `Mediador`: autenticado; becario seleccionado.

**Flujo principal:**

1. El actor solicita la visualización de datos académicos.

2. El sistema recupera `DatosAcademicos` por `id\_becario`.

3. El sistema envía la información a la interfaz.

**Comportamiento según estado y rol:**

| Estado | Becario | Tutor | Mediador |
| - | - | - | - |
| `Vacio` | Mensaje "debes llenar el formulario" | Mensaje "el becario no ha cargado datos" | Igual que Tutor |
| `Incompleto` | Visualiza datos con campos faltantes remarcados | Visualiza con campos faltantes remarcados | Visualiza |
| `Pendiente\_Revision` | Visualiza con estado | Visualiza + opciones **Aprobar** / **Rechazar** | Visualiza con estado |
| `Pendiente\_Modificar` | Visualiza datos + observaciones del Tutor | Visualiza datos + observaciones | Visualiza |
| `Aprobado` | Visualiza con estado | Visualiza | Visualiza |


**Postcondición:** Visualización de datos académicos con las opciones disponibles según rol y estado.


### CU-05: Listar Becarios

**Actores:** Tutor, Mediador

**Precondición:** Actor autenticado.

**Flujo principal:**

1. El actor solicita su lista de becarios.

2. El sistema recupera `lista\_becarios` del actor y la envía a la interfaz.

**Flujo alternativo:**

- Lista vacía → mensaje "Sin becarios asociados".

**Postcondición:** Listado de becarios asignados al actor.


### CU-06: Seleccionar Becario — Tutor

**Actor:** Tutor

**Precondición:** Haber ejecutado CU-05 (Listar Becarios).

**Flujo principal:**

1. El tutor selecciona un becario de la lista.

2. El sistema procesa la solicitud con el `id\_becario`.

3. El sistema recupera los datos y los envía a la interfaz.

**Flujo alternativo:**

- `id\_becario` no encontrado → mensaje "El becario no se encuentra registrado, contactar al sistema fonbec".

- Dato sin asignar → etiqueta "Sin datos asignados" en el campo correspondiente.

**Postcondición:** Visualización del perfil del becario con los siguientes datos y accesos:

| Dato / Acceso |
| - |
| `id\_usuario`, `nombre`, `apellido` |
| `edad`, `sexo`, `direccion`, `nivel\_cursado` |
| `estado\_datos\_academicos` + opción Ver datos académicos |
| Fecha de tutoría más cercana + opción Ver calendario de tutorías |
| `email`, `telefono` del becario + opción Contactar |
| Mediador asignado: `nombre`, `email`, `telefono` + opción Contactar Mediador |



### CU-07: Seleccionar Becario — Mediador

**Actor:** Mediador

**Precondición:** Haber ejecutado CU-05 (Listar Becarios).

**Flujo principal:**

1. El mediador selecciona un becario de la lista.

2. El sistema procesa la solicitud con el `id\_becario`.

3. El sistema recupera los datos y los envía a la interfaz.

**Flujo alternativo:**

- `id\_becario` no encontrado → mensaje "El becario no se encuentra registrado, contactar al sistema fonbec".

- Dato sin asignar → etiqueta "Sin datos asignados" en el campo correspondiente.

**Postcondición:** Visualización del perfil del becario con los siguientes datos y accesos:

| Dato / Acceso |
| - |
| `id\_usuario`, `nombre`, `apellido` |
| `edad`, `sexo`, `direccion`, `nivel\_cursado` |
| `estado\_datos\_academicos` + opción Ver datos académicos |
| Padrino asociado + fecha de envío más cercana + opción Ver calendario de envíos |
| `email`, `telefono` del becario + opción Contactar |
| Tutor asignado: `nombre`, `email`, `telefono` + opción Contactar Tutor |



### CU-08: Auditar Datos Académicos *(función principal del Tutor)*

**Actor:** Tutor

**Precondiciones:**

- Becario seleccionado.

- Vista de datos académicos activa (CU-04).

- `estado\_verificacion` = `Pendiente\_Revision`.

**Flujo principal — Aprobación:**

1. El tutor verifica manualmente la información.

2. El tutor selecciona "Aprobar".

3. El sistema invoca `datos\_academicos.actualizar\_estado(Aprobado)`.

4. El sistema persiste el nuevo estado.

5. El sistema envía los datos al sistema externo Fonbec *(mecanismo de integración: alcance futuro)*.

**Flujo alternativo — Rechazo:**

1. El tutor selecciona "Rechazar".

2. El sistema habilita un campo para cargar observaciones.

3. El tutor ingresa las observaciones.

4. El sistema invoca `datos\_academicos.actualizar\_estado(Pendiente\_Modificar)`.

5. El sistema persiste el nuevo estado y las observaciones.

**Flujo alternativo — Datos insuficientes:**

- Estado `Incompleto` o `Vacio` → opciones Aprobar/Rechazar no disponibles → mensaje "Contactar al becario para completar los datos".

**Postcondición:** Estado de `DatosAcademicos` actualizado.


### CU-09: Visualizar Calendario de Tutorías

**Actores:** Tutor, Becario

**Precondiciones:**

- `Tutor`: becario seleccionado.

- `Becario`: autenticado.

**Flujo principal:**

1. El actor solicita el calendario de tutorías.

2. El sistema recupera la `lista\_tutorias` del becario por `id\_becario`.

3. El sistema envía la información a la interfaz.

**Flujo alternativo:**

- Calendario vacío → mensaje "No hay tutorías programadas".

**Postcondición:** Visualización del calendario de tutorías y opciones disponibles.


### CU-10: Crear Tutoría

**Actor:** Tutor

**Precondiciones:**

- Becario seleccionado.

- Calendario de tutorías visualizado (CU-09).

**Campo requerido:** `fecha\_hora`

**Flujo principal:**

1. El tutor selecciona "Crear Tutoría".

2. El tutor ingresa la `fecha\_hora`.

3. El sistema valida que la fecha no tenga una tutoría ya asignada.

4. Se confirman los datos.

**Flujos alternativos:**

- Fecha no disponible → mensaje "Fecha no disponible, seleccione otra".

- Becario no disponible → aviso informativo al tutor *(no restrictivo; no bloquea la creación)*.

**Postcondición:** Nuevo registro `Tutoria` creado con estado `Programada`.


### CU-11: Actualizar Tutoría

**Actor:** Tutor

**Precondiciones:**

- Becario seleccionado.

- Tutoría existente seleccionada del calendario.

**Flujo principal:**

1. El tutor selecciona "Actualizar Tutoría".

2. El tutor modifica la `fecha\_hora`.

3. El sistema valida los nuevos datos.

4. Se confirman y persisten los cambios.

**Postcondición:** Registro de `Tutoria` actualizado.


### CU-12: Eliminar Tutoría

**Actor:** Tutor

**Precondición:** Tutoría existente seleccionada del calendario.

**Flujo principal:**

1. El tutor selecciona "Eliminar Tutoría".

2. El sistema invoca `tutoria.cambiar\_estado(Cancelada)`.

3. El registro se preserva con estado `Cancelada`.

**Postcondición:** `Tutoria` con estado `Cancelada`. El historial no se altera.


### CU-13: Visualizar Calendario de Envío de Cartas

**Actores:** Mediador, Becario

**Precondiciones:**

- `Mediador`: becario seleccionado.

- `Becario`: autenticado.

**Flujo principal:**

1. El actor solicita el calendario de envíos del becario.

2. El sistema recupera la `lista\_envios\_cartas` del becario por `id\_becario`.

3. El sistema envía la información a la interfaz.

**Flujo alternativo:**

- Calendario vacío → mensaje "No hay envíos de cartas programados".

**Postcondición:** Visualización del calendario de envíos y opciones disponibles.


### CU-14: Asignar Fecha de Envío de Carta

**Actor:** Mediador

**Precondiciones:**

- Becario seleccionado.

- Calendario de envíos visualizado (CU-13).

- Padrino asociado al becario.

**Flujo principal:**

1. El mediador solicita la creación de un envío.

2. El sistema pre-carga el padrino desde `Becario.puntero\_padrino`.

3. El mediador ingresa la `fecha\_envio`.

4. El sistema valida los datos.

5. Se confirman y persisten.

**Flujo alternativo:**

- Datos inválidos → mensaje "Verificar la información cargada".

**Postcondición:** Nuevo registro `EnvioCarta` creado con estado `Programada`.

> **Nota de negocio:** El mediador fija la fecha y supervisa el proceso. La carta es redactada y enviada físicamente por el becario fuera del sistema.


### CU-15: Actualizar Envío de Carta

**Actor:** Mediador

**Precondiciones:**

- Becario seleccionado.

- Envío existente seleccionado del calendario.

- Padrino asociado al becario.

**Flujo principal:**

1. El mediador solicita la actualización del envío.

2. El mediador modifica la `fecha\_envio` y/o el estado (`Reprogramada`, `Cancelada`).

3. El sistema valida los datos.

4. Se confirman y persisten.

**Flujo alternativo:**

- Datos inválidos → mensaje "Verificar la información cargada".

**Postcondición:** Registro de `EnvioCarta` actualizado.


## 3. Identificación de Responsabilidades — Tarjetas CRC


**Clase: `Usuario`** *(abstracta)*

| Responsabilidades | Colaboradores |
| - | - |
| Gestionar sus propios datos personales | — |
| Autenticarse en el sistema | — |
| Visualizar datos académicos *(abstracto)* | — |



**Clase: `Becario`**

| Responsabilidades | Colaboradores |
| - | - |
| Conocer su tutor asignado | `Tutor` |
| Conocer su mediador asignado | `Mediador` |
| Conocer su padrino asignado | `Padrino` |
| Conocer y gestionar sus datos académicos | `DatosAcademicos` |
| Ver su calendario de tutorías | `Tutoria` |
| Ver su calendario de envíos de cartas | `EnvioCarta` |
| Visualizar sus propios datos académicos | `DatosAcademicos` |



**Clase: `Referente`** *(abstracta)*

| Responsabilidades | Colaboradores |
| - | - |
| Conocer la lista de becarios a su cargo | `Becario` |
| Listar los becarios asignados | `Becario` |
| Seleccionar un becario *(abstracto; delegado a cada subclase)* | `Becario` |



**Clase: `Tutor`**

| Responsabilidades | Colaboradores |
| - | - |
| Seleccionar un becario (cargar: calendario + mediador) | `Becario` |
| Visualizar datos académicos del becario seleccionado | `DatosAcademicos` |
| Delegar la aprobación/rechazo de datos académicos | `DatosAcademicos` |
| Gestionar tutorías (crear, actualizar, cancelar) | `Tutoria` |
| Exponer sus propios datos de contacto | — |
| Contactar al mediador del becario seleccionado | `Becario`, `Mediador` |



**Clase: `Mediador`**

| Responsabilidades | Colaboradores |
| - | - |
| Seleccionar un becario (cargar: calendario envíos + tutor + padrino) | `Becario` |
| Visualizar datos académicos del becario seleccionado | `DatosAcademicos` |
| Gestionar envíos de carta (crear, actualizar) | `EnvioCarta` |
| Exponer sus propios datos de contacto | — |
| Contactar al tutor del becario seleccionado | `Becario`, `Tutor` |



**Clase: `Padrino`**

| Responsabilidades | Colaboradores |
| - | - |
| Ser referencia de destinatario para envíos de cartas | — |
| Exponer sus datos de contacto para visualización | — |



**Clase: `DatosAcademicos`**

| Responsabilidades | Colaboradores |
| - | - |
| Almacenar y gestionar los datos curriculares del becario | — |
| Validar la completitud de los datos obligatorios | — |
| Gestionar las transiciones de `estado\_verificacion` | — |
| Rechazar modificaciones cuando `estado` = `Aprobado` | — |
| Gestionar los documentos académicos adjuntos | `DocumentoAcademico` |



**Clase: `DocumentoAcademico`**

| Responsabilidades | Colaboradores |
| - | - |
| Almacenar la referencia a un archivo PDF | — |
| Registrar el tipo de documento y la fecha de carga | — |



**Clase: `Tutoria`**

| Responsabilidades | Colaboradores |
| - | - |
| Cambiar su estado | — |
| Reprogramar su fecha y hora | — |



**Clase: `EnvioCarta`**

| Responsabilidades | Colaboradores |
| - | - |
| Actualizar su estado | — |
| Actualizar su fecha de envío | — |



## 4. Reglas de Negocio

| ID | Regla | Clase responsable |
| - | - | - |
| RN-01 | Un becario tiene exactamente un tutor, un mediador y un padrino asignados (relación 1:1 en los tres casos). | `Becario` |
| RN-02 | Un becario no puede modificar sus datos académicos si `estado\_verificacion` = `Aprobado`. | `DatosAcademicos` |
| RN-03 | No existe relación directa entre `Tutor` y `Mediador`. Toda navegación entre ellos pasa por `Becario`. | `Tutor`, `Mediador` |
| RN-04 | Eliminar una tutoría cambia su estado a `Cancelada`. El registro nunca se elimina físicamente. | `Tutoria` |
| RN-05 | Para crear un `EnvioCarta`, el becario debe tener un padrino asignado. | `Mediador`, `Becario` |
| RN-06 | Las opciones "Aprobar" y "Rechazar" en la auditoría solo están disponibles si `estado\_verificacion` = `Pendiente\_Revision`. | `DatosAcademicos` |
| RN-07 | Para ejecutar cualquier acción sobre un becario (más allá de listar), el referente debe haberlo seleccionado primero. | `Tutor`, `Mediador` |
| RN-08 | El estado `Enviada` en `EnvioCarta` es asignado por un actor externo al sistema. | `EnvioCarta` |



## 5. Alcance Futuro

Los siguientes puntos quedan fuera del alcance de esta iteración y serán abordados en etapas posteriores del proyecto:

- Sistema de autenticación (login / logout / restablecer contraseña).

- Rol Administrador: casos de uso de alta, baja y asignación de usuarios (tutor, mediador, padrino a becario).

- Integración con el sistema externo Fonbec (postcondición de la auditoría de datos académicos).

- Mecanismo de asignación del estado `Enviada` en `EnvioCarta` por actor externo.

- Sistema de notificaciones ante cambios de estado (datos académicos, disponibilidad de becario en tutorías).

- Diagrama formal de transición de estados para `DatosAcademicos`, `Tutoria` y `EnvioCarta`.

- Restricciones de acceso por rol en la capa de autorización.

- Ampliación de campos de `Tutoria` (modalidad, duración, etc.).

