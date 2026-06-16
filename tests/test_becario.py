"""
Unit tests for Becario domain entity (Aggregate Root).

Covers:
    - CU-02: Contact delegation (contacto_tutor, contacto_mediador, get_datos_contacto)
    - CU-03: llenar_actualizar_formulario_academico — state assignment
    - CU-04: visualizar_datos_academicos — state-dependent output
    - CU-03: visualizar_formulario_academico — RN-02 guard
    - CU-08: Tutor.auditar_datos_academicos_becario — approve/reject delegation
"""

import sys
import os
import unittest
from datetime import datetime

from src.domain.enums import EstadoVerificacion, NivelCursado
from src.domain.models import Becario, DatosAcademicos, DocumentoAcademico, Mediador, Tutor


def _make_usuario_kwargs(**overrides):
    """Build common keyword arguments for Usuario subclass construction."""
    defaults = {
        "id_usuario": "usr-001",
        "nombre": "Test",
        "apellido": "User",
        "email": "test@example.com",
        "telefono": "+5491100000000",
        "edad": 20,
        "sexo": "M",
        "direccion": "Calle Falsa 123",
    }
    defaults.update(overrides)
    return defaults


def _make_becario(**overrides) -> Becario:
    """Create a Becario with sensible defaults."""
    defaults = {"id_usuario": "bec-001"}
    defaults.update(overrides)
    kwargs = _make_usuario_kwargs(**defaults)
    return Becario(**kwargs)


def _make_tutor(**overrides) -> Tutor:
    """Create a Tutor with sensible defaults."""
    kwargs = _make_usuario_kwargs(
        id_usuario="tut-001",
        email="tutor@example.com",
        telefono="+5491111111111",
        **overrides,
    )
    return Tutor(**kwargs)


def _make_mediador(**overrides) -> Mediador:
    """Create a Mediador with sensible defaults."""
    kwargs = _make_usuario_kwargs(
        id_usuario="med-001",
        email="mediador@example.com",
        telefono="+5491122222222",
        **overrides,
    )
    return Mediador(**kwargs)


# ---------------------------------------------------------------------------
# CU-02: Contact Delegation
# ---------------------------------------------------------------------------

class TestContactoTutor(unittest.TestCase):
    """Becario.contacto_tutor() delegation (CU-02)."""

    def test_contacto_tutor_exitoso(self):
        """Returns Tutor contact dict when puntero_tutor is set."""
        tutor = _make_tutor()
        becario = _make_becario(puntero_tutor=tutor)
        contacto = becario.contacto_tutor()
        self.assertEqual(contacto["email"], "tutor@example.com")
        self.assertEqual(contacto["telefono"], "+5491111111111")

    def test_contacto_tutor_sin_asignar(self):
        """Raises ValueError when no Tutor is assigned."""
        becario = _make_becario()
        with self.assertRaises(ValueError) as ctx:
            becario.contacto_tutor()
        self.assertIn("tutor", str(ctx.exception).lower())


class TestContactoMediador(unittest.TestCase):
    """Becario.contacto_mediador() delegation (CU-02)."""

    def test_contacto_mediador_exitoso(self):
        """Returns Mediador contact dict when puntero_mediador is set."""
        mediador = _make_mediador()
        becario = _make_becario(puntero_mediador=mediador)
        contacto = becario.contacto_mediador()
        self.assertEqual(contacto["email"], "mediador@example.com")

    def test_contacto_mediador_sin_asignar(self):
        """Raises ValueError when no Mediador is assigned."""
        becario = _make_becario()
        with self.assertRaises(ValueError) as ctx:
            becario.contacto_mediador()
        self.assertIn("mediador", str(ctx.exception).lower())


class TestGetDatosContacto(unittest.TestCase):
    """Becario.get_datos_contacto() (CU-02)."""

    def test_retorna_email_y_telefono(self):
        """Returns a dict with email and telefono."""
        becario = _make_becario(email="bec@test.com", telefono="+549000")
        contacto = becario.get_datos_contacto()
        self.assertEqual(contacto, {"email": "bec@test.com", "telefono": "+549000"})


# ---------------------------------------------------------------------------
# CU-03: Llenar / Actualizar Formulario Académico
# ---------------------------------------------------------------------------

