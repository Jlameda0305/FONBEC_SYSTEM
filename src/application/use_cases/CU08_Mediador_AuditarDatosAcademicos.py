from src.application.dto_mapper import usuario_to_dict, datos_academicos_to_dict
from src.application.protocols import MediadorRepositoryProtocol

class AuditarDatosAcademicosUseCase:
    """
    CU08: Auditar Datos Académicos (Mediador).
    
    Allows a Mediador to review the academic information uploaded by an assigned Becario,
    either approving it or rejecting it (with observations).
    """

    def __init__(self, mediador_repository: MediadorRepositoryProtocol):
        self.mediador_repository = mediador_repository

    def execute(self, id_mediador: str, id_becario: str, decision: str, observaciones: str = "") -> dict:
        """
        Executes the audit workflow.
        
        Args:
            id_mediador: The ID of the authenticated Mediador.
            id_becario: The ID of the Becario whose data is being audited.
            decision: "aprobar" or "rechazar".
            observaciones: Text detailing the reason for rejection (required if rejected).
            
        Returns:
            The serialized dict of the updated DatosAcademicos.
            
        Raises:
            ValueError: If the Mediador does not exist, the Becario is not assigned,
                        the transition is invalid, or the decision is malformed.
        """
        # 1. Recuperar el mediador
        mediador = self.mediador_repository.obtener_por_id(id_mediador)
        if not mediador:
            raise ValueError(f"Mediador con ID '{id_mediador}' no encontrado.")
            
        # 2. Obtener y validar permisos sobre el becario (vía Dominio)
        becario = mediador.seleccionar_becario(id_becario)
        
        # 3. Validar obligatoriedad de observaciones
        if decision == "rechazar" and not observaciones.strip():
            raise ValueError("Las observaciones son obligatorias al rechazar los datos.")
            
        # 4. Auditar (Modificar estado en el Dominio)
        mediador.auditar_datos_academicos_becario(becario, decision, observaciones)
        
        # 5. Persistir (Unit of Work implícito)
        self.mediador_repository.guardar(mediador)
        
        # 6. Devolver DTO del estado actualizado
        return datos_academicos_to_dict(becario.datos_academicos)
