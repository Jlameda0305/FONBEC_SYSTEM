# Observaciones

- **Regla 2 (Supabase Auth)**: Exceptuada temporalmente para la fase actual del MVP. Los controladores (`admin.py`, `tutor.py`, `becario.py`) utilizan `obtener_usuario_actual()` desde `src.web.mock_auth_service` para resolver la identidad de los usuarios y probar los Casos de Uso. Esta validación deberá ser reemplazada posteriormente por la autenticación real.

- **Regla 1 (CSS Vainilla)**: Exceptuada temporalmente. Aunque el estándar exige CSS Vainilla y prohíbe utilitarios, el dashboard actual ha sido migrado al diseño "Argon Dashboard" el cual depende fuertemente de clases utilitarias y componentes de Bootstrap 4 (`btn`, `card`, `bg-gradient-primary`, etc.) para mantener la coherencia y velocidad en la entrega del MVP.
