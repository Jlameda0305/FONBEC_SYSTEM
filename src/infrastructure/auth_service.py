"""
Supabase Authentication Service implementation.
"""

from typing import Optional
import os
from supabase import Client
from src.application.protocols import AuthServiceProtocol


class SupabaseAuthService(AuthServiceProtocol):
    """
    Concrete implementation of AuthServiceProtocol using Supabase Auth.
    """

    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client

    def invitar_usuario(self, email: str, rol: str) -> str:
        """
        Invites a user using Supabase Admin API.
        Note: Requires SUPABASE_SERVICE_ROLE_KEY initialized client.
        """
        base_url = os.environ.get("BASE_URL", "http://127.0.0.1:5000").rstrip("/")
        response = self.supabase.auth.admin.invite_user_by_email(
            email,
            options={
                "data": {
                    "rol": rol
                },
                "redirect_to": f"{base_url}/auth/callback"
            }
        )
        return response.user.id

    def recuperar_contrasena(self, email: str) -> None:
        """
        Requests a password reset email via Supabase auth.
        """
        base_url = os.environ.get("BASE_URL", "http://127.0.0.1:5000").rstrip("/")
        self.supabase.auth.reset_password_email(
            email,
            options={
                "redirect_to": f"{base_url}/auth/nueva-contrasena"
            }
        )

    def intercambiar_codigo(self, code: str) -> dict:
        """
        Exchanges an auth code for a session via Supabase.
        """
        res = self.supabase.auth.exchange_code_for_session({"auth_code": code})
        return {
            "access_token": res.session.access_token,
            "refresh_token": res.session.refresh_token
        }

    def obtener_usuario(self, access_token: str) -> Optional[dict]:
        """
        Retrieves user info using an access token.
        """
        try:
            response = self.supabase.auth.get_user(access_token)
            return response.user.model_dump() if response.user else None
        except Exception:
            return None

    def establecer_contrasena(self, access_token: str, nueva_contrasena: str, refresh_token: str) -> None:
        """
        Sets a new password for the authenticated user using Supabase auth.
        """
        # Set the session on the client so we can update the user
        # Note: supabase-py requires the session to be set for user update operations
        self.supabase.auth.set_session(access_token, refresh_token)
        self.supabase.auth.update_user({
            "password": nueva_contrasena
        })
        # Clear the session from the client instance to avoid cross-request contamination
        self.supabase.auth.sign_out()

    def login(self, email: str, password: str) -> dict:
        """
        Authenticates a user with email and password via Supabase auth.
        """
        try:
            response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            return {
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
                "user": response.user.model_dump() if response.user else None
            }
        except Exception as e:
            raise ValueError(f"Error de autenticación: {str(e)}")

    def logout(self, access_token: str) -> None:
        """
        Invalidates a session remotely using an access token.
        """
        try:
            # Set a dummy session in the client so we can sign out
            self.supabase.auth.set_session(access_token, "")
            self.supabase.auth.sign_out()
        except Exception:
            # If the token is already expired or invalid, we ignore the error
            # to ensure the local logout flow continues.
            pass

    def eliminar_usuario_auth(self, user_id: str) -> None:
        """
        Deletes a user identity from Supabase Auth via Admin API.
        Requires SUPABASE_SERVICE_ROLE_KEY to be configured.
        """
        try:
            self.supabase.auth.admin.delete_user(user_id)
        except Exception as e:
            raise ValueError(f"No se pudo eliminar el usuario en Auth: {str(e)}")
