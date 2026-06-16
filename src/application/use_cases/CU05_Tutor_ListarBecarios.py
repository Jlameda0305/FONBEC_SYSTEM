from src.application.dto_mapper import usuario_to_dict, datos_academicos_to_dict
"""
Use Case 05 - Tutor: Listar Becarios Asignados

Recibe el ID del Tutor, accede a la base de datos a través de su Repositorio,
y devuelve una lista formateada con los datos de sus becarios a cargo,
incluyendo el estado de sus datos académicos para facilitar la auditoría.
"""

from typing import List, Dict, Any

from src.application.protocols import TutorRepositoryProtocol

class ListarBecariosTutorUseCase:
    """
    Use case interactor for retrieving a Tutor's assigned Becarios.
    """

    def __init__(self, repository: TutorRepositoryProtocol):
        self.repository = repository

    def execute(self, tutor_id: str, busqueda: str = None) -> List[Dict[str, Any]]:
        """
        Ejecuta el caso de uso para listar becarios.

        Args:
            tutor_id: UUID del tutor en sesión.
            busqueda: Término opcional para filtrar por nombre, apellido o email.

        Returns:
            Una lista de diccionarios (DTOs) con los datos del becario.
            
        Raises:
            ValueError: Si el tutor no existe en la base de datos.
        """
        tutor = self.repository.obtener_por_id(tutor_id)
        if not tutor:
            raise ValueError("Tutor no encontrado o no autorizado")

        resultados = []
        for b in tutor.lista_becarios:
            if busqueda:
                termino = busqueda.lower()
                nombre_completo = f"{b.nombre} {b.apellido}".lower()
                email = b.email.lower()
                if termino not in nombre_completo and termino not in email:
                    continue

            dto = usuario_to_dict(b)
            
            # The domain entity guarantees these attributes exist, but we handle the Enum value extraction
            dto['estado_verificacion'] = b.datos_academicos.estado_verificacion.value if getattr(b, 'datos_academicos', None) else None
            
            if b.datos_academicos:
                da = b.datos_academicos
                dto['datos_academicos'] = {
                    'estado_verificacion': da.estado_verificacion.value if getattr(da, 'estado_verificacion', None) else None
                }
            else:
                dto['datos_academicos'] = None
                
            resultados.append(dto)

        return resultados
