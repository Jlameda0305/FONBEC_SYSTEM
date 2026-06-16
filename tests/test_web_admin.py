import unittest
from unittest.mock import patch, MagicMock
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

    @patch('src.infrastructure.repositories.SQLAlchemyUsuarioRepository')
    def test_acceso_denegado_becario(self, mock_repo_class):
        # Force user bec-002 (a becario)
        mock_repo = MagicMock()
        mock_user = MagicMock()
        mock_user.rol = "becario"
        mock_repo.obtener_por_id_y_rol.return_value = mock_user
        mock_repo_class.return_value = mock_repo

        with self.client.session_transaction() as sess:
            sess["user_id"] = "bec-002"
            sess["rol"] = "becario"
        response = self.client.get("/admin/dashboard")
        self.assertEqual(response.status_code, 403)

    @patch('src.infrastructure.repositories.SQLAlchemyUsuarioRepository')
    def test_acceso_concedido_administrador(self, mock_repo_class):
        mock_repo = MagicMock()
        mock_user = MagicMock()
        mock_user.rol = "administrador"
        mock_repo.obtener_por_id_y_rol.return_value = mock_user
        mock_repo_class.return_value = mock_repo

        with self.client.session_transaction() as sess:
            sess["user_id"] = "admin-001"
            sess["rol"] = "administrador"
        response = self.client.get("/admin/dashboard")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Panel Principal", response.data)
        
    @patch('src.infrastructure.repositories.SQLAlchemyUsuarioRepository')
    def test_parametros_busqueda_url(self, mock_repo_class):
        mock_repo = MagicMock()
        mock_user = MagicMock()
        mock_user.rol = "administrador"
        mock_repo.obtener_por_id_y_rol.return_value = mock_user
        mock_repo_class.return_value = mock_repo

        with self.client.session_transaction() as sess:
            sess["user_id"] = "admin-001"
            sess["rol"] = "administrador"
        response = self.client.get("/admin/directorio/becario?busqueda=juan")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'value="juan"', response.data)
        
if __name__ == "__main__":
    unittest.main()

