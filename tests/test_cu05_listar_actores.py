import unittest
from unittest.mock import Mock

from src.application.use_cases.CU05_Admin_ListarActores import ListarActoresUseCase
from src.domain.actors.administrador import Administrador
from src.domain.actors.becario import Becario


class TestCU05ListarActores(unittest.TestCase):
    def setUp(self):
        self.mock_repo = Mock()
        self.use_case = ListarActoresUseCase(repositorio=self.mock_repo)
        self.admin = Administrador(
            id_usuario="admin-123",
            nombre="Admin",
            apellido="Test",
            email="admin@test.com",
            telefono="123",
            edad=30,
            sexo="M",
            direccion="Test",
            password_hash="hash"
        )
        self.becario_mock = Becario(
            id_usuario="bec-123",
            nombre="Becario",
            apellido="Test",
            email="becario@test.com",
            telefono="123",
            edad=20,
            sexo="M",
            direccion="Test",
            password_hash="hash"
        )

    def test_listar_actores_exito(self):
        # Configure mock to return one becario
        self.mock_repo.listar_usuarios.return_value = [self.becario_mock]

        # Execute use case
        resultado = self.use_case.execute(
            actor_admin=self.admin,
            tipo_actor="becario",
            pagina=2,
            limite=10
        )

        # Assert repository was called with correct offset (pagina=2, limite=10 -> offset=10)
        self.mock_repo.listar_usuarios.assert_called_once_with(
            limite=10,
            offset=10,
            rol="becario",
            busqueda=None
        )

        # Assert returned data is serialized
        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]["id_usuario"], "bec-123")

    def test_rechazar_no_administrador(self):
        # Pass a becario instead of an admin
        with self.assertRaises(PermissionError):
            self.use_case.execute(
                actor_admin=self.becario_mock,  # Not an admin
                tipo_actor="tutor"
            )

    def test_pagina_negativa_se_ajusta(self):
        self.mock_repo.listar_usuarios.return_value = []
        self.use_case.execute(self.admin, "tutor", pagina=-5, limite=20)
        
        # Pagina -5 is invalid, should default to page 1 -> offset 0
        self.mock_repo.listar_usuarios.assert_called_once_with(
            limite=20,
            offset=0,
            rol="tutor",
            busqueda=None
        )

if __name__ == "__main__":
    unittest.main()
