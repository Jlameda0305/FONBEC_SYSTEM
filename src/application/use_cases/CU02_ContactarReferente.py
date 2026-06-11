from typing import Dict, Any

from src.application.protocols import BecarioRepositoryProtocol


class ContactarReferenteUseCase:
    """
    Use Case CU-02: Contactar Referente.
    
    Permite a un actor obtener los datos crudos de contacto (email, teléfono, nombre, apellido)
    del referente objetivo para generar un enlace de contacto directo (ej. wa.me).
    En esta iteración, se soporta exclusivamente el rol "becario".
    """

    def __init__(self, repository: BecarioRepositoryProtocol):
        self.repository = repository

    def execute(self, actor_id: str, rol_actor: str, objetivo_contacto: str) -> Dict[str, Any]:
        """
        Ejecuta la solicitud de contacto.

        Args:
            actor_id: ID del usuario que solicita el contacto.
            rol_actor: Rol en sesión del usuario (debe ser "becario" en esta iteración).
            objetivo_contacto: A quién se quiere contactar ("tutor" o "mediador").

        Returns:
            Dict con las claves: "nombre", "apellido", "email", "telefono".

        Raises:
            ValueError: Si el rol no está soportado, el becario no existe, 
                        o el referente no está asignado.
        """
        if rol_actor.lower() != "becario":
            raise NotImplementedError(
                f"El rol '{rol_actor}' no está implementado para este caso de uso en la iteración actual."
            )

        becario = self.repository.obtener_por_id(becario_id=actor_id)
        if not becario:
            raise ValueError(f"No se encontró un becario con el ID {actor_id}")

        objetivo_normalizado = objetivo_contacto.lower()
        if objetivo_normalizado == "tutor":
            return becario.contacto_tutor()
        elif objetivo_normalizado == "mediador":
            return becario.contacto_mediador()
        elif objetivo_normalizado == "padrino":
            raise ValueError("Los becarios y padrinos no pueden contactarse directamente.")
        else:
            raise ValueError(f"Objetivo de contacto desconocido: {objetivo_contacto}")


class ObtenerDatosReferentesUseCase:
    """
    Use Case auxiliar para recuperar los datos básicos de todos los referentes
    (Tutor, Mediador y Padrino) expuestos en la UI del becario.
    """

    def __init__(self, repository: BecarioRepositoryProtocol):
        self.repository = repository

    def execute(self, becario_id: str) -> Dict[str, Any]:
        """
        Recupera los datos básicos de los referentes asignados al becario.

        Returns:
            Dict con las claves "tutor", "mediador" y "padrino". 
            Si alguno no está asignado, su valor será None.
        """
        becario = self.repository.obtener_por_id(becario_id=becario_id)
        if not becario:
            raise ValueError(f"No se encontró un becario con el ID {becario_id}")

        tutor_data = None
        if becario.puntero_tutor:
            tutor_data = becario.puntero_tutor.get_datos_contacto()

        mediador_data = None
        if becario.puntero_mediador:
            mediador_data = becario.puntero_mediador.get_datos_contacto()

        padrino_data = None
        if becario.puntero_padrino:
            padrino_data = becario.puntero_padrino.get_datos_basicos()

        return {
            "tutor": tutor_data,
            "mediador": mediador_data,
            "padrino": padrino_data
        }
