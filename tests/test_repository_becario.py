from src.application.dto_mapper import usuario_to_dict, datos_academicos_to_dict
"""
Integration tests for SQLAlchemyBecarioRepository.

These tests connect to the real Supabase database to verify that
the repository correctly fetches and hydrates domain entities.
Requires SUPABASE_DATABASE_URL to be configured in .env.
"""

import unittest

from src.infrastructure.database import SessionLocal, init_db
from src.infrastructure.repositories import SQLAlchemyBecarioRepository


class TestSQLAlchemyBecarioRepository(unittest.TestCase):
    """Integration tests against the live database."""

    @classmethod
    def setUpClass(cls) -> None:
        """Initialize the mapping and database connection once for all tests."""
        try:
            init_db()
        except SystemExit:
            # init_db already ran in a previous test module (mapping test)
            pass

    def setUp(self) -> None:
        """Open a fresh session for each test."""
        self.session = SessionLocal()
        self.repo = SQLAlchemyBecarioRepository(self.session)

    def tearDown(self) -> None:
        """Close the session after each test."""
        self.session.close()

    def test_obtener_becario_existente(self) -> None:
        """Fetching an existing becario returns a hydrated Becario instance."""
        becario = self.repo.obtener_por_id("bec-001")
        self.assertIsNotNone(becario)
        self.assertEqual(becario.id_usuario, "bec-001")
        self.assertEqual(becario.nombre, "Ana")
        self.assertEqual(becario.apellido, "Lopez")

    def test_datos_academicos_cargados(self) -> None:
        """The datos_academicos composition is eagerly loaded (not None)."""
        becario = self.repo.obtener_por_id("bec-001")
        self.assertIsNotNone(becario)
        self.assertIsNotNone(becario.datos_academicos)
        # Verify the estado_verificacion is a valid enum value
        self.assertIsNotNone(becario.datos_academicos.estado_verificacion)

    def test_to_dict_funciona_fuera_de_sesion(self) -> None:
        """to_dict() works even after the session is closed (eager loading proof)."""
        becario = self.repo.obtener_por_id("bec-001")
        self.assertIsNotNone(becario)
        # Close the session to simulate real Use Case boundary
        self.session.close()
        # This would throw DetachedInstanceError if lazy loading was used
        dto = datos_academicos_to_dict(becario.datos_academicos)
        self.assertIsInstance(dto, dict)
        self.assertIn("estado_verificacion", dto)

    def test_obtener_becario_inexistente(self) -> None:
        """Fetching a non-existing becario returns None."""
        becario = self.repo.obtener_por_id("bec-999-inexistente")
        self.assertIsNone(becario)


if __name__ == "__main__":
    unittest.main()
