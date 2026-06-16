import unittest
from unittest.mock import MagicMock

from src.domain.actors.becario import Becario
from src.domain.actors.tutor import Tutor
from src.domain.actors.mediador import Mediador
from src.domain.actors.administrador import Administrador
from src.domain.domain_entities.padrino import Padrino
from src.application.use_cases.CU03_Admin_GestionarVinculaciones import GestionarVinculacionesUseCase


class TestCU03GestionarVinculaciones(unittest.TestCase):
    def setUp(self):
        self.becario_repo = MagicMock()
        self.usuario_repo = MagicMock()
        self.padrino_repo = MagicMock()
        
        self.use_case = GestionarVinculacionesUseCase(
            self.becario_repo, self.usuario_repo, self.padrino_repo
        )
        
        self.admin = Administrador(
            id_usuario="admin-1", nombre="A", apellido="B", email="e",
            telefono="1", edad=30, sexo="M", direccion="D", rol="administrador"
        )
        
        self.becario = Becario(
            id_usuario="bec-1", nombre="A", apellido="B", email="e",
            telefono="1", edad=20, sexo="F", direccion="D", rol="becario"
        )

    def test_asignar_tutor_exito(self):
        tutor = Tutor(
            id_usuario="tut-1", nombre="A", apellido="B", email="e",
            telefono="1", edad=30, sexo="M", direccion="D", rol="tutor"
        )
        self.becario_repo.obtener_por_id.return_value = self.becario
        self.usuario_repo.obtener_por_id.return_value = tutor
        
        self.use_case.asignar_vinculo(self.admin, "bec-1", "tutor", "tut-1")
        
        self.assertEqual(self.becario.puntero_tutor, tutor)
        self.becario_repo.guardar.assert_called_with(self.becario)

    def test_asignar_tutor_error_de_rol(self):
        # Tratar de asignar a alguien que es mediador en la ranura de tutor
        mediador_infiltrado = Mediador(
            id_usuario="med-1", nombre="A", apellido="B", email="e",
            telefono="1", edad=30, sexo="M", direccion="D", rol="mediador"
        )
        self.becario_repo.obtener_por_id.return_value = self.becario
        self.usuario_repo.obtener_por_id.return_value = mediador_infiltrado
        
        with self.assertRaises(ValueError) as ctx:
            self.use_case.asignar_vinculo(self.admin, "bec-1", "tutor", "med-1")
            
        self.assertIn("no pertenece a un Tutor válido", str(ctx.exception))
        self.assertIsNone(self.becario.puntero_tutor)
        self.becario_repo.guardar.assert_not_called()

    def test_desasignar_mediador(self):
        mediador = Mediador(
            id_usuario="med-1", nombre="A", apellido="B", email="e",
            telefono="1", edad=30, sexo="M", direccion="D", rol="mediador"
        )
        self.becario.puntero_mediador = mediador
        
        self.becario_repo.obtener_por_id.return_value = self.becario
        
        self.use_case.desasignar_vinculo(self.admin, "bec-1", "mediador")
        
        self.assertIsNone(self.becario.puntero_mediador)
        self.becario_repo.guardar.assert_called_with(self.becario)

    def test_seguridad_rol_incorrecto(self):
        tutor_hacker = Tutor(
            id_usuario="tut-99", nombre="A", apellido="B", email="e",
            telefono="1", edad=30, sexo="M", direccion="D", rol="tutor"
        )
        
        with self.assertRaises(PermissionError):
            self.use_case.asignar_vinculo(tutor_hacker, "bec-1", "padrino", "pad-1")


if __name__ == "__main__":
    unittest.main()
