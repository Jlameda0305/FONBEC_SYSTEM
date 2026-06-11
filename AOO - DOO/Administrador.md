# Análisis Orientado a Objetos — Actor Administrador

> **Anexo al documento principal:** `AOO_FONBEC.md`
> Este documento extiende el análisis orientado a objetos del sistema FONBEC con el actor `Administrador`, cuyo alcance funcional fue declarado fuera del MVP inicial y ahora se incorpora formalmente al modelo.

---

## 1. Descripción General del Actor

### Propósito
El `Administrador` es el actor de gestión central del sistema. Su existencia responde a una necesidad operativa crítica: ningún usuario del sistema debe poder registrarse de forma autónoma ni obtener acceso sin que un ser humano responsable haya validado previamente su identidad y su rol. El Administrador es el guardián de ese proceso.

### Responsabilidades Principales
- Gestionar el ciclo de vida de los usuarios del sistema: invitarlos, activarlos y, cuando corresponda, eliminarlos.
- Administrar las vinculaciones entre actores: asignar tutores, mediadores y padrinos a los becarios.
- Gestionar el registro de padrinos (entidad sin acceso al sistema).
- Supervisar el estado académico general de los becarios.
- Acceder a los datos de contacto de todos los actores del sistema.
- Mantener los listados globales de todos los actores registrados.

### Relación con otros Actores
- Es el único actor con poder de **crear** y **eliminar** vínculos entre `Becario`, `Tutor`, `Mediador` y `Padrino`.
- No participa en el flujo de auditoría académica: ese proceso pertenece exclusivamente al `Tutor`.
- No interactúa de forma directa con `DatosAcademicos` más allá de su visualización en estado `Aprobado`.
- Es el único actor con visibilidad global sobre todos los listados del sistema (becarios, tutores, mediadores, padrinos).

### Alcance Funcional
El `Administrador` opera sobre la estructura del sistema: decide quién puede entrar y cómo están relacionados entre sí los distintos actores. No opera sobre el contenido académico ni sobre los flujos de tutorías o envíos de cartas, que son responsabilidad de `Tutor` y `Mediador` respectivamente.

---

## 2. Atributos

El `Administrador` hereda todos los atributos de `Usuario` y no requiere atributos adicionales en esta iteración, dado que su diferenciación respecto de los demás actores se expresa exclusivamente en su `rol` y en los casos de uso que tiene habilitados.

| Atributo | Tipo | Descripción | Restricciones |
|---|---|---|---|
| `id_usuario` | `str` | Identificador único del administrador en el sistema | Inmutable. Asignado por Supabase Auth |
| `nombre` | `str` | Nombre de pila | No nulo |
| `apellido` | `str` | Apellido | No nulo |
| `email` | `str` | Dirección de correo electrónico | Único en el sistema. Usado para autenticación |
| `telefono` | `str` | Número de contacto | No nulo |
| `edad` | `int` | Edad del administrador | Valor positivo |
| `sexo` | `str` | Sexo del administrador | No nulo |
| `direccion` | `str` | Dirección física | No nulo |
| `password_hash` | `str` | Hash de la contraseña gestionada por Supabase Auth | Nunca almacenado en texto plano |
| `rol` | `str` | Identificador de rol del actor | Valor fijo: `"administrador"` |

---

## 3. Métodos

### 3.1 Gestión de Usuarios

**`invitar_usuario(email, rol)`**
- **Responsabilidad:** Generar y enviar un enlace de invitación seguro para que un candidato cree su cuenta con un rol predefinido.
- **Parámetros:** `email: str`, `rol: str` (valores válidos: `"becario"`, `"tutor"`, `"mediador", padrino`)
- **Resultado esperado:** El sistema (a través de Supabase Auth) envía un correo al destinatario con un token de acceso único. El destinatario solo puede establecer su contraseña y datos basicos; el rol ya está determinado.
- **Reglas de negocio:** El `rol` debe ser uno de los valores válidos del sistema. El Administrador no puede invitar a otro Administrador desde la interfaz general.

**`eliminar_usuario(id_usuario)`**
- **Responsabilidad:** Revocar el acceso de un usuario al sistema.
- **Parámetros:** `id_usuario: str`
- **Resultado esperado:** El usuario queda desactivado. Sus datos históricos se preservan para mantener la trazabilidad del sistema.
- **Reglas de negocio:** Antes de eliminar a un `Tutor`, `Mediador`, `becario`, `padrino`, el sistema debe verificar que las relaciones sean reasignados o eliminadas, de manera tal que los punteros esten en none.

