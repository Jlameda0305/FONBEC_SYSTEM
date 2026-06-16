import unittest

from src.application.use_cases.CU02_ContactarReferente import (
    ContactarReferenteUseCase,
    ObtenerDatosReferentesUseCase
)
from src.domain.actors.becario import Becario
from src.domain.actors.tutor import Tutor
from src.domain.actors.mediador import Mediador
from src.domain.domain_entities.padrino import Padrino

class MockBecarioRepository:
    def __init__(self, becarios: dict):
        self.becarios = becarios

    def obtener_por_id(self, becario_id: str) -> Becario:
        return self.becarios.get(becario_id)

    def guardar(self, becario: Becario) -> None:
        pass


class TestCU02ContactarReferente(unittest.TestCase):
    def setUp(self):
        tutor = Tutor(
            id_usuario="tut1", nombre="Laura", apellido="M", email="laura@m.com",
            telefono="123", edad=30, sexo="F", direccion="X", rol="tutor"
        )
        mediador = Mediador(
            id_usuario="med1", nombre="Carlos", apellido="G", email="carlos@g.com",
            telefono="456", edad=40, sexo="M", direccion="Y", rol="mediador"
        )
        padrino = Padrino(
            id_padrino="pad1", nombre="Ana", apellido="P", email="ana@p.com",
            telefono="789", direccion="Z"
        )
        
        becario_completo = Becario(
            id_usuario="bec1", nombre="Juan", apellido="B", email="juan@b.com",
            telefono="000", edad=20, sexo="M", direccion="W",
            puntero_tutor=tutor, puntero_mediador=mediador, puntero_padrino=padrino
        )
        
        becario_sin_tutor = Becario(
            id_usuario="bec2", nombre="Pedro", apellido="B", email="pedro@b.com",
            telefono="001", edad=21, sexo="M", direccion="W",
            puntero_mediador=mediador
        )
        
        self.repo_mock = MockBecarioRepository({
            "bec1": becario_completo,
            "bec2": becario_sin_tutor
        })

    def test_contactar_tutor_exitoso(self):
        use_case = ContactarReferenteUseCase(self.repo_mock)
        resultado = use_case.execute(actor_id="bec1", rol_actor="becario", objetivo_contacto="tutor")
        
        self.assertEqual(resultado["nombre"], "Laura")
        self.assertEqual(resultado["email"], "laura@m.com")
        self.assertEqual(resultado["telefono"], "123")

    def test_contactar_mediador_exitoso(self):
        use_case = ContactarReferenteUseCase(self.repo_mock)
        resultado = use_case.execute(actor_id="bec1", rol_actor="becario", objetivo_contacto="mediador")
        
        self.assertEqual(resultado["nombre"], "Carlos")
        self.assertEqual(resultado["telefono"], "456")

    def test_contactar_tutor_sin_asignar_lanza_error(self):
        use_case = ContactarReferenteUseCase(self.repo_mock)
        with self.assertRaisesRegex(ValueError, "No posee tutor asignado"):
            use_case.execute(actor_id="bec2", rol_actor="becario", objetivo_contacto="tutor")

    def test_contactar_padrino_lanza_error(self):
        use_case = ContactarReferenteUseCase(self.repo_mock)
        with self.assertRaisesRegex(ValueError, "Los becarios y padrinos no pueden contactarse directamente"):
            use_case.execute(actor_id="bec1", rol_actor="becario", objetivo_contacto="padrino")

    def test_rol_no_soportado_lanza_error(self):
        use_case = ContactarReferenteUseCase(self.repo_mock)
        with self.assertRaises(NotImplementedError):
            use_case.execute(actor_id="bec1", rol_actor="tutor", objetivo_contacto="mediador")

    def test_obtener_datos_referentes_completo(self):
        use_case = ObtenerDatosReferentesUseCase(self.repo_mock)
        resultado = use_case.execute("bec1")
        
        self.assertIsNotNone(resultado["tutor"])
        self.assertEqual(resultado["tutor"]["nombre"], "Laura")
        
        self.assertIsNotNone(resultado["mediador"])
        self.assertEqual(resultado["mediador"]["nombre"], "Carlos")
        
        self.assertIsNotNone(resultado["padrino"])
        self.assertEqual(resultado["padrino"]["nombre"], "Ana")

    def test_obtener_datos_referentes_incompleto(self):
        use_case = ObtenerDatosReferentesUseCase(self.repo_mock)
        resultado = use_case.execute("bec2")
        
        self.assertIsNone(resultado["tutor"])
        self.assertIsNotNone(resultado["mediador"])
        self.assertIsNone(resultado["padrino"])

if __name__ == '__main__':
    unittest.main()
