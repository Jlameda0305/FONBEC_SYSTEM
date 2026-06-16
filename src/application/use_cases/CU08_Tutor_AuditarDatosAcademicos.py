from src.application.dto_mapper import usuario_to_dict, datos_academicos_to_dict
from src.application.protocols import TutorRepositoryProtocol

class AuditarDatosAcademicosUseCase:
    """
    CU08: Auditar Datos Académicos (Tutor).
    
    Allows a Tutor to review the academic information uploaded by an assigned Becario,
    either approving it or rejecting it (with observations).
    """

    def __init__(self, tutor_repository: TutorRepositoryProtocol):
        self.tutor_repository = tutor_repository

    def execute(self, id_tutor: str, id_becario: str, decision: str, observaciones: str = "") -> dict:
        """
        Executes the audit workflow.
        
        Args:
            id_tutor: The ID of the authenticated Tutor.
            id_becario: The ID of the Becario whose data is being audited.
            decision: "aprobar" or "rechazar".
            observaciones: Text detailing the reason for rejection (required if rejected).
            
        Returns:
            The serialized dict of the updated DatosAcademicos.
            
        Raises:
            ValueError: If the Tutor does not exist, the Becario is not assigned,
                        the transition is invalid, or the decision is malformed.
        """
        # 1. Recuperar el tutor
        tutor = self.tutor_repository.obtener_por_id(id_tutor)
        if not tutor:
            raise ValueError(f"Tutor con ID '{id_tutor}' no encontrado.")
            
        # 2. Obtener y validar permisos sobre el becario (vía Dominio)
        becario = tutor.seleccionar_becario(id_becario)
        
        # 3. Validar obligatoriedad de observaciones
        if decision == "rechazar" and not observaciones.strip():
            raise ValueError("Las observaciones son obligatorias al rechazar los datos.")
            
        # 4. Auditar (Modificar estado en el Dominio)
        tutor.auditar_datos_academicos_becario(becario, decision, observaciones)
        
        # 5. Persistir (Unit of Work implícito)
        self.tutor_repository.guardar(tutor)
        
        # 6. Devolver DTO del estado actualizado
        return datos_academicos_to_dict(becario.datos_academicos)