### 3.2 Gestión de Vinculaciones

**`asignar_tutor(id_becario, id_tutor)`**
- **Responsabilidad:** Establecer la referencia `puntero_tutor` en el agregado `Becario`.
- **Parámetros:** `id_becario: str`, `id_tutor: str`
- **Resultado esperado:** El `Becario` queda vinculado al `Tutor` y aparece en la `lista_becarios` de ese `Tutor`.
- **Reglas de negocio:** Un becario solo puede tener un tutor asignado a la vez (relación 1:1 — RN-01). La asignación reemplaza la anterior si ya existía una.

**`desasignar_tutor(id_becario)`**
- **Responsabilidad:** Remover la referencia `puntero_tutor` del `Becario`.
- **Parámetros:** `id_becario: str`
- **Resultado esperado:** `puntero_tutor` queda en `None`. El `Becario` es removido de la `lista_becarios` del tutor previo.

**`asignar_mediador(id_becario, id_mediador)`**
- **Responsabilidad:** Establecer la referencia `puntero_mediador` en el agregado `Becario`.
- **Parámetros:** `id_becario: str`, `id_mediador: str`
- **Resultado esperado:** El `Becario` queda vinculado al `Mediador` y aparece en la `lista_becarios` de ese `Mediador`.
- **Reglas de negocio:** Relación 1:1 (RN-01). La asignación reemplaza la anterior si ya existía una.

**`desasignar_mediador(id_becario)`**
- **Responsabilidad:** Remover la referencia `puntero_mediador` del `Becario`.
- **Parámetros:** `id_becario: str`
- **Resultado esperado:** `puntero_mediador` queda en `None`.

**`asignar_padrino(id_becario, id_padrino)`**
- **Responsabilidad:** Establecer la referencia `puntero_padrino` en el agregado `Becario`.
- **Parámetros:** `id_becario: str`, `id_padrino: str`
- **Resultado esperado:** El `Becario` queda vinculado al `Padrino`.
- **Reglas de negocio:** Relación 1:1 (RN-01). La asignación reemplaza la anterior si ya existía una.

**`desasignar_padrino(id_becario)`**
- **Responsabilidad:** Remover la referencia `puntero_padrino` del `Becario`.
- **Parámetros:** `id_becario: str`
- **Resultado esperado:** `puntero_padrino` queda en `None`.

### 3.3 Gestión de Padrinos (ABM)

**`crear_padrino(datos)`**
- **Responsabilidad:** Registrar un nuevo `Padrino` en el sistema.
- **Parámetros:** `datos: dict` con `nombre`, `apellido`, `email`, `telefono`, `direccion`
- **Resultado esperado:** Nueva instancia de `Padrino` persistida en el sistema.
- **Reglas de negocio:** El `Padrino` no recibe invitación ni tiene acceso al sistema. Su registro es una operación exclusiva del Administrador.

**`actualizar_padrino(id_padrino, datos)`**
- **Responsabilidad:** Modificar los datos de un `Padrino` existente.
- **Parámetros:** `id_padrino: str`, `datos: dict`
- **Resultado esperado:** Datos del `Padrino` actualizados y persistidos.

**`eliminar_padrino(id_padrino)`**
- **Responsabilidad:** Eliminar el registro de un `Padrino`.
- **Parámetros:** `id_padrino: str`
- **Resultado esperado:** El `Padrino` es eliminado del sistema.
- **Reglas de negocio:** Si el `Padrino` está asignado a uno o más becarios, el sistema debe advertir al Administrador y requerir confirmación explícita antes de proceder.

### 3.4 Supervisión y Consulta

**`listar_becarios()`**
- **Responsabilidad:** Recuperar la lista completa de todos los becarios registrados en el sistema.
- **Resultado esperado:** Colección global de `Becario` con datos de identificación y estado académico.

**`listar_tutores()`**
- **Responsabilidad:** Recuperar la lista completa de todos los tutores registrados.
- **Resultado esperado:** Colección global de `Tutor`.

**`listar_mediadores()`**
- **Responsabilidad:** Recuperar la lista completa de todos los mediadores registrados.
- **Resultado esperado:** Colección global de `Mediador`.

