import unittest
from unittest.mock import MagicMock

from src.domain.models import Padrino, Administrador
from src.application.use_cases.CU04_Admin_GestionarPadrinos import GestionarPadrinosUseCase


class TestCU04GestionarPadrinos(unittest.TestCase):
    def setUp(self):
        self.mock_repo = MagicMock()
        self.use_case = GestionarPadrinosUseCase(self.mock_repo)
        
        self.admin = Administrador(
            id_usuario="admin-1", nombre="A", apellido="B", email="e",
            telefono="1", edad=30, sexo="M", direccion="D", rol="administrador"
        )
        self.otro_usuario = MagicMock()
        self.otro_usuario.rol = "becario"

    def test_crear_requiere_admin(self):
        with self.assertRaises(PermissionError):
            self.use_case.crear(self.otro_usuario, {})

    def test_crear_exito(self):
        datos = {"nombre": "Juan", "apellido": "Perez"}
        nuevo_id = self.use_case.crear(self.admin, datos)
        
        self.assertTrue(nuevo_id.startswith("pad-"))
        self.mock_repo.crear_padrino.assert_called_once()
        args, _ = self.mock_repo.crear_padrino.call_args
        padrino_creado = args[0]
        self.assertEqual(padrino_creado.nombre, "Juan")

    def test_eliminar_exito(self):
        padrino = Padrino(id_padrino="pad-1", nombre="N", apellido="A", email="e", telefono="t", direccion="d")
        self.mock_repo.obtener_padrino_por_id.return_value = padrino
        
        self.use_case.eliminar(self.admin, "pad-1")
        self.mock_repo.eliminar_padrino.assert_called_with("pad-1")

    def test_eliminar_inexistente(self):
        self.mock_repo.obtener_padrino_por_id.return_value = None
        with self.assertRaises(ValueError):
            self.use_case.eliminar(self.admin, "pad-1")

    def test_modificar_exito(self):
        padrino = Padrino(id_padrino="pad-1", nombre="Viejo", apellido="A", email="e", telefono="t", direccion="d")
        self.mock_repo.obtener_padrino_por_id.return_value = padrino
        
        datos_nuevos = {"nombre": "Nuevo"}
        self.use_case.modificar(self.admin, "pad-1", datos_nuevos)
        
        self.assertEqual(padrino.nombre, "Nuevo")
        self.assertEqual(padrino.apellido, "A")  # Preserved
        self.mock_repo.actualizar_padrino.assert_called_with(padrino)


if __name__ == "__main__":
    unittest.main()
