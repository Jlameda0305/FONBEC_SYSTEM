"""
Unit tests for DatosAcademicos domain entity.

Covers:
    - All 8 valid state transitions from Diag_Est_DatosA.puml
    - All invalid state transitions (must raise ValueError)
    - RN-02: actualizar_datos() guard when estado == APROBADO
    - validar_completitud() — complete vs incomplete scenarios
"""

import sys
import os
import unittest

# Add src to the path so domain can be imported directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from src.domain.enums import EstadoVerificacion
from src.domain.models import DatosAcademicos, DocumentoAcademico
from datetime import datetime


class TestTransicionesValidas(unittest.TestCase):
    """Test all valid state transitions defined in the state diagram."""

    TRANSICIONES_VALIDAS = [
        (EstadoVerificacion.VACIO, EstadoVerificacion.INCOMPLETO),
        (EstadoVerificacion.VACIO, EstadoVerificacion.PENDIENTE_REVISION),
        (EstadoVerificacion.INCOMPLETO, EstadoVerificacion.INCOMPLETO),
        (EstadoVerificacion.INCOMPLETO, EstadoVerificacion.PENDIENTE_REVISION),
        (EstadoVerificacion.PENDIENTE_REVISION, EstadoVerificacion.APROBADO),
        (EstadoVerificacion.PENDIENTE_REVISION, EstadoVerificacion.PENDIENTE_MODIFICAR),
        (EstadoVerificacion.PENDIENTE_MODIFICAR, EstadoVerificacion.INCOMPLETO),
        (EstadoVerificacion.PENDIENTE_MODIFICAR, EstadoVerificacion.PENDIENTE_REVISION),
    ]

    def test_transiciones_validas(self):
        """Each valid transition should succeed without raising."""
        for origen, destino in self.TRANSICIONES_VALIDAS:
            with self.subTest(origen=origen.value, destino=destino.value):
                datos = DatosAcademicos(estado_verificacion=origen)
                datos.actualizar_estado(destino)
                self.assertEqual(datos.estado_verificacion, destino)


class TestTransicionesInvalidas(unittest.TestCase):
    """Test all invalid state transitions — must raise ValueError."""

    TODOS_LOS_ESTADOS = list(EstadoVerificacion)

    def test_aprobado_es_terminal(self):
        """APROBADO must not transition to any state (RN-02)."""
        datos = DatosAcademicos(estado_verificacion=EstadoVerificacion.APROBADO)
        for destino in self.TODOS_LOS_ESTADOS:
            with self.subTest(destino=destino.value):
                with self.assertRaises(ValueError):
                    datos.actualizar_estado(destino)

    def test_vacio_no_puede_ir_a_aprobado(self):
        """VACIO → APROBADO is not a valid transition."""
        datos = DatosAcademicos(estado_verificacion=EstadoVerificacion.VACIO)
        with self.assertRaises(ValueError):
            datos.actualizar_estado(EstadoVerificacion.APROBADO)

    def test_vacio_no_puede_ir_a_pendiente_modificar(self):
        """VACIO → PENDIENTE_MODIFICAR is not a valid transition."""
        datos = DatosAcademicos(estado_verificacion=EstadoVerificacion.VACIO)
        with self.assertRaises(ValueError):
            datos.actualizar_estado(EstadoVerificacion.PENDIENTE_MODIFICAR)

    def test_incompleto_no_puede_ir_a_aprobado(self):
        """INCOMPLETO → APROBADO is not a valid transition."""
        datos = DatosAcademicos(estado_verificacion=EstadoVerificacion.INCOMPLETO)
        with self.assertRaises(ValueError):
            datos.actualizar_estado(EstadoVerificacion.APROBADO)

    def test_pendiente_revision_no_puede_ir_a_vacio(self):
        """PENDIENTE_REVISION → VACIO is not a valid transition."""
        datos = DatosAcademicos(estado_verificacion=EstadoVerificacion.PENDIENTE_REVISION)
        with self.assertRaises(ValueError):
            datos.actualizar_estado(EstadoVerificacion.VACIO)


