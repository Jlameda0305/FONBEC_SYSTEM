import os
import sys

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.infrastructure.mapping import iniciar_mapeo
from src.infrastructure.schema import metadata

# Load environment variables from .env file
load_dotenv()

# Ensure the required database URL is present
SUPABASE_DATABASE_URL = os.getenv("SUPABASE_DATABASE_URL")
if not SUPABASE_DATABASE_URL:
    print("Error: SUPABASE_DATABASE_URL no está configurada en el archivo .env", file=sys.stderr)
    sys.exit(1)

# Ensure the URL uses 'postgresql://' instead of 'postgres://' for newer SQLAlchemy compatibility
if SUPABASE_DATABASE_URL.startswith("postgres://"):
    SUPABASE_DATABASE_URL = SUPABASE_DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Create the SQLAlchemy engine
# pool_pre_ping=True helps detect stale connections to the DB
engine = create_engine(SUPABASE_DATABASE_URL, pool_pre_ping=True)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """
    Initializes the database connection by establishing the imperative mapping
    and creating all tables defined in the metadata.
    """
    try:
        # Step 1: Bind domain classes to tables
        iniciar_mapeo()
        print("✓ Mapeo imperativo completado.")
        
        # Step 2: Create all tables in the database (if they don't exist)
        metadata.create_all(bind=engine)
        print("✓ Tablas sincronizadas con Supabase.")
    except Exception as e:
        print(f"Error al inicializar la base de datos: {e}", file=sys.stderr)
        sys.exit(1)
