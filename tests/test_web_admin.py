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
        # Force user bec-002 (a becario)
        response = self.client.get("/admin/dashboard?force_user=bec-002")
        self.assertEqual(response.status_code, 403)

    def test_acceso_concedido_administrador(self):
        # Default mock user is admin-001
        response = self.client.get("/admin/dashboard")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Directorio de Actores del Sistema", response.data)
        
    def test_parametros_busqueda_url(self):
        # Force admin user to override any session state from previous tests
        response = self.client.get("/admin/dashboard?busqueda=juan&filtro_rol=becario&force_user=admin-001")
        self.assertEqual(response.status_code, 200)
        # Verify the inputs retained their values
        self.assertIn(b'value="juan"', response.data)
        
if __name__ == "__main__":
    unittest.main()
