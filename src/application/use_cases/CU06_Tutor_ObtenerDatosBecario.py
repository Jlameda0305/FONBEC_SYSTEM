"""
Use Case 06 - Tutor: Obtener Datos de Becario

Responsable de extraer de forma segura los datos personales y la red
de contención de un becario (Mediador y Padrino) garantizando que
el Tutor autenticado esté efectivamente asignado a dicho becario.
"""

from typing import Dict, Any

from src.application.protocols import TutorRepositoryProtocol


class ObtenerDatosBecarioUseCase:
    """
    Use case interactor for securely retrieving a Becario's profile.
    """

    def __init__(self, repository: TutorRepositoryProtocol):
        self.repository = repository

    def execute(self, tutor_id: str, becario_id: str) -> Dict[str, Any]:
        """
        Extrae los datos básicos del becario y de sus contactos.

        Args:
            tutor_id: UUID del tutor en sesión.
            becario_id: UUID del becario solicitado.

        Returns:
            Dict agrupando perfil del becario, datos del mediador y datos del padrino.
            
        Raises:
            ValueError: Si el tutor no existe o si el becario no le pertenece.
        """
        # 1. Recuperar el tutor (trae asociados los becarios mediante eager loading)
        tutor = self.repository.obtener_por_id(tutor_id)
        if not tutor:
            raise ValueError("Tutor no encontrado o no autorizado.")

        # 2. Seguridad en Dominio: Se valida que el becario pertenezca a la cartera de este tutor.
        # Si no le pertenece, lanzará "No posee permisos para acceder al becario solicitado."
        becario = tutor.seleccionar_becario(becario_id)

        # 3. Empaquetar Perfil Base
        datos_contacto_becario = becario.get_datos_contacto()
        perfil_becario = {
            "nombre": becario.nombre,
            "apellido": becario.apellido,
            "edad": getattr(becario, 'edad', 'N/A'),
            "sexo": getattr(becario, 'sexo', 'N/A'),
            "direccion": getattr(becario, 'direccion', 'N/A'),
            "email": datos_contacto_becario.get("email"),
            "telefono": datos_contacto_becario.get("telefono")
        }

        # 4. Empaquetar Mediador
        mediador_asignado = None
        if becario.puntero_mediador:
            contacto_mediador = becario.puntero_mediador.get_datos_contacto()
            mediador_asignado = {
                "nombre": contacto_mediador.get("nombre"),
                "apellido": contacto_mediador.get("apellido"),
                "email": contacto_mediador.get("email"),
                "telefono": contacto_mediador.get("telefono")
            }

        # 5. Empaquetar Padrino
        padrino_asignado = None
        if becario.puntero_padrino:
            # Padrino hereda de AbstractActor, pero para asegurarnos usamos sus propiedades directas
            padrino_asignado = {
                "nombre": becario.puntero_padrino.nombre,
                "apellido": becario.puntero_padrino.apellido,
                "email": becario.puntero_padrino.email,
                "telefono": becario.puntero_padrino.telefono
            }

        return {
            "perfil_becario": perfil_becario,
            "mediador_asignado": mediador_asignado,
            "padrino_asignado": padrino_asignado,
            "datos_academicos": becario.datos_academicos.to_dict() if becario.datos_academicos else {}
        }
