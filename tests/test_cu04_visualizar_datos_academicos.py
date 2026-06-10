"""
Unit tests for CU04: Visualizar Datos Académicos (Becario context).

Uses an in-memory fake repository to satisfy BecarioRepositoryProtocol
without any database or SQLAlchemy dependency.
"""

import unittest
from typing import Optional

from src.domain.enums import EstadoVerificacion, NivelCursado
from src.domain.models import Becario, DatosAcademicos
from src.application.protocols import BecarioRepositoryProtocol
from src.application.use_cases.CU04_VisualizarDatosAcademicos import (
    CU04_VisualizarDatosAcademicos,
)


class FakeBecarioRepository:
    """
    In-memory fake repository implementing BecarioRepositoryProtocol.
    """

    def __init__(self) -> None:
        self._store: dict[str, Becario] = {}

    def agregar(self, becario: Becario) -> None:
        """Helper to seed fake data."""
        self._store[becario.id_usuario] = becario

    def obtener_por_id(self, becario_id: str) -> Optional[Becario]:
        return self._store.get(becario_id)


class TestCU04BecarioConDatos(unittest.TestCase):
    """Scenario: Becario with existing academic data."""

    def setUp(self) -> None:
        self.repo = FakeBecarioRepository()
        datos = DatosAcademicos(
            nombre_carrera="Ingeniería en Sistemas",
            anio_ingreso=2023,
            anio_en_curso=3,
            materias_a_cursar=["Algoritmos II", "Base de Datos"],
            materias_adeudadas=["Física I"],
            estado_verificacion=EstadoVerificacion.PENDIENTE_REVISION,
            observaciones=None,
        )
        becario = Becario(
            id_usuario="bec-001",
            nombre="Ana",
            apellido="Lopez",
            email="ana@example.com",
            telefono="111111111",
            edad=19,
            sexo="Femenino",
            direccion="San Martin 100",
            password_hash="hash_b1",
            nivel_cursado=NivelCursado.UNIVERSITARIO,
            datos_academicos=datos,
        )
        self.repo.agregar(becario)
        self.use_case = CU04_VisualizarDatosAcademicos(self.repo)

    def test_retorna_diccionario_con_datos(self) -> None:
        """ejecutar() returns a dict with all academic data fields."""
        resultado = self.use_case.ejecutar("bec-001")
        self.assertIsInstance(resultado, dict)
        self.assertEqual(resultado["nombre_carrera"], "Ingeniería en Sistemas")
        self.assertEqual(resultado["anio_ingreso"], 2023)
        self.assertEqual(resultado["anio_en_curso"], 3)
        self.assertEqual(resultado["materias_a_cursar"], ["Algoritmos II", "Base de Datos"])
        self.assertEqual(resultado["materias_adeudadas"], ["Física I"])

    def test_enum_traducido_a_string(self) -> None:
        """Enum values are serialized to their string representation."""
        resultado = self.use_case.ejecutar("bec-001")
        self.assertEqual(resultado["estado_verificacion"], "Pendiente_Revision")
        self.assertIsInstance(resultado["estado_verificacion"], str)


class TestCU04BecarioSinDatos(unittest.TestCase):
    """Scenario: Becario with no academic data (datos_academicos is None)."""

    def setUp(self) -> None:
        self.repo = FakeBecarioRepository()
        becario = Becario(
            id_usuario="bec-002",
            nombre="Juan",
            apellido="Perez",
            email="juan@example.com",
            telefono="222222222",
            edad=20,
            sexo="Masculino",
            direccion="Belgrano 200",
            password_hash="hash_b2",
            nivel_cursado=NivelCursado.UNIVERSITARIO,
        )
        # Force datos_academicos to None to test the guard clause
        becario.datos_academicos = None
        self.repo.agregar(becario)
        self.use_case = CU04_VisualizarDatosAcademicos(self.repo)

    def test_retorna_diccionario_vacio(self) -> None:
        """ejecutar() returns an empty dict when no academic data exists."""
        resultado = self.use_case.ejecutar("bec-002")
        self.assertIsInstance(resultado, dict)
        self.assertEqual(resultado, {})


class TestCU04BecarioNoEncontrado(unittest.TestCase):
    """Scenario: Becario ID does not exist in the repository."""

    def setUp(self) -> None:
        self.repo = FakeBecarioRepository()
        self.use_case = CU04_VisualizarDatosAcademicos(self.repo)

    def test_lanza_value_error(self) -> None:
        """ejecutar() raises ValueError when the Becario is not found."""
        with self.assertRaises(ValueError) as ctx:
            self.use_case.ejecutar("bec-inexistente")
        self.assertIn("bec-inexistente", str(ctx.exception))


class TestMockAuthService(unittest.TestCase):
    """Scenario: Mock auth service returns hardcoded user."""

    def test_obtener_usuario_actual_retorna_string(self) -> None:
        """obtener_usuario_actual() returns a hardcoded becario_id."""
        from src.application.mock_auth_service import obtener_usuario_actual
        resultado = obtener_usuario_actual()
        self.assertIsInstance(resultado, str)
        self.assertEqual(resultado, "bec-001")


if __name__ == "__main__":
    unittest.main()
