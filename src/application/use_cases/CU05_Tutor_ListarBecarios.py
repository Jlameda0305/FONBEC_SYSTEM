"""
Use Case 06 (Partial) - Tutor: Listar Becarios Asignados

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

    def execute(self, tutor_id: str) -> List[Dict[str, Any]]:
        """
        Ejecuta el caso de uso para listar becarios.

        Args:
            tutor_id: UUID del tutor en sesión.

        Returns:
            Una lista de diccionarios con la información de los becarios asignados.
            
        Raises:
            ValueError: Si el tutor no existe en la base de datos.
        """
        tutor = self.repository.obtener_por_id(tutor_id)
        if not tutor:
            raise ValueError("Tutor no encontrado o no autorizado")

        becarios_list = []
        for becario in tutor.lista_becarios:
            datos_contacto = becario.get_datos_contacto()
            
            # Extract state from DatosAcademicos ensuring it doesn't crash if None (though it shouldn't be)
            estado_verificacion = "Desconocido"
            if becario.datos_academicos:
                estado_verificacion = becario.datos_academicos.estado_verificacion.value
                
            becarios_list.append({
                "id_usuario": becario.id_usuario,
                "nombre": becario.nombre,
                "apellido": becario.apellido,
                "edad": getattr(becario, 'edad', 'N/A'),
                "estado_verificacion": estado_verificacion
            })
            
        return becarios_list
