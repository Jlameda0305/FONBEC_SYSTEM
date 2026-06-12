# Observaciones

- **Regla 2 (Supabase Auth)**: Exceptuada temporalmente para la fase actual del MVP. Los controladores (`admin.py`, `tutor.py`, `becario.py`) utilizan `obtener_usuario_actual()` desde `src.web.mock_auth_service` para resolver la identidad de los usuarios y probar los Casos de Uso. Esta validación deberá ser reemplazada posteriormente por la autenticación real.