class TestValidarCompletitud(unittest.TestCase):
    """Test validar_completitud() determines correct state readiness."""

    def test_datos_completos(self):
        """All required fields present → returns True."""
        datos = DatosAcademicos(
            nombre_carrera="Ingeniería en Sistemas",
            anio_ingreso=2023,
            anio_en_curso=2,
            materias_a_cursar=["Matemática I", "Programación"],
            lista_documentos=[
                DocumentoAcademico("Programa", "r.pdf", datetime.now()),
                DocumentoAcademico("CartaCompromiso", "r.pdf", datetime.now()),
                DocumentoAcademico("Inscripcion", "r.pdf", datetime.now()),
            ]
        )
        self.assertTrue(datos.validar_completitud())

    def test_falta_nombre_carrera(self):
        """Missing nombre_carrera → returns False."""
        datos = DatosAcademicos(
            anio_ingreso=2023,
            anio_en_curso=2,
            materias_a_cursar=["Matemática I"],
        )
        self.assertFalse(datos.validar_completitud())

    def test_falta_anio_ingreso(self):
        """Missing anio_ingreso → returns False."""
        datos = DatosAcademicos(
            nombre_carrera="Ingeniería",
            anio_en_curso=2,
            materias_a_cursar=["Matemática I"],
        )
        self.assertFalse(datos.validar_completitud())

    def test_falta_anio_en_curso(self):
        """Missing anio_en_curso → returns False."""
        datos = DatosAcademicos(
            nombre_carrera="Ingeniería",
            anio_ingreso=2023,
            materias_a_cursar=["Matemática I"],
        )
        self.assertFalse(datos.validar_completitud())

    def test_materias_vacias(self):
        """Empty materias_a_cursar list → returns False."""
        datos = DatosAcademicos(
            nombre_carrera="Ingeniería",
            anio_ingreso=2023,
            anio_en_curso=2,
            materias_a_cursar=[],
        )
        self.assertFalse(datos.validar_completitud())

    def test_datos_vacios_por_defecto(self):
        """Default DatosAcademicos (all None/empty) → returns False."""
        datos = DatosAcademicos()
        self.assertFalse(datos.validar_completitud())


class TestActualizarDatos(unittest.TestCase):
    """Test actualizar_datos() guards and field updates."""

    def test_rn02_bloquea_modificacion_aprobado(self):
        """RN-02: Cannot modify data when estado is APROBADO."""
        datos = DatosAcademicos(estado_verificacion=EstadoVerificacion.APROBADO)
        with self.assertRaises(ValueError) as ctx:
            datos.actualizar_datos(nombre_carrera="Nueva Carrera")
        self.assertIn("aprobados", str(ctx.exception).lower())

    def test_actualizar_campo_valido(self):
        """Valid field update on non-approved data succeeds."""
        datos = DatosAcademicos(estado_verificacion=EstadoVerificacion.VACIO)
        datos.actualizar_datos(nombre_carrera="Ingeniería en Sistemas")
        self.assertEqual(datos.nombre_carrera, "Ingeniería en Sistemas")

    def test_actualizar_multiples_campos(self):
        """Multiple fields can be updated at once."""
        datos = DatosAcademicos(estado_verificacion=EstadoVerificacion.INCOMPLETO)
        datos.actualizar_datos(
            nombre_carrera="Derecho",
            anio_ingreso=2024,
            materias_a_cursar=["Civil I"],
        )
        self.assertEqual(datos.nombre_carrera, "Derecho")
        self.assertEqual(datos.anio_ingreso, 2024)
        self.assertEqual(datos.materias_a_cursar, ["Civil I"])

    def test_campo_no_permitido_rechazado(self):
        """Unknown field names raise AttributeError."""
        datos = DatosAcademicos(estado_verificacion=EstadoVerificacion.VACIO)
        with self.assertRaises(AttributeError):
            datos.actualizar_datos(campo_inventado="valor")


