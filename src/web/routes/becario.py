"""
Becario HTTP Controller (Flask Blueprint).

Acts as a pure adapter between the HTTP layer and the Application Use Cases.
Contains zero business logic — only wiring and rendering.
"""

from flask import Blueprint, g, render_template, request, redirect, url_for, flash
from src.web.auth_utils import requiere_rol

from src.web.mock_auth_service import obtener_usuario_actual
from src.application.use_cases.CU04_VisualizarDatosAcademicos import (
    CU04_VisualizarDatosAcademicos,
)
from src.application.use_cases.CU03_LlenarActualizarFormularioAcademico import (
    CU03_LlenarActualizarFormularioAcademico,
)
from src.application.use_cases.CU03_EliminarDocumentoAcademico import (
    CU03_EliminarDocumentoAcademico,
)
from src.application.use_cases.CU02_ContactarReferente import (
    ObtenerDatosReferentesUseCase,
)
from src.infrastructure.repositories import SQLAlchemyBecarioRepository
from src.infrastructure.storage.supabase_storage import SupabaseStorageServiceImpl

# Explicit document type keys — order matches the UI fields
TIPOS_DOCUMENTO = ["Programa", "CartaCompromiso", "Inscripcion"]

becario_bp = Blueprint("becario", __name__, url_prefix="/becario")


@becario_bp.route("/", methods=["GET"])
@requiere_rol("becario")
def index():
    """Redirects base /becario to the dashboard."""
    return redirect(url_for("becario.dashboard"))


@becario_bp.route("/dashboard", methods=["GET"])
@requiere_rol("becario")
def dashboard():
    """
    GET /becario/dashboard
    
    Renders the main dashboard. Retrieves the referentes data (Tutor, Mediador, Padrino)
    via CU02.
    """
    user_id = obtener_usuario_actual()
    repo = SQLAlchemyBecarioRepository(g.db_session)
    use_case = ObtenerDatosReferentesUseCase(repo)
    
    try:
        referentes = use_case.execute(user_id)
    except ValueError as e:
        flash(str(e), "error")
        referentes = {"tutor": None, "mediador": None, "padrino": None}
        
    return render_template("becario/dashboard.html", referentes=referentes)


@becario_bp.route("/academico", methods=["GET"])
@requiere_rol("becario")
def visualizar_academico():
    """
    GET /becario/academico

    Wires the infrastructure repository and application use case,
    executes CU04, and renders the academic data view.
    """
    # 1. Resolve the authenticated user (mock for now)
    user_id = obtener_usuario_actual()

    # 2. Instantiate Infrastructure + Application layers via DI
    repo = SQLAlchemyBecarioRepository(g.db_session)
    use_case = CU04_VisualizarDatosAcademicos(repo)

    # 3. Execute the Use Case
    try:
        datos = use_case.ejecutar(user_id)
        
        # Obtener referentes (Tutor y Mediador)
        use_case_ref = ObtenerDatosReferentesUseCase(repo)
        referentes = use_case_ref.execute(user_id)
        
    except ValueError as e:
        return render_template("error.html", message=str(e)), 404

    return render_template("becario/academico.html", datos=datos, referentes=referentes)

@becario_bp.route("/academico/editar", methods=["GET", "POST"])
@requiere_rol("becario")
def editar_formulario_academico():
    """
    GET /becario/academico/editar
    POST /becario/academico/editar
    
    Handles filling and updating the academic form (CU03).
    Reads three explicit file inputs: Programa, CartaCompromiso, Inscripcion.
    """
    user_id = obtener_usuario_actual()
    repo = SQLAlchemyBecarioRepository(g.db_session)
    storage = SupabaseStorageServiceImpl()
    
    if request.method == "POST":
        # Extraer y transformar datos
        try:
            anio_ingreso_raw = request.form.get("anio_ingreso")
            anio_en_curso_raw = request.form.get("anio_en_curso")
            
            datos = {
                "nombre_carrera": request.form.get("nombre_carrera"),
                "anio_ingreso": int(anio_ingreso_raw) if anio_ingreso_raw else None,
                "anio_en_curso": int(anio_en_curso_raw) if anio_en_curso_raw else None,
                "materias_a_cursar": [m.strip() for m in request.form.get("materias_a_cursar", "").split(",") if m.strip()],
                "materias_adeudadas": [m.strip() for m in request.form.get("materias_adeudadas", "").split(",") if m.strip()]
            }
            
            # Collect files from explicit per-type inputs
            archivos = []
            for tipo in TIPOS_DOCUMENTO:
                file_obj = request.files.get(tipo)
                if file_obj and file_obj.filename:
                    archivos.append((tipo, file_obj))
                
            use_case = CU03_LlenarActualizarFormularioAcademico(repo, storage)
            use_case.ejecutar(user_id, datos, archivos)
            
            flash("Formulario actualizado con éxito.", "success")
            return redirect(url_for("becario.visualizar_academico"))
            
        except (ValueError, TypeError) as e:
            flash(str(e), "error")
            # Fall through to GET logic to re-render form with errors
            
    # GET logic or failed POST fall-through
    cu04 = CU04_VisualizarDatosAcademicos(repo)
    try:
        datos_actuales = cu04.ejecutar(user_id)
    except ValueError:
        datos_actuales = {}
        
    return render_template("becario/formulario.html", datos=datos_actuales)


@becario_bp.route("/academico/documento/eliminar", methods=["POST"])
@requiere_rol("becario")
def eliminar_documento_academico():
    """
    POST /becario/academico/documento/eliminar

    Deletes a specific academic document by its tipo_documento key.
    Expects form field 'tipo_documento' with one of:
        Programa, CartaCompromiso, Inscripcion.
    """
    user_id = obtener_usuario_actual()
    tipo_documento = request.form.get("tipo_documento", "").strip()

    if tipo_documento not in TIPOS_DOCUMENTO:
        flash(f"Tipo de documento inválido: '{tipo_documento}'.", "error")
        return redirect(url_for("becario.editar_formulario_academico"))

    repo = SQLAlchemyBecarioRepository(g.db_session)
    storage = SupabaseStorageServiceImpl()

    try:
        use_case = CU03_EliminarDocumentoAcademico(repo, storage)
        use_case.ejecutar(user_id, tipo_documento)
        flash(f"Documento '{tipo_documento}' eliminado con éxito.", "success")
    except ValueError as e:
        flash(str(e), "error")

    return redirect(url_for("becario.editar_formulario_academico"))

