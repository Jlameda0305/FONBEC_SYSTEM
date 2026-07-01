import unittest
from datetime import datetime

from src.application.use_cases.CU08_Mediador_AuditarDatosAcademicos import AuditarDatosAcademicosUseCase
from src.application.protocols import MediadorRepositoryProtocol
from src.domain.actors.mediador import Mediador
from src.domain.actors.becario import Becario
from src.domain.enums import EstadoVerificacion
from src.domain.domain_entities.datos_academicos import DatosAcademicos


class MockMediadorRepository(MediadorRepositoryProtocol):
    def __init__(self):
        self.mediadores = {}
        self.guardado_llamado = False

    def guardar(self, mediador: Mediador) -> None:
        self.mediadores[mediador.id_usuario] = mediador
        self.guardado_llamado = True

    def obtener_por_id(self, id_usuario: str) -> Mediador | None:
        return self.mediadores.get(id_usuario)

    def obtener_todos(self) -> list[Mediador]:
        return list(self.mediadores.values())


class TestAuditarDatosAcademicosUseCase(unittest.TestCase):
    def setUp(self):
        self.repo = MockMediadorRepository()
        self.use_case = AuditarDatosAcademicosUseCase(self.repo)

        # Setup Becario con datos en Pendiente de Revisión
        self.datos = DatosAcademicos(
            nombre_carrera="Ingeniería",
            anio_ingreso=2020,
            anio_en_curso=4,
            materias_a_cursar=["Física"],
            estado_verificacion=EstadoVerificacion.PENDIENTE_REVISION
        )
        self.becario = Becario(
            id_usuario="bec-1",
            nombre="Juan",
            apellido="Pérez",
            email="juan@test.com",
            telefono="1234",
            edad=20,
            sexo="M",
            direccion="Calle 123",
            datos_academicos=self.datos
        )

        # Setup Mediador
        self.mediador = Mediador(
            id_usuario="med-1",
            nombre="Ana",
            apellido="Gómez",
            email="ana@test.com",
            telefono="5678",
            edad=40,
            sexo="F",
            direccion="Av Siempre Viva",
            lista_becarios=[self.becario]
        )
        self.repo.guardar(self.mediador)
        self.repo.guardado_llamado = False

    def test_mediador_inexistente_lanza_error(self):
        with self.assertRaisesRegex(ValueError, "Mediador con ID 'med-x' no encontrado."):
            self.use_case.execute("med-x", "bec-1", "aprobar")

    def test_becario_ajeno_lanza_error(self):
        with self.assertRaisesRegex(ValueError, "No posee permisos para acceder al becario solicitado."):
            self.use_case.execute("med-1", "bec-x", "aprobar")

    def test_rechazar_sin_observaciones_lanza_error(self):
        with self.assertRaisesRegex(ValueError, "Las observaciones son obligatorias al rechazar los datos."):
            self.use_case.execute("med-1", "bec-1", "rechazar", observaciones="   ")

    def test_aprobar_cambia_estado_y_limpia_observaciones(self):
        # Primero simulamos que tenía una observación anterior y la vamos a aprobar ahora
        self.datos.observaciones = "Algo"
        self.datos.fecha_observacion = datetime.now()

        resultado = self.use_case.execute("med-1", "bec-1", "aprobar")

        self.assertEqual(resultado["estado_verificacion"], EstadoVerificacion.APROBADO.value)
        self.assertIsNone(resultado["observaciones"])
        self.assertIsNone(resultado["fecha_observacion"])
        self.assertTrue(self.repo.guardado_llamado)
        
    def test_rechazar_cambia_estado_y_registra_observacion(self):
        resultado = self.use_case.execute("med-1", "bec-1", "rechazar", observaciones="Falta firma")

        self.assertEqual(resultado["estado_verificacion"], EstadoVerificacion.PENDIENTE_MODIFICAR.value)
        self.assertEqual(resultado["observaciones"], "Falta firma")
        self.assertIsNotNone(resultado["fecha_observacion"])
        self.assertTrue(self.repo.guardado_llamado)

    def test_decision_invalida_lanza_error(self):
        with self.assertRaisesRegex(ValueError, "Decisión inválida: 'otra'. Debe ser 'aprobar' o 'rechazar'"):
            self.use_case.execute("med-1", "bec-1", "otra")

    def test_estado_invalido_lanza_error(self):
        self.datos.estado_verificacion = EstadoVerificacion.INCOMPLETO
        with self.assertRaisesRegex(ValueError, "Solo se pueden auditar datos en estado Pendiente_Revision"):
            self.use_case.execute("med-1", "bec-1", "aprobar")

if __name__ == "__main__":
    unittest.main()