**`listar_padrinos()`**
- **Responsabilidad:** Recuperar la lista completa de todos los padrinos registrados.
- **Resultado esperado:** Colección global de `Padrino`.

**`visualizar_datos_academicos(becario)`**
- **Responsabilidad:** Visualizar la información académica de un becario seleccionado. Solo disponible cuando el estado es `Aprobado`.
- **Parámetros:** `becario: Becario`
- **Resultado esperado:** Datos académicos del becario incluyendo documentos adjuntos aprobados.
- **Reglas de negocio:** El Administrador no tiene acceso a datos en estados intermedios (`Incompleto`, `Pendiente_Revision`, `Pendiente_Modificar`). La auditoría es responsabilidad exclusiva del `Tutor`.

**`get_datos_contacto(actor)`**
- **Responsabilidad:** Acceder a los datos de contacto de cualquier actor del sistema.
- **Parámetros:** `actor` — instancia de `Becario`, `Tutor`, `Mediador` o `Padrino`
- **Resultado esperado:** Diccionario con `{email, telefono}` del actor consultado.

---

## 4. Casos de Uso

### CU-ADM-01: Invitar Usuario

**Actor:** Administrador

**Precondiciones:**
- Administrador autenticado.
- El candidato no posee una cuenta activa en el sistema.

**Flujo principal:**
1. El Administrador selecciona "Invitar usuario".
2. Ingresa el `email` del candidato y selecciona su `rol`.
3. El sistema valida que el email no esté ya registrado.
4. El sistema genera un enlace de invitación con el rol preconfigurado (via Supabase Auth `invite_user_by_email`).
5. El candidato recibe el correo y establece su contraseña mediante el enlace.
6. La cuenta queda activa con el rol asignado.

**Flujos alternativos:**
- Email ya registrado → mensaje "Este correo ya tiene una cuenta activa en el sistema".
- Rol inválido → el sistema no permite la acción (control de formulario).

**Postcondición:** Nueva cuenta creada con rol predefinido. El usuario puede autenticarse con sus credenciales.

---

### CU-ADM-02: Eliminar Usuario

**Actor:** Administrador

**Precondiciones:**
- Administrador autenticado.
- El usuario a eliminar existe en el sistema.

**Flujo principal:**
1. El Administrador selecciona al usuario desde el listado correspondiente.
2. Selecciona "Eliminar usuario".
3. El sistema verifica si el usuario tiene vinculaciones activas.
4. El sistema solicita confirmación explícita.
5. El Administrador confirma.
6. El acceso del usuario queda revocado. Los datos históricos se preservan.

**Flujo alternativo:**
- El usuario tiene actores vinculados → mensaje de advertencia indicando los actores afectados, lo cual implica reasignacion o eliminacion de los punteros afectados.

**Postcondición:** Usuario sin acceso al sistema. Registros históricos preservados.

---

### CU-ADM-03: Gestionar Vinculaciones de Becario

**Actor:** Administrador

**Precondiciones:**
- Administrador autenticado.
- El becario existe en el sistema.

**Flujo principal (Asignación):**
1. El Administrador selecciona un `Becario` del listado.
2. Accede a la sección de vinculaciones del perfil del becario.
3. Selecciona el actor a asignar (Tutor, Mediador o Padrino) desde una lista desplegable con los registros disponibles.
4. Confirma la asignación.
5. El sistema actualiza el puntero correspondiente en el agregado `Becario` y lo persiste.

**Flujo principal (Desasignación):**
1. El Administrador selecciona un `Becario` del listado.
2. Accede a la sección de vinculaciones.
3. Selecciona "Remover" sobre la vinculación existente (Tutor, Mediador o Padrino).
4. Confirma la operación.
5. El puntero correspondiente queda en `None`.

**Flujos alternativos:**
- No hay tutores/mediadores/padrinos disponibles en el sistema → mensaje informativo; se sugiere invitar primero al candidato.

**Postcondición:** Vinculación del `Becario` actualizada y persistida.

---

### CU-ADM-04: Gestionar Padrinos (ABM)

**Actor:** Administrador

**Precondiciones:**
- Administrador autenticado.

**Flujo Crear:**
1. El Administrador selecciona "Nuevo Padrino".
2. Completa los datos: `nombre`, `apellido`, `email`, `telefono`, `direccion`.
3. Confirma.
4. El sistema persiste el nuevo `Padrino`.

