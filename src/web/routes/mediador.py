"""
Mediador HTTP Controller (Flask Blueprint).
Acts as a pure adapter between the HTTP layer and the Mediador Application Use Cases.
"""

from flask import Blueprint, g, render_template, request, redirect, url_for, flash

from src.web.auth_utils import requiere_rol
from src.application.use_cases.CU08_Mediador_AuditarDatosAcademicos import AuditarDatosAcademicosUseCase
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
    # En el MVP se puede reutilizar la vista base temporalmente
    return render_template("tutor/dashboard.html")


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