class TestAgregarDocumentoUpsert(unittest.TestCase):
    """Test agregar_documento() upsert semantics."""

    def test_agregar_documento_nuevo(self):
        """Adding a new tipo_documento appends to the list."""
        datos = DatosAcademicos()
        doc = DocumentoAcademico("Programa", "/path/prog.pdf", datetime(2026, 1, 1))
        datos.agregar_documento(doc)
        self.assertEqual(len(datos.lista_documentos), 1)

    def test_agregar_documento_mismo_tipo_reemplaza(self):
        """Adding a document with the same tipo_documento replaces it."""
        datos = DatosAcademicos()
        doc1 = DocumentoAcademico("Programa", "/path/v1.pdf", datetime(2026, 1, 1))
        doc2 = DocumentoAcademico("Programa", "/path/v2.pdf", datetime(2026, 6, 1))
        datos.agregar_documento(doc1)
        datos.agregar_documento(doc2)
        self.assertEqual(len(datos.lista_documentos), 1)
        self.assertEqual(datos.lista_documentos[0].ruta_archivo, "/path/v2.pdf")

    def test_agregar_tipos_distintos_no_reemplaza(self):
        """Adding different tipo_documento values appends each."""
        datos = DatosAcademicos()
        datos.agregar_documento(
            DocumentoAcademico("Programa", "/p1.pdf", datetime(2026, 1, 1))
        )
        datos.agregar_documento(
            DocumentoAcademico("CartaCompromiso", "/p2.pdf", datetime(2026, 1, 1))
        )
        self.assertEqual(len(datos.lista_documentos), 2)

    def test_agregar_bloqueado_en_aprobado(self):
        """RN-02: Cannot add documents when APROBADO."""
        datos = DatosAcademicos(estado_verificacion=EstadoVerificacion.APROBADO)
        doc = DocumentoAcademico("Programa", "/path.pdf", datetime(2026, 1, 1))
        with self.assertRaises(ValueError):
            datos.agregar_documento(doc)


class TestEliminarDocumento(unittest.TestCase):
    """Test eliminar_documento() domain method."""

    def setUp(self):
        self.datos = DatosAcademicos()
        self.datos.agregar_documento(
            DocumentoAcademico("Programa", "/p1.pdf", datetime(2026, 1, 1))
        )
        self.datos.agregar_documento(
            DocumentoAcademico("CartaCompromiso", "/p2.pdf", datetime(2026, 1, 1))
        )

    def test_eliminar_existente(self):
        """Removing an existing tipo_documento reduces the list."""
        self.datos.eliminar_documento("Programa")
        self.assertEqual(len(self.datos.lista_documentos), 1)
        self.assertEqual(self.datos.lista_documentos[0].tipo_documento, "CartaCompromiso")

    def test_eliminar_inexistente_lanza_error(self):
        """Removing a non-existent tipo_documento raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            self.datos.eliminar_documento("Inscripcion")
        self.assertIn("No existe un documento", str(ctx.exception))

    def test_eliminar_bloqueado_en_aprobado(self):
        """RN-02: Cannot remove documents when APROBADO."""
        self.datos.estado_verificacion = EstadoVerificacion.APROBADO
        with self.assertRaises(ValueError):
            self.datos.eliminar_documento("Programa")


class TestToDictConDocumentos(unittest.TestCase):
    """Test to_dict() includes the documentos map."""

    def test_to_dict_sin_documentos(self):
        """Empty lista_documentos produces an empty documentos dict."""
        datos = DatosAcademicos()
        result = datos.to_dict()
        self.assertIn("documentos", result)
        self.assertEqual(result["documentos"], {})

    def test_to_dict_con_documentos(self):
        """Documents are serialized as a map keyed by tipo_documento."""
        datos = DatosAcademicos()
        datos.agregar_documento(
            DocumentoAcademico("Programa", "/p1.pdf", datetime(2026, 1, 15))
        )
        datos.agregar_documento(
            DocumentoAcademico("Inscripcion", "/p2.pdf", datetime(2026, 6, 1))
        )
        result = datos.to_dict()
        self.assertIn("Programa", result["documentos"])
        self.assertIn("Inscripcion", result["documentos"])
        self.assertEqual(result["documentos"]["Programa"]["ruta_archivo"], "/p1.pdf")


if __name__ == "__main__":
    unittest.main()
