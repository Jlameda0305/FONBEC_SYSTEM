import unittest

from flask import g
from src.web.app import create_app
from src.infrastructure.database import SessionLocal, init_db

class TestWebAdmin(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.client = cls.app.test_client()

    def setUp(self):
        with self.app.app_context():
            init_db()

    def test_acceso_denegado_becario(self):
        # The user bec-001 is injected in setUp as a becario.

        with self.client.session_transaction() as sess:
            sess["user_id"] = "bec-001"
            sess["rol"] = "becario"
        response = self.client.get("/admin/dashboard")
        self.assertEqual(response.status_code, 403)

    def test_acceso_concedido_administrador(self):
        # admin-001 is injected in setUp

        with self.client.session_transaction() as sess:
            sess["user_id"] = "admin-001"
            sess["rol"] = "administrador"
        response = self.client.get("/admin/dashboard")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Panel Principal", response.data)
        
    def test_parametros_busqueda_url(self):
        # admin-001 is injected in setUp

        with self.client.session_transaction() as sess:
            sess["user_id"] = "admin-001"
            sess["rol"] = "administrador"
        response = self.client.get("/admin/directorio/becario?busqueda=juan")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'value="juan"', response.data)
        
if __name__ == "__main__":
    unittest.main()

