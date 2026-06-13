import unittest
from flask import g
from src.web.app import create_app
from src.infrastructure.database import SessionLocal, init_db

class TestWebPadrinos(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.client = cls.app.test_client()

    def setUp(self):
        with self.app.app_context():
            init_db()

    def test_listar_padrinos(self):
        with self.client.session_transaction() as sess:
            sess["user_id"] = "admin-001"
        response = self.client.get("/admin/padrinos")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Listado de Padrinos", response.data)

    def test_nuevo_padrino_get(self):
        with self.client.session_transaction() as sess:
            sess["user_id"] = "admin-001"
        response = self.client.get("/admin/padrinos/nuevo")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Registrar Nuevo Padrino", response.data)

if __name__ == "__main__":
    unittest.main()