class TestLlenarFormularioAcademico(unittest.TestCase):
    """Becario.llenar_actualizar_formulario_academico() (CU-03)."""

    def test_formulario_completo_estado_pendiente_revision(self):
        """Complete data → estado = PENDIENTE_REVISION."""
        becario = _make_becario()
        becario.llenar_actualizar_formulario_academico({
            "nombre_carrera": "Ingeniería",
            "anio_ingreso": 2023,
            "anio_en_curso": 2,
            "materias_a_cursar": ["Matemática I"],
        })
        becario.datos_academicos.agregar_documento(DocumentoAcademico("Programa", "r.pdf", datetime.now()))
        becario.datos_academicos.agregar_documento(DocumentoAcademico("CartaCompromiso", "r.pdf", datetime.now()))
        becario.datos_academicos.agregar_documento(DocumentoAcademico("Inscripcion", "r.pdf", datetime.now()))
        self.assertEqual(
            becario.datos_academicos.estado_verificacion,
            EstadoVerificacion.PENDIENTE_REVISION,
        )

    def test_formulario_incompleto_estado_incompleto(self):
        """Partial data → estado = INCOMPLETO."""
        becario = _make_becario()
        becario.llenar_actualizar_formulario_academico({
            "nombre_carrera": "Derecho",
        })
        self.assertEqual(
            becario.datos_academicos.estado_verificacion,
            EstadoVerificacion.INCOMPLETO,
        )

    def test_formulario_bloqueado_si_aprobado(self):
        """RN-02: Cannot fill form when data is APROBADO."""
        becario = _make_becario()
        becario.datos_academicos.estado_verificacion = EstadoVerificacion.APROBADO
        with self.assertRaises(ValueError):
            becario.llenar_actualizar_formulario_academico({
                "nombre_carrera": "Otra Carrera",
            })

    def test_formulario_tipos_invalidos_lanza_error(self):
        """Invalid types should raise TypeError."""
        becario = _make_becario()
        with self.assertRaises(TypeError):
            becario.llenar_actualizar_formulario_academico({"anio_ingreso": "2020"})  # str instead of int
            
    def test_formulario_anio_futuro_lanza_error(self):
        """Year beyond current year should raise ValueError."""
        becario = _make_becario()
        future_year = datetime.now().year + 5
        with self.assertRaises(ValueError):
            becario.llenar_actualizar_formulario_academico({"anio_ingreso": future_year})

    def test_agregar_documento_exitoso(self):
        """Should add DocumentoAcademico when not APROBADO."""
        becario = _make_becario()
        doc = DocumentoAcademico("Test", "ruta/test.pdf", datetime.now())
        becario.datos_academicos.agregar_documento(doc)
        self.assertEqual(len(becario.datos_academicos.lista_documentos), 1)
        
    def test_agregar_documento_bloqueado_si_aprobado(self):
        """RN-02: Cannot add document when APROBADO."""
        becario = _make_becario()
        becario.datos_academicos.estado_verificacion = EstadoVerificacion.APROBADO
        doc = DocumentoAcademico("Test", "ruta/test.pdf", datetime.now())
        with self.assertRaises(ValueError):
            becario.datos_academicos.agregar_documento(doc)


# ---------------------------------------------------------------------------
# CU-04: Visualizar Datos Académicos — Becario view
# ---------------------------------------------------------------------------

class TestVisualizarDatosAcademicosBecario(unittest.TestCase):
    """Becario.visualizar_datos_academicos() (CU-04 Becario view)."""

    def test_estado_vacio_muestra_mensaje(self):
        """VACIO state shows 'llenar formulario' message."""
        becario = _make_becario()
        result = becario.visualizar_datos_academicos()
        self.assertEqual(result["estado"], "Vacio")
        self.assertIn("llenar", result.get("mensaje", "").lower())

    def test_estado_aprobado_no_tiene_opciones(self):
        """APROBADO state has no edit options."""
        becario = _make_becario()
        becario.datos_academicos.estado_verificacion = EstadoVerificacion.APROBADO
        result = becario.visualizar_datos_academicos()
        self.assertEqual(result["estado"], "Aprobado")
        self.assertEqual(result["opciones"], [])


# ---------------------------------------------------------------------------
# CU-03: Visualizar Formulario — RN-02 guard
# ---------------------------------------------------------------------------

class TestVisualizarFormularioAcademico(unittest.TestCase):
    """Becario.visualizar_formulario_academico() (CU-03 step 1)."""

    def test_formulario_accesible_en_estado_vacio(self):
        """Can access form when estado is VACIO."""
        becario = _make_becario()
        form = becario.visualizar_formulario_academico()
        self.assertIn("nombre_carrera", form)

    def test_formulario_bloqueado_en_aprobado(self):
        """RN-02: Cannot access form when APROBADO."""
        becario = _make_becario()
        becario.datos_academicos.estado_verificacion = EstadoVerificacion.APROBADO
        with self.assertRaises(ValueError):
            becario.visualizar_formulario_academico()


# ---------------------------------------------------------------------------
# CU-08: Tutor audits academic data
# ---------------------------------------------------------------------------

