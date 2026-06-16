from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .becario import Becario

@dataclass
class Usuario(ABC):
    """
    Abstract base for all system actors (AOO §1.1).

    login() and logout() raise NotImplementedError because actual
    authentication is handled by the infrastructure layer.
    """
    id_usuario: str
    nombre: str
    apellido: str
    email: str
    telefono: str
    edad: int
    sexo: str
    direccion: str
    rol: str

    def login(self) -> None:
        """Authenticate the user. Delegated to infrastructure."""
        raise NotImplementedError("Autenticación delegada a la capa de infraestructura.")

    def logout(self) -> None:
        """End the user session. Delegated to infrastructure."""
        raise NotImplementedError("Cierre de sesión delegado a la capa de infraestructura.")

    def actualizar_datos_personales(self, telefono: str = None, direccion: str = None, edad: int = None, sexo: str = None) -> None:
        """Update personal data fields."""
        if telefono is not None:
            self.telefono = telefono
        if direccion is not None:
            self.direccion = direccion
        if edad is not None:
            self.edad = edad
        if sexo is not None:
            self.sexo = sexo
    def restablecer_contrasena(self) -> None:
        """Reset password. Stub — no .puml for this CU."""
        raise NotImplementedError

    @abstractmethod
    def visualizar_datos_academicos(self) -> dict:
        """
        Retrieve academic data for visualization (CU-04).
        Each subclass provides its own implementation.
        """


@dataclass
class Referente(Usuario, ABC):
    """
    Abstract base for Tutor and Mediador (AOO §1.3).
    Shares lista_becarios and listar_becarios_asignados().
    """
    lista_becarios: list[Becario] = field(default_factory=list)

    def listar_becarios_asignados(self) -> list[Becario]:
        """
        Return the list of assigned Becarios (CU-05).
        """
        return self.lista_becarios

    @abstractmethod
    def seleccionar_becario(self, id_becario: str) -> Becario:
        """
        Select a Becario by ID and load their context (CU-06/CU-07).
        Each subclass loads different context data.
        """
