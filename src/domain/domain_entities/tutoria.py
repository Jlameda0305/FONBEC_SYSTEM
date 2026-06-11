from dataclasses import dataclass
from datetime import datetime
from src.domain.enums import EstadoTutoria

@dataclass
class Tutoria:
    """
    Tutoring session stub — attributes only (CU-09 to CU-12 out of MVP).
    """
    id_tutoria: str
    fecha_hora: datetime
    estado: EstadoTutoria = EstadoTutoria.PROGRAMADA