**Flujo Actualizar:**
1. El Administrador selecciona un `Padrino` del listado.
2. Modifica los campos necesarios.
3. Confirma. El sistema persiste los cambios.

**Flujo Eliminar:**
1. El Administrador selecciona un `Padrino` del listado y elige "Eliminar".
2. Si el `Padrino` tiene becarios asignados, el sistema advierte con una lista de los becarios afectados.
3. El Administrador confirma explícitamente.
4. El sistema elimina el registro y desvincula el `puntero_padrino` en los becarios afectados.

**Postcondición:** Registro de `Padrino` creado, actualizado o eliminado.

---

### CU-ADM-05: Listar Actores del Sistema

**Actor:** Administrador

**Precondición:** Administrador autenticado.

**Flujo principal:**
1. El Administrador accede al panel de administración.
2. Selecciona el listado que desea visualizar: Becarios, Tutores, Mediadores o Padrinos.
3. El sistema recupera la colección global correspondiente y la presenta en la interfaz.

**Flujo alternativo:**
- Lista vacía → mensaje "No hay [actores] registrados en el sistema".

**Postcondición:** Listado del tipo de actor seleccionado presentado en pantalla.

---

### CU-ADM-06: Visualizar Datos Académicos Aprobados

**Actor:** Administrador

**Precondiciones:**
- Administrador autenticado.
- Becario seleccionado desde el listado.
- `estado_verificacion` del becario seleccionado = `Aprobado`.

**Flujo principal:**
1. El Administrador selecciona un `Becario` desde el listado.
2. Accede a la sección de datos académicos del becario.
3. El sistema verifica el estado de los datos académicos.
4. El sistema presenta los datos académicos aprobados, incluyendo los documentos adjuntos.

**Flujo alternativo:**
- Estado diferente de `Aprobado` → el sistema no muestra el contenido detallado; presenta únicamente el estado actual del registro (ej. "Pendiente de revisión por el Tutor").

**Postcondición:** Visualización de datos académicos aprobados, o mensaje informativo sobre el estado actual.

---

### CU-ADM-07: Contactar Actores del Sistema

**Actor:** Administrador

**Precondición:** Administrador autenticado.

**Flujo principal:**
1. El Administrador accede al perfil del actor que desea contactar (Becario, Tutor, Mediador o Padrino).
2. El sistema presenta los datos de contacto disponibles: `email` y `telefono`.
3. El sistema ofrece los enlaces de contacto directo (wa.me / tel: / mailto:).

**Flujo alternativo:**
- Sin datos de contacto registrados → campo correspondiente marcado como "Sin información".

**Postcondición:** Acceso a los datos de contacto del actor seleccionado.

---

## 5. Tarjetas CRC

**Clase: `Administrador`**

| Responsabilidades | Colaboradores |
|---|---|
| Invitar nuevos usuarios al sistema con rol predefinido | Sistema de Invitaciones (Supabase Auth) |
| Eliminar el acceso de usuarios existentes | `Becario`, `Tutor`, `Mediador` |
| Asignar y desasignar tutores a becarios | `Becario`, `Tutor` |
| Asignar y desasignar mediadores a becarios | `Becario`, `Mediador` |
| Asignar y desasignar padrinos a becarios | `Becario`, `Padrino` |
| Crear, actualizar y eliminar registros de padrinos | `Padrino` |
| Listar todos los becarios del sistema | `Becario` |
| Listar todos los tutores del sistema | `Tutor` |
| Listar todos los mediadores del sistema | `Mediador` |
| Listar todos los padrinos del sistema | `Padrino` |
| Visualizar datos académicos en estado Aprobado | `Becario`, `DatosAcademicos`, `DocumentoAcademico` |
| Acceder a datos de contacto de cualquier actor | `Becario`, `Tutor`, `Mediador`, `Padrino` |
| Autenticarse en el sistema | — |

---

## 6. Reglas de Negocio

