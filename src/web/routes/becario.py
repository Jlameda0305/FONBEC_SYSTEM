"""
Becario HTTP Controller (Flask Blueprint).

Acts as a pure adapter between the HTTP layer and the Application Use Cases.
Contains zero business logic — only wiring and rendering.
"""

from flask import Blueprint, g, render_template, request, redirect, url_for, flash

from src.application.mock_auth_service import obtener_usuario_actual
from src.application.use_cases.CU04_VisualizarDatosAcademicos import (
    CU04_VisualizarDatosAcademicos,
)
from src.application.use_cases.CU03_LlenarActualizarFormularioAcademico import (
    CU03_LlenarActualizarFormularioAcademico,
)
from src.infrastructure.repositories import SQLAlchemyBecarioRepository
from src.infrastructure.storage.supabase_storage import SupabaseStorageServiceImpl

becario_bp = Blueprint("becario", __name__, url_prefix="/becario")


@becario_bp.route("/academico", methods=["GET"])
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
    except ValueError as e:
        return render_template("error.html", message=str(e)), 404

    return render_template("becario/academico.html", datos=datos)

@becario_bp.route("/academico/editar", methods=["GET", "POST"])
def editar_formulario_academico():
    """
    GET /becario/academico/editar
    POST /becario/academico/editar
    
    Handles filling and updating the academic form (CU03).
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
            
            archivos = []
            file_obj = request.files.get("documento_academico")
            if file_obj and file_obj.filename:
                archivos.append((file_obj.filename, file_obj))
                
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
