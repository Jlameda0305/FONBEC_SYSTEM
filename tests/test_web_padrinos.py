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
            from src.infrastructure.database import SessionLocal
            from src.domain.actors.administrador import Administrador
            from src.domain.actors.becario import Becario
            from src.domain.actors.tutor import Tutor
            from src.domain.actors.mediador import Mediador
            from src.domain.domain_entities.datos_academicos import DatosAcademicos
            from src.domain.enums import EstadoVerificacion
            from src.infrastructure.repositories import SQLAlchemyUsuarioRepository
            session = SessionLocal()
            repo = SQLAlchemyUsuarioRepository(session)
            try:
                repo.guardar(Administrador(id_usuario="admin-001", nombre="A", apellido="B", email="a@b.com", telefono="1", direccion="1", edad=1, sexo="M"))
                becario = Becario(id_usuario="bec-001", nombre="A", apellido="B", email="b@b.com", telefono="1", direccion="1", edad=1, sexo="M")
                becario.datos_academicos = DatosAcademicos(nombre_carrera="Ingeniería", anio_ingreso=2020, anio_en_curso=2, estado_verificacion=EstadoVerificacion.APROBADO)
                repo.guardar(becario)
                repo.guardar(Tutor(id_usuario="tut-001", nombre="A", apellido="B", email="t@b.com", telefono="1", direccion="1", edad=1, sexo="M"))
                repo.guardar(Mediador(id_usuario="med-1", nombre="A", apellido="B", email="m@b.com", telefono="1", direccion="1", edad=1, sexo="M"))
                session.commit()
            except Exception as e:
                print("DB Error:", e)
                session.rollback()
            finally:
                session.close()


    def test_listar_padrinos(self):
        with self.client.session_transaction() as sess:
            sess["user_id"] = "admin-001"
            sess["rol"] = "administrador"
        response = self.client.get("/admin/padrinos")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Listado de Padrinos", response.data)

    def test_nuevo_padrino_get(self):
        with self.client.session_transaction() as sess:
            sess["user_id"] = "admin-001"
            sess["rol"] = "administrador"
        response = self.client.get("/admin/padrinos/nuevo")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Registrar Nuevo Padrino", response.data)

if __name__ == "__main__":
    unittest.main()
