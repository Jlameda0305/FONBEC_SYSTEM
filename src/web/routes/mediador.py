"""
Mediador HTTP Controller (Flask Blueprint).
Acts as a pure adapter between the HTTP layer and the Mediador Application Use Cases.
"""

from flask import Blueprint, g, render_template, request, redirect, url_for, flash

from src.web.auth_utils import requiere_rol
from src.application.use_cases.CU08_Mediador_AuditarDatosAcademicos import AuditarDatosAcademicosUseCase
from src.application.use_cases.CU05_Mediador_ListarBecarios import ListarBecariosMediadorUseCase
from src.application.use_cases.CU06_Mediador_ObtenerDatosBecario import ObtenerDatosBecarioUseCase
from src.infrastructure.repositories import SQLAlchemyMediadorRepository

mediador_bp = Blueprint("mediador", __name__, url_prefix="/mediador")


@mediador_bp.route("/", methods=["GET"])
@requiere_rol("mediador")
def index():
    """Redirects base /mediador to the dashboard."""
    return redirect(url_for("mediador.dashboard"))


@mediador_bp.route("/dashboard", methods=["GET"])
@requiere_rol("mediador")
def dashboard():
    """
    GET /mediador/dashboard
    
    Renders the main dashboard for the Mediador. 
    """
    # En el MVP se renderiza la vista de construcción para envíos de cartas
    return render_template("mediador/dashboard.html")

@mediador_bp.route("/mis-becarios", methods=["GET"])
@requiere_rol("mediador")
def mis_becarios():
    """
    GET /mediador/mis-becarios
    
    Renders the list of assigned Becarios via CU05.
    """
    user_id = g.usuario_actual.id_usuario
    busqueda = request.args.get("busqueda", "")
    
    repo = SQLAlchemyMediadorRepository(g.db_session)
    use_case = ListarBecariosMediadorUseCase(repo)
    
    try:
        becarios_list = use_case.execute(user_id, busqueda=busqueda)
    except ValueError as e:
        flash(str(e), "error")
        becarios_list = []
        
    return render_template("mediador/mis_becarios.html", becarios=becarios_list, busqueda=busqueda)


@mediador_bp.route("/becario/<id_usuario>", methods=["GET"])
@requiere_rol("mediador")
def becario_detalle(id_usuario):
    """
    GET /mediador/becario/<id_usuario>
    
    Loads the detailed profile of the assigned Becario (CU06).
    """
    user_id = g.usuario_actual.id_usuario
    repo = SQLAlchemyMediadorRepository(g.db_session)
    use_case = ObtenerDatosBecarioUseCase(repo)
    
    try:
        datos = use_case.execute(user_id, id_usuario)
    except ValueError as e:
        flash(str(e), "error")
        return redirect(url_for("mediador.dashboard"))
        
    return render_template("shared/becario_detalle.html", datos=datos, id_usuario=id_usuario)


@mediador_bp.route("/becario/<id_becario>/auditoria", methods=["POST"])
@requiere_rol("mediador")
def procesar_auditoria_academica(id_becario):
    """
    POST /mediador/becario/<id_becario>/auditoria
    
    Processes the auditing decision (Aprobar/Rechazar) from the Mediador (CU08).
    """
    id_mediador = g.usuario_actual.id_usuario
    decision = request.form.get("decision")
    observaciones = request.form.get("observaciones", "")
    
    repo = SQLAlchemyMediadorRepository(g.db_session)
    use_case = AuditarDatosAcademicosUseCase(repo)
    
    try:
        use_case.execute(id_mediador, id_becario, decision, observaciones)
        if decision == "aprobar":
            flash("Información académica aprobada correctamente.", "success")
        else:
            flash("Se han solicitado modificaciones al becario.", "success")
    except ValueError as e:
        flash(str(e), "error")
        
    return redirect(url_for("mediador.dashboard"))
