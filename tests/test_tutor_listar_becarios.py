import unittest
from unittest.mock import MagicMock

from src.application.use_cases.CU05_Tutor_ListarBecarios import ListarBecariosTutorUseCase
from src.domain.actors.tutor import Tutor
from src.domain.models import Becario, DatosAcademicos
from src.domain.enums import EstadoVerificacion


class MockTutorRepository:
    def __init__(self):
        self.tutor_db = {}

    def obtener_por_id(self, tutor_id: str) -> Tutor:
        return self.tutor_db.get(tutor_id)


class TestListarBecariosTutorUseCase(unittest.TestCase):
    def setUp(self):
        self.repo = MockTutorRepository()
        self.use_case = ListarBecariosTutorUseCase(self.repo)

    def test_tutor_not_found(self):
        """Si el tutor no existe, debe lanzar ValueError."""
        with self.assertRaises(ValueError) as context:
            self.use_case.execute("fake-tutor-id")
        self.assertEqual(str(context.exception), "Tutor no encontrado o no autorizado")

    def test_tutor_sin_becarios_asignados(self):
        """Si el tutor no tiene becarios, debe retornar una lista vacía."""
        tutor = Tutor(
            id_usuario="tutor-123",
            nombre="Juan",
            apellido="Perez",
            email="tutor@test.com",
            telefono="12345",
            edad=40, sexo="M", direccion="dir"
        )
        tutor.lista_becarios = []
        self.repo.tutor_db["tutor-123"] = tutor

        resultado = self.use_case.execute("tutor-123")
        self.assertEqual(resultado, [])

    def test_tutor_con_becarios_retorna_lista_formateada(self):
        """Si el tutor tiene becarios, retorna una lista de diccionarios con sus datos y estados."""
        # Armar el mock del Tutor
        tutor = Tutor(
            id_usuario="tutor-123",
            nombre="Juan",
            apellido="Perez",
            email="tutor@test.com",
            telefono="12345",
            edad=40, sexo="M", direccion="dir"
        )

        # Armar Becario 1 (Pendiente)
        becario_1 = Becario(
            id_usuario="bec-1",
            nombre="Carlos",
            apellido="Gomez",
            email="carlos@test.com",
            telefono="999",
            edad=20, sexo="M", direccion="dir"
        )
        datos_1 = DatosAcademicos()
        datos_1.estado_verificacion = EstadoVerificacion.PENDIENTE_REVISION
        becario_1.datos_academicos = datos_1

        # Armar Becario 2 (Aprobado)
        becario_2 = Becario(
            id_usuario="bec-2",
            nombre="Ana",
            apellido="Silva",
            email="ana@test.com",
            telefono="888",
            edad=22, sexo="F", direccion="dir"
        )
        datos_2 = DatosAcademicos()
        datos_2.estado_verificacion = EstadoVerificacion.APROBADO
        becario_2.datos_academicos = datos_2

        # Asignar becarios al tutor
        tutor.lista_becarios = [becario_1, becario_2]
        self.repo.tutor_db["tutor-123"] = tutor

        # Ejecutar Caso de Uso
        resultado = self.use_case.execute("tutor-123")

        # Validaciones
        self.assertEqual(len(resultado), 2)
        
        self.assertEqual(resultado[0]["id_usuario"], "bec-1")
        self.assertEqual(resultado[0]["nombre"], "Carlos")
        self.assertEqual(resultado[0]["edad"], 20)
        self.assertEqual(resultado[0]["estado_verificacion"], "Pendiente_Revision")
        
        self.assertEqual(resultado[1]["id_usuario"], "bec-2")
        self.assertEqual(resultado[1]["nombre"], "Ana")
        self.assertEqual(resultado[1]["edad"], 22)
        self.assertEqual(resultado[1]["estado_verificacion"], "Aprobado")


if __name__ == "__main__":
    unittest.main()
