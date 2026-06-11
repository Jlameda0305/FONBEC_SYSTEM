from dataclasses import dataclass
from datetime import datetime
from src.domain.enums import EstadoEnvioCarta

@dataclass
class EnvioCarta:
    """
    Letter-sending event stub — attributes only (CU-13 to CU-15 out of MVP).
    """
    id_envio: str
    fecha_envio: datetime
    estado: EstadoEnvioCarta = EstadoEnvioCarta.PROGRAMADA
