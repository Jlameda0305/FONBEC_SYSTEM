from src.application.dto_mapper import usuario_to_dict, datos_academicos_to_dict
"""
Use Case 06 - Mediador: Obtener Datos de Becario

Responsable de extraer de forma segura los datos personales y la red
de contención de un becario (Tutor y Padrino) garantizando que
el Mediador autenticado esté efectivamente asignado a dicho becario.
"""

from typing import Dict, Any

from src.application.protocols import MediadorRepositoryProtocol


class ObtenerDatosBecarioUseCase:
    """
    Use case interactor for securely retrieving a Becario's profile for a Mediador.
    """

    def __init__(self, repository: MediadorRepositoryProtocol):
        self.repository = repository

    def execute(self, mediador_id: str, becario_id: str) -> Dict[str, Any]:
        """
        Extrae los datos básicos del becario y de sus contactos.

        Args:
            mediador_id: UUID del mediador en sesión.
            becario_id: UUID del becario solicitado.

        Returns:
            Dict agrupando perfil del becario, datos del tutor y datos del padrino.
            
        Raises:
            ValueError: Si el mediador no existe o si el becario no le pertenece.
        """
        # 1. Recuperar el mediador (trae asociados los becarios mediante eager loading)
        mediador = self.repository.obtener_por_id(mediador_id)
        if not mediador:
            raise ValueError("Mediador no encontrado o no autorizado.")

        # 2. Seguridad en Dominio: Se valida que el becario pertenezca a la cartera de este mediador.
        becario = mediador.seleccionar_becario(becario_id)

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

        # 4. Empaquetar Tutor
        tutor_asignado = None
        if becario.puntero_tutor:
            contacto_tutor = becario.puntero_tutor.get_datos_contacto()
            tutor_asignado = {
                "nombre": contacto_tutor.get("nombre"),
                "apellido": contacto_tutor.get("apellido"),
                "email": contacto_tutor.get("email"),
                "telefono": contacto_tutor.get("telefono")
            }

        # 5. Empaquetar Padrino
        padrino_asignado = None
        if becario.puntero_padrino:
            padrino_asignado = {
                "nombre": becario.puntero_padrino.nombre,
                "apellido": becario.puntero_padrino.apellido,
                "email": becario.puntero_padrino.email,
                "telefono": becario.puntero_padrino.telefono
            }

        return {
            "perfil_becario": perfil_becario,
            # Se usa la clave mediador_asignado para el Tutor en la plantilla reutilizada (se podría mapear distinto si la plantilla lo soportara)
            # Aunque en shared/becario_detalle.html las tarjetas dicen "Tutor/Mediador".
            # Es mejor pasar ambos explícitamente y que la vista lo decida, pero para no romper enviamos mediador_asignado = None (el actual es el que mira la pantalla) y pasamos tutor_asignado
            "tutor_asignado": tutor_asignado,
            "mediador_asignado": None,
            "padrino_asignado": padrino_asignado,
            "datos_academicos": datos_academicos_to_dict(becario.datos_academicos) if becario.datos_academicos else {}
        }
