from dataclasses import dataclass
from datetime import datetime

@dataclass
class DocumentoAcademico:
    """
    PDF attachment linked to a Becario's academic data.
    Data-only container; no methods in MVP.
    """
    tipo_documento: str
    ruta_archivo: str
    fecha_carga: datetime
