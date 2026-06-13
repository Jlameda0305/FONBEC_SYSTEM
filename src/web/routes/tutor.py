"""
Tutor HTTP Controller (Flask Blueprint).
Acts as a pure adapter between the HTTP layer and the Tutor Application Use Cases.
"""

from flask import Blueprint, g, render_template, request, redirect, url_for, flash

from src.web.auth_utils import requiere_rol
from src.web.mock_auth_service import obtener_usuario_actual  # noqa: disable=rule-2, IGNORAR REGLA 2
from src.application.use_cases.CU05_Tutor_ListarBecarios import ListarBecariosTutorUseCase
from src.application.use_cases.CU06_Tutor_ObtenerDatosBecario import ObtenerDatosBecarioUseCase
from src.application.use_cases.CU08_Tutor_AuditarDatosAcademicos import AuditarDatosAcademicosUseCase
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
    Retrieves the list of assigned Becarios via CU05.
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
    user_id = obtener_usuario_actual()
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
    user_id = obtener_usuario_actual()
    repo = SQLAlchemyTutorRepository(g.db_session)
    use_case = ObtenerDatosBecarioUseCase(repo)
    
    try:
        datos = use_case.execute(user_id, id_usuario)
    except ValueError as e:
        flash(str(e), "error")
        return redirect(url_for("tutor.dashboard"))
        
    return render_template("shared/becario_detalle.html", datos=datos, id_usuario=id_usuario)





@tutor_bp.route("/becario/<id_becario>/auditoria", methods=["POST"])
@requiere_rol("tutor")
def procesar_auditoria_academica(id_becario):
    """
    POST /tutor/becario/<id_becario>/auditoria
    
    Processes the auditing decision (Aprobar/Rechazar) from the Tutor (CU08).
    """
    id_tutor = obtener_usuario_actual()
    decision = request.form.get("decision")
    observaciones = request.form.get("observaciones", "")
    
    repo = SQLAlchemyTutorRepository(g.db_session)
    use_case = AuditarDatosAcademicosUseCase(repo)
    
    try:
        use_case.execute(id_tutor, id_becario, decision, observaciones)
        if decision == "aprobar":
            flash("Información académica aprobada correctamente.", "success")
        else:
            flash("Se han solicitado modificaciones al becario.", "success")
    except ValueError as e:
        flash(str(e), "error")
        
    return redirect(url_for("tutor.becario_detalle", id_usuario=id_becario))

