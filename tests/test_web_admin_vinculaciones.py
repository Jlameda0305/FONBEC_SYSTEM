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
        from src.domain.domain_entities.datos_academicos import DatosAcademicos

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

            self.session = SessionLocal()
            # Clear any leftover seed data including foreign keys
            self.session.query(DatosAcademicos).filter_by(becario_id="bec-test").delete()
            self.session.query(Becario).filter_by(id_usuario="bec-test").delete()
            self.session.query(Administrador).filter_by(id_usuario="admin-test").delete()
            self.session.commit()
            # Seed un admin y un becario
            admin = Administrador(id_usuario="admin-test", nombre="A", apellido="A", email="a@a.com", telefono="1", edad=30, sexo="M", direccion="D", rol="administrador")
            becario = Becario(id_usuario="bec-test", nombre="B", apellido="B", email="b@b.com", telefono="1", edad=20, sexo="M", direccion="D", rol="becario")
            self.session.add(admin)
            self.session.add(becario)
            self.session.commit()

    def tearDown(self):
        from src.domain.domain_entities.datos_academicos import DatosAcademicos
        with self.app.app_context():
            self.session.query(DatosAcademicos).filter_by(becario_id="bec-test").delete()
            self.session.query(Becario).filter_by(id_usuario="bec-test").delete()
            self.session.query(Administrador).filter_by(id_usuario="admin-test").delete()
            self.session.commit()
            self.session.close()

    def test_get_vinculaciones(self):
        with self.client.session_transaction() as sess:
            sess["user_id"] = "admin-test"
        response = self.client.get("/admin/becarios/bec-test/detalle")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Vinculaciones", response.data)

if __name__ == "__main__":
    unittest.main()
