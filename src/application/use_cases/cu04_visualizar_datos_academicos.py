from src.application.dto_mapper import usuario_to_dict, datos_academicos_to_dict
"""
Caso de Uso 04: Visualizar Datos Académicos (Becario).

Permite a un Becario autenticado consultar el estado y la información
de sus datos académicos. Retorna un diccionario puro (DTO) para que
la capa de presentación no dependa de las entidades de dominio.

Scope: Solo el contexto del Becario. La visualización por parte del
Tutor será implementada en una iteración futura.
"""

from typing import Any, Dict

from src.application.protocols import BecarioRepositoryProtocol


class CU04_VisualizarDatosAcademicos:
    """
    Application-layer interactor for CU-04 (Becario context).

    Receives a repository abstraction via constructor injection and
    orchestrates the retrieval + DTO conversion of academic data.
    """

    def __init__(self, repositorio: BecarioRepositoryProtocol) -> None:
        """
        Initialize the use case with its repository dependency.

        Args:
            repositorio: An object satisfying BecarioRepositoryProtocol.
        """
        self.repositorio = repositorio

    def ejecutar(self, becario_id: str) -> Dict[str, Any]:
        """
        Execute the use case: fetch and serialize the Becario's academic data.

        Args:
            becario_id: The unique identifier of the authenticated Becario.

        Returns:
            A dictionary (DTO) with the academic data fields and their
            current values. Returns an empty dict if the Becario has no
            academic data initialized.

        Raises:
            ValueError: If no Becario with the given ID exists in the repository.
        """
        becario = self.repositorio.obtener_por_id(becario_id)

        if becario is None:
            raise ValueError(f"No se encontró un becario con el ID '{becario_id}'")

        # Guard: if datos_academicos is somehow None, return empty DTO
        if becario.datos_academicos is None:
            return {}

        return datos_academicos_to_dict(becario.datos_academicos)
