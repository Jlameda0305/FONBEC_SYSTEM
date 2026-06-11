from dataclasses import dataclass

@dataclass
class Padrino:
    """
    External reference entity — sponsor without system access.
    Used as a letter recipient in the EnvioCarta flow (out of MVP scope).
    """
    id_padrino: str
    nombre: str
    apellido: str
    email: str
    telefono: str
    direccion: str

    def get_datos_basicos(self) -> dict:
        """
        Return basic profile information for this Padrino.
        """
        return {
            "nombre": self.nombre,
            "apellido": self.apellido,
            "email": self.email,
            "telefono": self.telefono
        }
