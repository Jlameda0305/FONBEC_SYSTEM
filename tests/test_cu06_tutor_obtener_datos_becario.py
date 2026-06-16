import unittest

from src.application.use_cases.CU06_Tutor_ObtenerDatosBecario import ObtenerDatosBecarioUseCase
from src.domain.actors.tutor import Tutor
from src.domain.models import Becario, Mediador, Padrino


class MockTutorRepository:
    def __init__(self):
        self.tutor_db = {}

    def obtener_por_id(self, tutor_id: str) -> Tutor:
        return self.tutor_db.get(tutor_id)


class TestObtenerDatosBecarioUseCase(unittest.TestCase):
    def setUp(self):
        self.repo = MockTutorRepository()
        self.use_case = ObtenerDatosBecarioUseCase(self.repo)

        # Configurar estado base
        self.tutor = Tutor(
            id_usuario="tutor-123",
            nombre="Juan",
            apellido="Tutor",
            email="tutor@test.com",
            telefono="111",
            edad=40, sexo="M", direccion="dir"
        )
        
        self.becario = Becario(
            id_usuario="bec-1",
            nombre="Carlos",
            apellido="Gomez",
            email="carlos@test.com",
            telefono="222",
            edad=20, sexo="M", direccion="Calle Falsa 123"
        )
        
        self.mediador = Mediador(
            id_usuario="med-1",
            nombre="Ana",
            apellido="Mediador",
            email="ana@test.com",
            telefono="333",
            edad=35, sexo="F", direccion="dir"
        )
        
        self.padrino = Padrino(
            id_padrino="pad-1",
            nombre="Roberto",
            apellido="Padrino",
            email="roberto@test.com",
            telefono="444",
            direccion="dir"
        )

    def test_tutor_no_encontrado(self):
        """Lanza ValueError si el tutor no existe."""
        with self.assertRaisesRegex(ValueError, "Tutor no encontrado o no autorizado"):
            self.use_case.execute("fake-tutor", "bec-1")

    def test_seguridad_acceso_becario_no_asignado(self):
        """Lanza ValueError si el tutor intenta acceder a un becario ajeno."""
        # Tutor existe pero lista de becarios vacía
        self.repo.tutor_db["tutor-123"] = self.tutor

        with self.assertRaisesRegex(ValueError, "No posee permisos para acceder al becario solicitado."):
            self.use_case.execute("tutor-123", "bec-1")

    def test_obtener_datos_completos(self):
        """Retorna el diccionario estructurado con datos del becario, mediador y padrino."""
        # Asociar relaciones
        self.becario.puntero_mediador = self.mediador
        self.becario.puntero_padrino = self.padrino
        self.tutor.lista_becarios = [self.becario]
        self.repo.tutor_db["tutor-123"] = self.tutor

        resultado = self.use_case.execute("tutor-123", "bec-1")

        # Verificar Perfil Becario
        perfil = resultado["perfil_becario"]
        self.assertEqual(perfil["nombre"], "Carlos")
        self.assertEqual(perfil["email"], "carlos@test.com")
        self.assertEqual(perfil["edad"], 20)
        self.assertEqual(perfil["direccion"], "Calle Falsa 123")

        # Verificar Mediador
        med = resultado["mediador_asignado"]
        self.assertIsNotNone(med)
        self.assertEqual(med["nombre"], "Ana")
        self.assertEqual(med["telefono"], "333")

        # Verificar Padrino
        pad = resultado["padrino_asignado"]
        self.assertIsNotNone(pad)
        self.assertEqual(pad["nombre"], "Roberto")
        self.assertEqual(pad["email"], "roberto@test.com")

    def test_obtener_datos_sin_referentes(self):
        """Retorna los datos del becario y None para los referentes si no están asignados."""
        self.tutor.lista_becarios = [self.becario]
        self.repo.tutor_db["tutor-123"] = self.tutor

        resultado = self.use_case.execute("tutor-123", "bec-1")

        self.assertIsNotNone(resultado["perfil_becario"])
        self.assertIsNone(resultado["mediador_asignado"])
        self.assertIsNone(resultado["padrino_asignado"])
        self.assertIn("datos_academicos", resultado)


if __name__ == "__main__":
    unittest.main()
