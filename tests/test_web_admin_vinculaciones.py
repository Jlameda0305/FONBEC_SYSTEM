import unittest
from flask import g
from src.web.app import create_app
from src.infrastructure.database import SessionLocal, init_db
from src.domain.actors.becario import Becario
from src.domain.actors.administrador import Administrador

class TestWebAdminVinculaciones(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.client = cls.app.test_client()

    def setUp(self):
        with self.app.app_context():
            init_db()
            self.session = SessionLocal()
            # Seed un admin y un becario
            admin = Administrador(id_usuario="admin-test", nombre="A", apellido="A", email="a@a.com", telefono="1", edad=30, sexo="M", direccion="D", password_hash="H", rol="administrador")
            becario = Becario(id_usuario="bec-test", nombre="B", apellido="B", email="b@b.com", telefono="1", edad=20, sexo="M", direccion="D", password_hash="H", rol="becario")
            self.session.add(admin)
            self.session.add(becario)
            self.session.commit()

    def tearDown(self):
        with self.app.app_context():
            self.session.query(Becario).filter_by(id_usuario="bec-test").delete()
            self.session.query(Administrador).filter_by(id_usuario="admin-test").delete()
            self.session.commit()
            self.session.close()

    def test_get_vinculaciones(self):
        with self.client.session_transaction() as sess:
            sess["user_id"] = "admin-test"
        response = self.client.get("/admin/becarios/bec-test/vinculaciones")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Gest", response.data)

if __name__ == "__main__":
    unittest.main()
