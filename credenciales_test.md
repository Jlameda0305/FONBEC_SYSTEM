# Credenciales de Prueba (Fase 2: Login)

A continuación, se detallan los usuarios generados en el sistema (Supabase Auth + DB Local) listos para testear el flujo de Login y redireccionamiento por roles:

### 1. Administrador
- **Email:** `admin@fonbec.org`
- **Contraseña:** `password123`
- **Destino post-login esperado:** `/admin/dashboard`

### 2. Tutor
- **Email:** `tutor@fonbec.org`
- **Contraseña:** `password123`
- **Destino post-login esperado:** `/tutor/dashboard`

### 3. Becario
- **Email:** `becario@fonbec.org`
- **Contraseña:** `password123`
- **Destino post-login esperado:** `/becario/dashboard`

> **Nota:** Estos usuarios fueron insertados vía Admin API en Supabase (evadiendo la confirmación de email) y fueron inyectados directamente en las tablas locales (`administradores`, `tutores`, `becarios`) respetando el Clean Architecture. Podés utilizarlos para probar cierres y aperturas de sesión libres de fricción.