class TestAuditarDatosAcademicos(unittest.TestCase):
    """Tutor.auditar_datos_academicos_becario() (CU-08)."""

    def _becario_pendiente_revision(self) -> Becario:
        """Helper: create a Becario with datos in PENDIENTE_REVISION."""
        becario = _make_becario()
        becario.datos_academicos = DatosAcademicos(
            nombre_carrera="Ingeniería",
            anio_ingreso=2023,
            anio_en_curso=2,
            materias_a_cursar=["Matemática I"],
            estado_verificacion=EstadoVerificacion.PENDIENTE_REVISION,
            lista_documentos=[
                DocumentoAcademico("Programa", "r.pdf", datetime.now()),
                DocumentoAcademico("CartaCompromiso", "r.pdf", datetime.now()),
                DocumentoAcademico("Inscripcion", "r.pdf", datetime.now()),
            ]
        )
        return becario

    def test_aprobar_cambia_estado(self):
        """Approving sets estado to APROBADO."""
        tutor = _make_tutor()
        becario = self._becario_pendiente_revision()
        tutor.auditar_datos_academicos_becario(becario, "aprobar")
        self.assertEqual(
            becario.datos_academicos.estado_verificacion,
            EstadoVerificacion.APROBADO,
        )

    def test_rechazar_cambia_estado_y_guarda_observaciones(self):
        """Rejecting sets PENDIENTE_MODIFICAR and stores observaciones."""
        tutor = _make_tutor()
        becario = self._becario_pendiente_revision()
        tutor.auditar_datos_academicos_becario(
            becario, "rechazar", observaciones="Falta documento de inscripción"
        )
        self.assertEqual(
            becario.datos_academicos.estado_verificacion,
            EstadoVerificacion.PENDIENTE_MODIFICAR,
        )
        self.assertEqual(
            becario.datos_academicos.observaciones,
            "Falta documento de inscripción",
        )

    def test_aprobar_limpia_observaciones(self):
        """Approving clears any previous observaciones."""
        tutor = _make_tutor()
        becario = self._becario_pendiente_revision()
        becario.datos_academicos.observaciones = "Obs previa"
        tutor.auditar_datos_academicos_becario(becario, "aprobar")
        self.assertIsNone(becario.datos_academicos.observaciones)

    def test_decision_invalida_rechazada(self):
        """Invalid decision string raises ValueError."""
        tutor = _make_tutor()
        becario = self._becario_pendiente_revision()
        with self.assertRaises(ValueError):
            tutor.auditar_datos_academicos_becario(becario, "pendiente")

    def test_auditar_en_estado_incorrecto_rechazado(self):
        """Cannot audit when estado is not PENDIENTE_REVISION."""
        tutor = _make_tutor()
        becario = _make_becario()  # estado VACIO
        with self.assertRaises(ValueError):
            tutor.auditar_datos_academicos_becario(becario, "aprobar")


# ---------------------------------------------------------------------------
# CU-05/06: Tutor lists and selects Becarios
# ---------------------------------------------------------------------------

class TestTutorSeleccionarBecario(unittest.TestCase):
    """Tutor.seleccionar_becario() and listar_becarios_asignados() (CU-05/06)."""

    def test_listar_becarios_retorna_lista(self):
        """listar_becarios_asignados returns the lista_becarios."""
        bec1 = _make_becario(id_usuario="bec-001")
        bec2 = _make_becario(id_usuario="bec-002")
        tutor = _make_tutor(lista_becarios=[bec1, bec2])
        self.assertEqual(len(tutor.listar_becarios_asignados()), 2)

    def test_seleccionar_becario_existente(self):
        """Selects and returns the Becario with matching ID."""
        bec = _make_becario(id_usuario="bec-123")
        tutor = _make_tutor(lista_becarios=[bec])
        resultado = tutor.seleccionar_becario("bec-123")
        self.assertEqual(resultado.id_usuario, "bec-123")

    def test_seleccionar_becario_no_encontrado(self):
        """Raises ValueError if no Becario matches the ID."""
        tutor = _make_tutor(lista_becarios=[])
        with self.assertRaises(ValueError):
            tutor.seleccionar_becario("bec-999")


# ---------------------------------------------------------------------------
# CU-02: Tutor contacts Mediador through Becario
# ---------------------------------------------------------------------------

class TestTutorContactarMediador(unittest.TestCase):
    """Tutor.contactar_mediador_becario() (CU-02)."""

    def test_contactar_mediador_exitoso(self):
        """Returns Mediador contact when assigned."""
        mediador = _make_mediador()
        becario = _make_becario(puntero_mediador=mediador)
        tutor = _make_tutor()
        contacto = tutor.contactar_mediador_becario(becario)
        self.assertEqual(contacto["email"], "mediador@example.com")

    def test_contactar_mediador_sin_asignar(self):
        """Raises ValueError when Becario has no Mediador."""
        becario = _make_becario()
        tutor = _make_tutor()
        with self.assertRaises(ValueError):
            tutor.contactar_mediador_becario(becario)


if __name__ == "__main__":
    unittest.main()
