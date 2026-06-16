"""
Integration tests for the Flask Web Layer (Becario routes).

Uses Flask's test_client to verify HTTP responses and HTML content
rendered by the Jinja2 templates.
"""

import unittest
from unittest.mock import patch, MagicMock

from src.web.app import create_app


class TestWebBecarioAcademico(unittest.TestCase):
    """Tests for GET /becario/academico."""

    @classmethod
    def setUpClass(cls) -> None:
        """Create the Flask app once for all tests."""
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.client = cls.app.test_client()

    def setUp(self):
        # Set up standard session and user mock for all requests in this test
        self.patcher = patch('src.infrastructure.repositories.SQLAlchemyUsuarioRepository')
        self.mock_repo_class = self.patcher.start()
        
        self.mock_repo = MagicMock()
        self.mock_user = MagicMock()
        self.mock_user.id_usuario = "bec-002"
        self.mock_user.rol = "becario"
        # We also need the user to have valid 'datos_academicos' for the view to render properly without crashing
        self.mock_user.datos_academicos = MagicMock()
        self.mock_user.datos_academicos.nombre_carrera = "Ingeniería"
        self.mock_user.datos_academicos.anio_ingreso = 2020
        self.mock_user.datos_academicos.estado_verificacion = MagicMock(value="APROBADO")
        
        self.mock_repo.obtener_por_id_y_rol.return_value = self.mock_user
        self.mock_repo_class.return_value = self.mock_repo

    def tearDown(self):
        self.patcher.stop()

    def _get_academico(self):
        with self.client.session_transaction() as sess:
            sess["user_id"] = "bec-002"
            sess["rol"] = "becario"
        return self.client.get("/becario/academico")

    def test_ruta_retorna_200(self) -> None:
        """GET /becario/academico returns 200 OK."""
        response = self._get_academico()
        self.assertEqual(response.status_code, 200)

    def test_html_contiene_titulo(self) -> None:
        """The rendered HTML contains the page title."""
        response = self._get_academico()
        html = response.data.decode("utf-8")
        self.assertIn("Datos Académicos", html)

    def test_html_contiene_datos_del_becario(self) -> None:
        """The rendered HTML contains academic data fields structure."""
        response = self._get_academico()
        html = response.data.decode("utf-8")
        # Check that the layout renders the keys
        self.assertIn("Carrera", html)
        self.assertIn("Año de Ingreso", html)

    def test_html_contiene_estado_verificacion(self) -> None:
        """The rendered HTML contains the verification status badge."""
        response = self._get_academico()
        html = response.data.decode("utf-8")
        self.assertIn("badge", html)

    def test_html_contiene_estructura_base(self) -> None:
        """The rendered HTML extends the base template (has header, footer)."""
        response = self._get_academico()
        html = response.data.decode("utf-8")
        self.assertIn("FONBEC", html)
        self.assertIn("footer", html)


if __name__ == "__main__":
    unittest.main()

