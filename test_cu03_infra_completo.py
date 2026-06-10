import os
import sys
from dotenv import load_dotenv

# Ensure we can import src
sys.path.append(os.path.abspath("."))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.infrastructure.mapping import iniciar_mapeo
from src.infrastructure.repositories import SQLAlchemyBecarioRepository
from src.infrastructure.storage.supabase_storage import SupabaseStorageServiceImpl
from src.application.use_cases.CU03_LlenarActualizarFormularioAcademico import CU03_LlenarActualizarFormularioAcademico
from src.domain.models import Becario, DatosAcademicos
from src.domain.enums import EstadoVerificacion

class MockFileWithLen:
    def __init__(self, data: bytes):
        self._data = data
        self.content_length = len(data)
    
    def read(self):
        return self._data

def main():
    print("Iniciando prueba de integración CU-03...")
    load_dotenv()
    
    # 1. Setup DB
    print("Iniciando mapeo de SQLAlchemy...")
    iniciar_mapeo()
    engine = create_engine(os.environ.get("DATABASE_URL"))
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # 2. Instantiate Adapters
    repo = SQLAlchemyBecarioRepository(session)
    storage = SupabaseStorageServiceImpl()
    
    # Pre-condición: Necesitamos un becario en la BD para probar.
    becario_id = "bec-test-infra"
    becario_existente = repo.obtener_por_id(becario_id)
    if not becario_existente:
        print(f"Creando becario de prueba {becario_id}...")
        datos_acad = DatosAcademicos(estado_verificacion=EstadoVerificacion.PENDIENTE_MODIFICAR)
        nuevo_becario = Becario(
            id_usuario=becario_id,
            nombre="Juan",
            apellido="Perez",
            email="juan@ejemplo.com",
            telefono="123456789",
            edad=20,
            sexo="M",
            direccion="Calle Falsa 123",
            password_hash="fakehash",
            datos_academicos=datos_acad
        )
        session.add(nuevo_becario)
        session.commit()
        print("Becario creado.")
    else:
        # Resetear el estado para que se pueda editar
        becario_existente.datos_academicos.estado_verificacion = EstadoVerificacion.PENDIENTE_MODIFICAR
        session.commit()
        print(f"Becario {becario_id} ya existe, estado reseteado a PENDIENTE_MODIFICAR.")

    # 3. Use Case
    use_case = CU03_LlenarActualizarFormularioAcademico(repo, storage)
    
    # Mock PDF (must be valid length, simulating < 5MB)
    fake_pdf = MockFileWithLen(b"%PDF-1.4 Fake Content For Testing")
    
    datos = {
        "nombre_carrera": "Ingeniería en Sistemas (Prueba Infra)",
        "anio_ingreso": 2021,
        "anio_en_curso": 4,
        "materias_a_cursar": ["Algoritmos", "Base de Datos"],
        "materias_adeudadas": []
    }
    
    try:
        print("Ejecutando caso de uso CU-03...")
        resultado = use_case.ejecutar(
            becario_id=becario_id,
            datos=datos,
            archivos=[("certificado_alumno_regular.pdf", fake_pdf)]
        )
        print("\n¡ÉXITO! Caso de uso finalizado.")
        print("DTO Resultante:")
        print(f"  Carrera: {resultado.get('nombre_carrera')}")
        print(f"  Estado Verificación: {resultado.get('estado_verificacion')}")
        docs = resultado.get('lista_documentos') or []
        print(f"  Documentos: {len(docs)}")
        for doc in docs:
            print(f"    - {doc.get('nombre_archivo')}: {doc.get('url_archivo')}")
            
    except Exception as e:
        print(f"\nERROR durante la ejecución: {e}")
        session.rollback()

if __name__ == "__main__":
    main()
