# Roadmap y Alcance Detallado - MVP Sistema FONBEC

Este documento define con alta precisión el alcance, los plazos estimados y el desglose de tareas técnicas requeridas para el lanzamiento del Producto Mínimo Viable (MVP). Todo requerimiento fuera de este documento queda oficialmente diferido para versiones 2.0+.

## Resumen Ejecutivo del Estado del Proyecto
- **Progreso Estimado:** 60% del total del MVP.
- **Tiempo Restante Estimado:** 1 a 2 semanas de desarrollo continuo.
- **Hito Actual:** Transición a la Fase 3 (Módulo de Administración).

---

## 🟢 FASE 1: Área del Becario
**Estado:** `COMPLETADA` ✅  
**Duración Total:** Finalizada.

Esta fase construyó la base transaccional de los documentos y estados, proveyendo al becario autonomía para iniciar su auditoría académica.

### Desglose de Casos de Uso (Implementados)
1. **CU04 - Visualizar Datos Académicos:** Renderizado del perfil académico y el estado actual de la verificación (`INCOMPLETO`, `PENDIENTE_REVISION`, `APROBADO`, `RECHAZADO`).
2. **CU03 - Llenar y Actualizar Formulario:** Carga de datos de la carrera y subida concurrente de los tres archivos PDF obligatorios (Programa, Carta Compromiso, Inscripción) sincronizados con Supabase Storage.
3. **CU03 - Eliminar Documento:** Remoción de un PDF específico mediante validación de estado en el agregado.
4. **CU02 - Contactar Referentes:** Exposición de los datos de Tutor, Mediador y Padrino en el Dashboard, habilitando la generación dinámica de enlaces de WhatsApp.

---

## 🟢 FASE 2: Área del Tutor
**Estado:** `COMPLETADA` ✅  
**Duración Total:** Finalizada.

Fase dedicada a la interacción activa del tutor, permitiendo el control y la toma de decisiones sobre la documentación entregada por los becarios. Nos encontramos en fase de verificación y testeo final.

### Desglose de Casos de Uso (Implementados)
1. **Visualizar Becarios Asignados:**
   - **Backend:** Creación de `ListarBecariosTutorUseCase`.
   - **Frontend:** Construcción del Dashboard del Tutor (UI) listando los becarios asociados a su ID de usuario de manera visual.
2. **Contactar Becario:**
   - **Frontend:** Tarjetas de perfiles en el dashboard y vista en detalle exponiendo botón dinámico para contactar a los becarios.
3. **Auditar Datos Académicos [CRÍTICO]:**
   - **Backend:** Implementación de `AuditarDatosAcademicosUseCase`, validando estrictamente las transiciones del estado de `PENDIENTE_REVISION` a `APROBADO` o `PENDIENTE_MODIFICAR`.
   - **Lógica de Negocio:** Habilitación estricta de rechazos forzando la inyección de observaciones y sincronizando con SQLAlchemy y Supabase.
   - **Frontend:** Interfaz de auditoría renderizada desde partials compartidos, condicional a estados, previsualización de información y botones de acción reactivos.

---

## 🔴 FASE 3: Módulo de Administración (Backoffice)
**Estado:** `EN ESPERA` ⏸️  
**Duración Estimada:** 1 Semanas (4 a 6 días hábiles). 
**SE TERMINARA DE IMPLEMENTAR EN SU TOTALIDAD POSTERIOR A UNA SEGUNDA REUNION CON FONBEC**

Construcción desde cero del motor de gestión del sistema. Reemplazará la actual carga manual (SQL directo/Temp Seeds) por un panel gráfico administrativo.

### Desglose de Casos de Uso a Implementar
1. **Modelado y Arquitectura Inicial (1 día):**
   - Crear entidad `Administrador` en la capa de Dominio e Infraestructura (SQLAlchemy).
2. **CRUD Base de Usuarios (2 días):**
   - **Backend:** `CrearUsuarioUseCase`, `ListarUsuariosUseCase`, `ActualizarUsuarioUseCase`.
   - **Frontend:** Tablas de administración (Datatables) con filtros básicos.
3. **Gestión de Roles (1 días):**
   - **Backend:** `AsignarRolUsuarioUseCase`. Capacidad de convertir a un usuario base en Becario, Tutor, Mediador o Padrino, instanciando los modelos de dominio correspondientes.
4. **Gestión de Relaciones y Punteros (1 días) [CRÍTICO]:**
   - **Backend:** `VincularBecarioReferenteUseCase`. Reglas de negocio para inyectar/eliminar relaciones en los agregados (ej. Asignar el Tutor ID 4 al Becario ID 10).
   - **Frontend:** Formularios tipo select/dropdown para asignar tutores/mediadores/padrinos a los becarios desde un panel central.

---

## 🔴 FASE 4: Autenticación y Seguridad
**Estado:** `EN ESPERA` ⏸️  
**Duración Estimada:** 1 Semana (5 días hábiles).

Se remueve la seguridad simulada y se implementa seguridad oficial de producción aislando totalmente las rutas.

### Desglose de Tareas Técnicas
1. **Integración Supabase Auth (2 días):**
   - Instalación del SDK oficial y configuración de variables de entorno.
   - Construcción del servicio `SupabaseAuthService` en infraestructura.
2. **Casos de Uso de Autenticación (1 día):**
   - `IniciarSesionUseCase`: Llama a Supabase, obtiene el JWT y devuelve las credenciales.
   - `CerrarSesionUseCase`.
3. **Middleware y Protección de Rutas (1 día):**
   - Refactorizar todos los controladores (`/becario`, `/tutor`, `/admin`) usando un decorador Flask (ej. `@login_required`).
   - Validación y parseo del JWT guardado en la `session` del servidor.
4. **Pantalla de Login Global (1 día):**
   - **Frontend:** Interfaz única de inicio de sesión que redirija al Dashboard correspondiente (Becario, Tutor o Admin) analizando el Rol de la base de datos tras un login exitoso.

---

## 🔴 FASE 5: Integracion de workflows de n8n
**Estado:** `EN ESPERA` ⏸️  
**Duración Estimada:** Por estimar 
**SE DESARROLLARA EN PARALELO CON LA FASE 4**

Se desarrollaran los flujos de n8n para la generacion de notificaciones con respecto a las transiciones de estados datos academicos

### Desglose de Tareas Técnicas
1. **Integración con Supabase (4 horas):** Generar las apis y URL necesarias para configurar las credenciales de supabase en n8n.

2. **Diseño de los worflows):** Modelado de el diagrama de flujo para implementar los workflows contemplando cada uno de las transiciones posibles de estados academicos

3. **Integracion con medios de comunicacion:** Estudio de las posibildiades de integracion con gmail o WhatsApp (para este ultimo, considerar la creacion de scrips de python y APIs para que las consuman un flujo de n8n)

## ❌ FUERA DEL ALCANCE (Diferido Post-MVP)
Para garantizar la velocidad de entrega, los siguientes requerimientos están descartados para esta etapa:
- **Área y Panel del Mediador:** No existirá vista para este actor.
- **Área y Panel del Padrino:** No existirá vista para este actor.
- **Envío Automatizado de Cartas:** El proceso será manual y externo al sistema temporalmente.
- **Mensajería / Chat Interno:** Toda comunicación se resolverá redirigiendo a WhatsApp o correos electrónicos.
