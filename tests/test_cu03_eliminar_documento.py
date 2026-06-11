"""
Unit tests for the CU03_EliminarDocumentoAcademico Use Case.
"""

import unittest
from datetime import datetime
from typing import Optional

from src.application.protocols import BecarioRepositoryProtocol, IStorageServiceProtocol
from src.application.use_cases.CU03_EliminarDocumentoAcademico import CU03_EliminarDocumentoAcademico
from src.domain.models import Becario, DocumentoAcademico


class MockFile:
    def __init__(self, size: int):
        self.content_length = size


class MockBecarioRepository(BecarioRepositoryProtocol):
    def __init__(self, becario: Optional[Becario] = None):
        self.becario = becario
        self.guardado = False

    def obtener_por_id(self, becario_id: str) -> Optional[Becario]:
        if self.becario and self.becario.id_usuario == becario_id:
            return self.becario
        return None

    def guardar(self, becario: Becario) -> None:
        self.guardado = True


class MockStorageService(IStorageServiceProtocol):
    def __init__(self, fail_on_delete: bool = False):
        self.fail_on_delete = fail_on_delete
        self.deleted: list[dict] = []

    def subir_documento(
        self,
        archivo: object,
        becario_id: str,
        tipo_documento: str,
        nombre_completo: str,
    ) -> str:
        return f"/mock/path/{becario_id}/{tipo_documento}_{nombre_completo}.pdf"

    def eliminar_documento_por_url(self, ruta_archivo: str) -> None:
        if self.fail_on_delete:
            raise Exception("Storage delete failed")
        if getattr(self, "not_found_on_delete", False):
            raise Exception("object not found")
        self.deleted.append(ruta_archivo)


def _make_becario_con_documentos() -> Becario:
    becario = Becario(
        id_usuario="bec-123",
        nombre="Test",
        apellido="User",
        email="test@example.com",
        telefono="+5491100000000",
        edad=20,
        sexo="M",
        direccion="Fake St 123",
        password_hash="hash"
    )
    becario.datos_academicos.agregar_documento(
        DocumentoAcademico(
            tipo_documento="Programa",
            ruta_archivo="/mock/path/bec-123/Programa_Test_User.pdf",
            fecha_carga=datetime(2026, 1, 15),
        )
    )
    becario.datos_academicos.agregar_documento(
        DocumentoAcademico(
            tipo_documento="CartaCompromiso",
            ruta_archivo="/mock/path/bec-123/CartaCompromiso_Test_User.pdf",
            fecha_carga=datetime(2026, 1, 15),
        )
    )
    return becario


class TestCU03EliminarDocumentoAcademico(unittest.TestCase):

    def setUp(self):
        self.becario = _make_becario_con_documentos()
        self.repo = MockBecarioRepository(self.becario)
        self.storage = MockStorageService()
        self.use_case = CU03_EliminarDocumentoAcademico(self.repo, self.storage)

    def test_eliminar_documento_exitoso(self):
        """Should remove the document from src.domain and call storage delete."""
        self.assertEqual(len(self.becario.datos_academicos.lista_documentos), 2)

        result = self.use_case.ejecutar("bec-123", "Programa")

        self.assertEqual(len(self.becario.datos_academicos.lista_documentos), 1)
        self.assertEqual(
            self.becario.datos_academicos.lista_documentos[0].tipo_documento,
            "CartaCompromiso"
        )
        self.assertTrue(self.repo.guardado)
        self.assertEqual(len(self.storage.deleted), 1)
        self.assertEqual(self.storage.deleted[0], "/mock/path/bec-123/Programa_Test_User.pdf")
        # Verify documentos map in returned DTO
        self.assertNotIn("Programa", result["documentos"])
        self.assertIn("CartaCompromiso", result["documentos"])

    def test_eliminar_documento_inexistente_lanza_error(self):
        """Should raise ValueError if no document of that type exists."""
        with self.assertRaises(ValueError) as ctx:
            self.use_case.ejecutar("bec-123", "Inscripcion")
        self.assertIn("No existe un documento", str(ctx.exception))
        self.assertFalse(self.repo.guardado)

    def test_eliminar_becario_no_encontrado(self):
        """Should raise ValueError if becario does not exist."""
        with self.assertRaises(ValueError):
            self.use_case.ejecutar("no-existe", "Programa")

    def test_eliminar_storage_falla_criticamente_aborta_operacion(self):
        """If storage delete fails with a generic error, it should abort and not touch DB."""
        self.storage.fail_on_delete = True

        with self.assertRaises(RuntimeError) as ctx:
            self.use_case.ejecutar("bec-123", "Programa")
            
        self.assertIn("Error crítico", str(ctx.exception))
        # Domain should NOT be cleaned up
        self.assertEqual(len(self.becario.datos_academicos.lista_documentos), 2)
        self.assertFalse(self.repo.guardado)

    def test_eliminar_storage_falla_not_found_continua_limpieza(self):
        """If storage reports not found, it should proceed to clean the DB."""
        self.storage.not_found_on_delete = True

        result = self.use_case.ejecutar("bec-123", "Programa")

        # Domain should still be cleaned up
        self.assertEqual(len(self.becario.datos_academicos.lista_documentos), 1)
        self.assertTrue(self.repo.guardado)


if __name__ == "__main__":
    unittest.main()
