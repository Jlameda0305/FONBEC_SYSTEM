"""
CU-ADM-06: Supervisión Académica por Administrador.

Permite a un administrador visualizar los datos académicos de un becario, 
pero solo si su estado de verificación es "Aprobado", garantizando 
así la no interferencia con la labor de auditoría del Tutor (RN-06, RN-07).
"""

from typing import Dict, Any

from src.application.protocols import BecarioRepositoryProtocol
from src.domain.enums import EstadoVerificacion

class VerDatosAcademicosUseCase:
    """
    Interactor para consultar el estado académico de un Becario 
    por parte del Administrador.
    """
    
    def __init__(self, becario_repo: BecarioRepositoryProtocol):
        self.becario_repo = becario_repo

    def ejecutar(self, actor_admin: object, id_becario: str) -> Dict[str, Any]:
        """
        Ejecuta el caso de uso.
        
        Retorna un DTO de presentación:
        - Si el estado es APROBADO: Retorna los datos académicos completos.
        - Si el estado es distinto: Retorna {'acceso_restringido': True, 'estado_actual': ...}
        
        Args:
            actor_admin: Instancia del actor ejecutante (debe ser Administrador).
            id_becario: ID del Becario objetivo.
        """
        if getattr(actor_admin, "rol", None) != "administrador":
            raise PermissionError("Solo un Administrador puede supervisar datos académicos de terceros.")
            
        becario = self.becario_repo.obtener_por_id(id_becario)
        if not becario:
            raise ValueError(f"No se encontró un becario con ID: {id_becario}")
            
        estado_actual = becario.datos_academicos.estado_verificacion
        
        # Si NO está aprobado, restringimos el acceso
        if estado_actual != EstadoVerificacion.APROBADO:
            return {
                "acceso_restringido": True,
                "estado_actual": estado_actual.value
            }
            
        # Si está aprobado, retornamos los datos tal cual los ve el Tutor (o el Becario)
        # becario.visualizar_formulario_academico arroja error en APROBADO para CU03, 
        # así que accederemos a sus campos directamente de forma estructurada.
        da = becario.datos_academicos
        documentos = {
            doc.tipo_documento: {
                "ruta_archivo": doc.ruta_archivo,
                "fecha_carga": doc.fecha_carga.isoformat() if doc.fecha_carga else None,
            }
            for doc in da.lista_documentos
        }
        
        return {
            "acceso_restringido": False,
            "estado_actual": estado_actual.value,
            "nombre_carrera": da.nombre_carrera,
            "anio_ingreso": da.anio_ingreso,
            "anio_en_curso": da.anio_en_curso,
            "materias_a_cursar": da.materias_a_cursar,
            "materias_adeudadas": da.materias_adeudadas,
            "documentos": documentos,
            "observaciones": da.observaciones
        }
