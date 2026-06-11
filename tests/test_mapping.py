"""
Tests for the infrastructure mapping configuration.
Ensures that all imperative mappings are valid and don't throw SQLAlchemy errors.
"""

import unittest
from sqlalchemy.orm import clear_mappers

from src.infrastructure.mapping import iniciar_mapeo
from src.infrastructure.schema import metadata


class TestMapping(unittest.TestCase):
    def setUp(self):
        # Ensure clean state before each test
        clear_mappers()
        import src.infrastructure.mapping
        src.infrastructure.mapping._mapped = False

    def tearDown(self):
        # Clean up mappers after each test
        clear_mappers()
        import src.infrastructure.mapping
        src.infrastructure.mapping._mapped = False

    def test_iniciar_mapeo_executes_without_errors(self):
        """
        iniciar_mapeo() should map all domain entities to their tables without raising
        ArgumentError or ConfigurationError from SQLAlchemy.
        """
        try:
            iniciar_mapeo()
        except Exception as e:
            self.fail(f"iniciar_mapeo() raised an exception unexpectedly: {e}")

        # Verify that all expected tables are in metadata
        expected_tables = {
            "padrinos", "tutores", "mediadores", "becarios",
            "datos_academicos", "documentos_academicos", "tutorias", "envios_cartas"
        }
        self.assertEqual(expected_tables, set(metadata.tables.keys()))
