"""
Use Case 06 - Admin: Obtener Datos de Becario

Responsable de extraer de forma segura los datos personales y la red
de contención de un becario (Tutor, Mediador y Padrino) para su
visualización en el panel administrativo, garantizando el desacoplamiento.
"""

from typing import Dict, Any

from src.application.protocols import BecarioRepositoryProtocol
from src.domain.actors.administrador import Administrador


class AdminObtenerDatosBecarioUseCase:
    """
    Use case interactor for retrieving a Becario's profile for administrators.
    """

    def __init__(self, repository: BecarioRepositoryProtocol):
        self.repository = repository

    def execute(self, actor_admin: Administrador, becario_id: str) -> Dict[str, Any]:
        """
        Extrae los datos básicos del becario y de sus vinculaciones para el administrador.

        Args:
            actor_admin: Instancia del Administrador en sesión.
            becario_id: UUID del becario solicitado.

        Returns:
            Dict agrupando perfil del becario, datos del tutor, mediador y padrino.
            
        Raises:
            PermissionError: Si el actor no es un administrador.
            ValueError: Si el becario no es encontrado.
        """
        if not isinstance(actor_admin, Administrador):
            raise PermissionError("Acceso denegado. Solo administradores pueden realizar esta acción.")

        becario = self.repository.obtener_por_id(becario_id)
        if not becario:
            raise ValueError("Becario no encontrado.")

        datos_contacto_becario = becario.get_datos_contacto()
        perfil_becario = {
            "id_usuario": becario.id_usuario,
            "nombre": becario.nombre,
            "apellido": becario.apellido,
            "edad": getattr(becario, 'edad', 'N/A'),
            "sexo": getattr(becario, 'sexo', 'N/A'),
            "direccion": getattr(becario, 'direccion', 'N/A'),
            "email": datos_contacto_becario.get("email"),
            "telefono": datos_contacto_becario.get("telefono")
        }

        tutor_asignado = None
        if getattr(becario, 'puntero_tutor', None):
            contacto_tutor = becario.puntero_tutor.get_datos_contacto()
            tutor_asignado = {
                "nombre": contacto_tutor.get("nombre"),
                "apellido": contacto_tutor.get("apellido"),
                "email": contacto_tutor.get("email"),
                "telefono": contacto_tutor.get("telefono")
            }

        mediador_asignado = None
        if getattr(becario, 'puntero_mediador', None):
            contacto_mediador = becario.puntero_mediador.get_datos_contacto()
            mediador_asignado = {
                "nombre": contacto_mediador.get("nombre"),
                "apellido": contacto_mediador.get("apellido"),
                "email": contacto_mediador.get("email"),
                "telefono": contacto_mediador.get("telefono")
            }

        padrino_asignado = None
        if getattr(becario, 'puntero_padrino', None):
            padrino_asignado = {
                "nombre": becario.puntero_padrino.nombre,
                "apellido": becario.puntero_padrino.apellido,
                "email": becario.puntero_padrino.email,
                "telefono": becario.puntero_padrino.telefono
            }

        datos_academicos = {}
        if getattr(becario, 'datos_academicos', None):
            datos_academicos = becario.datos_academicos.to_dict()
            if getattr(becario.datos_academicos, 'estado_verificacion', None):
                datos_academicos["estado_verificacion"] = becario.datos_academicos.estado_verificacion.value

        return {
            "perfil_becario": perfil_becario,
            "tutor_asignado": tutor_asignado,
            "mediador_asignado": mediador_asignado,
            "padrino_asignado": padrino_asignado,
            "datos_academicos": datos_academicos
        }
