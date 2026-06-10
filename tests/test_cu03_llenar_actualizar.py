"""
Unit tests for the CU03_LlenarActualizarFormularioAcademico Use Case.
"""

import sys
import os
import unittest
from typing import Optional

from src.application.protocols import BecarioRepositoryProtocol, IStorageServiceProtocol
from src.application.use_cases.CU03_LlenarActualizarFormularioAcademico import CU03_LlenarActualizarFormularioAcademico
from src.domain.models import Becario


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
    def __init__(self, fail_on_upload: bool = False):
        self.fail_on_upload = fail_on_upload

    def subir_documento(self, archivo: object, becario_id: str) -> str:
        if self.fail_on_upload:
            raise Exception("Network error simulating storage failure")
        return f"/mock/path/{becario_id}/doc.pdf"


def _make_becario() -> Becario:
    return Becario(
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


class TestCU03LlenarActualizarFormularioAcademico(unittest.TestCase):

    def setUp(self):
        self.becario = _make_becario()
        self.repo = MockBecarioRepository(self.becario)
        self.storage = MockStorageService()
        self.use_case = CU03_LlenarActualizarFormularioAcademico(self.repo, self.storage)

    def test_ejecutar_exitoso(self):
        """Should upload files, update domain, and save the aggregate."""
        archivos = [("certificado.pdf", MockFile(1024))]
        datos = {"nombre_carrera": "Abogacía"}
        
        result = self.use_case.ejecutar("bec-123", datos, archivos)
        
        self.assertTrue(self.repo.guardado)
        self.assertEqual(result["nombre_carrera"], "Abogacía")
        self.assertEqual(len(self.becario.datos_academicos.lista_documentos), 1)

    def test_fallo_formato_archivo(self):
        """Should reject non-PDF files and NOT call guardar()."""
        archivos = [("foto.jpg", MockFile(1024))]
        with self.assertRaises(ValueError) as ctx:
            self.use_case.ejecutar("bec-123", {}, archivos)
            
        self.assertIn("Solo se permiten archivos PDF", str(ctx.exception))
        self.assertFalse(self.repo.guardado)

    def test_fallo_tamanio_archivo(self):
        """Should reject files over 5MB and NOT call guardar()."""
        archivos = [("grande.pdf", MockFile(6 * 1024 * 1024))]
        with self.assertRaises(ValueError) as ctx:
            self.use_case.ejecutar("bec-123", {}, archivos)
            
        self.assertIn("supera el tamaño máximo", str(ctx.exception))
        self.assertFalse(self.repo.guardado)

    def test_rollback_si_falla_storage(self):
        """If storage fails, should raise exception and NOT call guardar()."""
        self.storage.fail_on_upload = True
        archivos = [("doc.pdf", MockFile(1024))]
        
        with self.assertRaises(Exception) as ctx:
            self.use_case.ejecutar("bec-123", {"nombre_carrera": "Medicina"}, archivos)
            
        self.assertIn("Network error", str(ctx.exception))
        self.assertFalse(self.repo.guardado)

    def test_becario_no_encontrado(self):
        """Should raise ValueError if becario does not exist."""
        with self.assertRaises(ValueError):
            self.use_case.ejecutar("no-existe", {}, [])


if __name__ == "__main__":
    unittest.main()