| ID | Regla | Clase responsable |
|---|---|---|
| RN-ADM-01 | El Administrador es el único actor autorizado para generar invitaciones. Ningún usuario puede registrarse de forma autónoma. | `Administrador` |
| RN-ADM-02 | Las invitaciones deben tener el rol del usuario determinado en el momento de la generación. El destinatario solo puede establecer su contraseña. | `Administrador`, Sistema de Invitaciones |
| RN-ADM-03 | El Administrador puede crear, modificar y eliminar vinculaciones entre `Becario` y los actores `Tutor`, `Mediador` y `Padrino`. | `Administrador`, `Becario` |
| RN-ADM-04 | Las vinculaciones son de tipo 1:1 para cada relación (un becario tiene como máximo un tutor, un mediador y un padrino). Una nueva asignación reemplaza la anterior. Extiende RN-01. | `Administrador`, `Becario` |
| RN-ADM-05 | Antes de eliminar un `Tutor`, `Mediador` o `Padrino` que tenga becarios asignados, el sistema DEBE advertir al Administrador con la lista de becarios afectados y requerir confirmación explícita. | `Administrador` |
| RN-ADM-06 | El Administrador ÚNICAMENTE visualiza datos académicos cuando el `estado_verificacion` es `Aprobado`. El acceso a estados intermedios del proceso de auditoría está reservado al `Tutor`. | `Administrador`, `DatosAcademicos` |
| RN-ADM-07 | El Administrador no participa en el proceso de auditoría académica (CU-08). La aprobación y el rechazo de datos académicos son responsabilidad exclusiva del `Tutor`. | `Administrador`, `Tutor` |
| RN-ADM-08 | El `Padrino` no tiene acceso al sistema. Su registro es gestionado íntegramente por el Administrador mediante el ABM de padrinos. | `Administrador`, `Padrino` |
| RN-ADM-09 | El Administrador puede acceder a los datos de contacto de todos los actores del sistema (`Becario`, `Tutor`, `Mediador`, `Padrino`). | `Administrador` |

---

## 7. Modelo Conceptual

### Posición dentro del Dominio

El `Administrador` es el actor de mayor jerarquía operativa del sistema en términos de control de acceso y estructura de datos. Sin embargo, su ámbito de acción es **transversal y estructural**, no funcional: no produce contenido académico, no realiza tutorías y no gestiona envíos de cartas. Su poder reside en definir quién puede hacer qué y cómo están relacionados entre sí los actores del dominio.

### Relaciones con las Demás Entidades

```
Administrador
│
├── Invita (Supabase Auth)
│     ├── Becario
│     ├── Tutor
│     └── Mediador
│
├── Vincula a través de
│     └── Becario (Aggregate Root)
│           ├── puntero_tutor ──────────► Tutor
│           ├── puntero_mediador ───────► Mediador
│           └── puntero_padrino ────────► Padrino
│
├── Gestiona directamente (ABM)
│     └── Padrino
│
├── Supervisa (solo lectura, solo estado Aprobado)
│     └── DatosAcademicos
│           └── DocumentoAcademico
│
└── Accede a datos de contacto
      ├── Becario.get_datos_contacto()
      ├── Tutor.get_datos_contacto()
      ├── Mediador.get_datos_contacto()
      └── Padrino (email, telefono)
```

### Dependencias Principales

- **Supabase Auth:** Para la generación de invitaciones. Esta es la única dependencia de infraestructura que el rol implica a nivel de dominio. La invitación es el mecanismo de entrada al sistema.
- **`Becario` como Aggregate Root:** Toda vinculación entre actores (tutor, mediador, padrino) se materializa a través de los punteros del agregado `Becario`. El Administrador no crea relaciones directas entre actores; siempre navega a través del `Becario`.
- **`DatosAcademicos`:** Entidad de solo lectura para el Administrador, y únicamente en estado `Aprobado`. La cadena de responsabilidad de auditoría (`Tutor`) permanece intacta.

### Nota de Diseño — Jerarquía de Herencia

El `Administrador` hereda de `Usuario` directamente, sin pasar por `Referente`. Esta decisión es intencional: `Referente` define el patrón de trabajo con `lista_becarios` para los actores que supervisan un subconjunto de becarios asignados. El `Administrador`, en cambio, tiene visibilidad sobre **todos** los actores del sistema y no opera sobre un subconjunto predefinido. La jerarquía actualizada del sistema queda:

```
Usuario (abstracta)
├── Becario                    ← Aggregate Root del modelo
├── Administrador              ← Actor de gestión global
└── Referente (abstracta)
    ├── Tutor
    └── Mediador
```
