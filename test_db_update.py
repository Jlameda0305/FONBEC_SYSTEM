from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.infrastructure.mapping import iniciar_mapeo
from src.infrastructure.repositories import SQLAlchemyTutorRepository
import os
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)
session = Session()

iniciar_mapeo()

repo = SQLAlchemyTutorRepository(session)
tutor = repo.obtener_por_id("tut-001")
becario = tutor.seleccionar_becario("bec-002")
datos = becario.datos_academicos

print("Estado antes:", datos.estado_verificacion)
tutor.auditar_datos_academicos_becario(becario, "aprobar", "")
print("Estado modificado en RAM:", datos.estado_verificacion)

print("Datos in session.dirty:", datos in session.dirty)
repo.guardar(tutor)
session.commit()
print("Commit enviado.")
