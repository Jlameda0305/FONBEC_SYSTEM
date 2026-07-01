"""
Tutor HTTP Controller (Flask Blueprint).
Acts as a pure adapter between the HTTP layer and the Tutor Application Use Cases.
"""

from flask import Blueprint, g, render_template, request, redirect, url_for, flash

from src.web.auth_utils import requiere_rol
from src.application.use_cases.CU05_Tutor_ListarBecarios import ListarBecariosTutorUseCase
from src.application.use_cases.CU06_Tutor_ObtenerDatosBecario import ObtenerDatosBecarioUseCase
from src.infrastructure.repositories import SQLAlchemyTutorRepository

tutor_bp = Blueprint("tutor", __name__, url_prefix="/tutor")


@tutor_bp.route("/", methods=["GET"])
@requiere_rol("tutor")
def index():
    """Redirects base /tutor to the dashboard."""
    return redirect(url_for("tutor.dashboard"))


@tutor_bp.route("/dashboard", methods=["GET"])
@requiere_rol("tutor")
def dashboard():
    """
    GET /tutor/dashboard
    
    Renders the main dashboard for the Tutor. 
    """
    # Por ahora el dashboard solo mostrará las próximas tutorías
    # En el MVP esta sección se renderiza vacía
    return render_template("tutor/dashboard.html")

@tutor_bp.route("/mis-becarios", methods=["GET"])
@requiere_rol("tutor")
def mis_becarios():
    """
    GET /tutor/mis-becarios
    
    Renders the list of assigned Becarios via CU05.
    """
    user_id = g.usuario_actual.id_usuario
    busqueda = request.args.get("busqueda", "")
    
    repo = SQLAlchemyTutorRepository(g.db_session)
    use_case = ListarBecariosTutorUseCase(repo)
    
    try:
        becarios_list = use_case.execute(user_id, busqueda=busqueda)
    except ValueError as e:
        flash(str(e), "error")
        becarios_list = []
        
    return render_template("tutor/mis_becarios.html", becarios=becarios_list, busqueda=busqueda)



@tutor_bp.route("/becario/<id_usuario>", methods=["GET"])
@requiere_rol("tutor")
def becario_detalle(id_usuario):
    """
    GET /tutor/becario/<id_usuario>
    
    Loads the detailed profile of the assigned Becario (CU06).
    """
    user_id = g.usuario_actual.id_usuario
    repo = SQLAlchemyTutorRepository(g.db_session)
    use_case = ObtenerDatosBecarioUseCase(repo)
    
    try:
        datos = use_case.execute(user_id, id_usuario)
    except ValueError as e:
        flash(str(e), "error")
        return redirect(url_for("tutor.dashboard"))
        
    return render_template("shared/becario_detalle.html", datos=datos, id_usuario=id_usuario)



