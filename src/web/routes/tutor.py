"""
Tutor HTTP Controller (Flask Blueprint).
Acts as a pure adapter between the HTTP layer and the Tutor Application Use Cases.
"""

from flask import Blueprint, g, render_template, request, redirect, url_for, flash

from src.application.mock_auth_service import obtener_usuario_actual
from src.application.use_cases.CU05_Tutor_ListarBecarios import ListarBecariosTutorUseCase
from src.application.use_cases.CU06_Tutor_ObtenerDatosBecario import ObtenerDatosBecarioUseCase
from src.application.use_cases.CU08_Tutor_AuditarDatosAcademicos import AuditarDatosAcademicosUseCase
from src.infrastructure.repositories import SQLAlchemyTutorRepository

tutor_bp = Blueprint("tutor", __name__, url_prefix="/tutor")


@tutor_bp.route("/", methods=["GET"])
def index():
    """Redirects base /tutor to the dashboard."""
    return redirect(url_for("tutor.dashboard"))


@tutor_bp.route("/dashboard", methods=["GET"])
def dashboard():
    """
    GET /tutor/dashboard
    
    Renders the main dashboard for the Tutor. 
    Retrieves the list of assigned Becarios via CU05.
    """
    # Usando el mismo mock auth, aunque idealmente retornará el ID real del tutor en sesión
    # En MVP podemos hardcodear un id si no hay mock para el tutor, o usar el actual
    # Asumimos que obtener_usuario_actual() nos da el id del tutor logueado
    user_id = obtener_usuario_actual()
    
    # IMPORTANTE: Si estamos mockeando y user_id es de un becario, fallará. 
    # Usaremos "tutor-1" para el mock si user_id no funciona, pero dejamos el código real
    
    repo = SQLAlchemyTutorRepository(g.db_session)
    use_case = ListarBecariosTutorUseCase(repo)
    
    try:
        becarios_list = use_case.execute(user_id)
    except ValueError as e:
        flash(str(e), "error")
        becarios_list = []
        
    return render_template("tutor/dashboard.html", becarios=becarios_list)



@tutor_bp.route("/becario/<id_usuario>", methods=["GET"])
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
        
    return render_template("tutor/becario_detalle.html", datos=datos, id_usuario=id_usuario)


@tutor_bp.route("/becario/<id_becario>/auditoria", methods=["GET"])
def visualizar_auditoria_academica(id_becario):
    """
    GET /tutor/becario/<id_becario>/auditoria
    
    Visualizes the academic data for auditing (CU08).
    Reuses CU06 to obtain the basic data wrapper.
    """
    id_tutor = obtener_usuario_actual()
    repo = SQLAlchemyTutorRepository(g.db_session)
    use_case = ObtenerDatosBecarioUseCase(repo)
    
    try:
        # CU06 returns a full payload including datos_academicos and documents
        payload = use_case.execute(id_tutor, id_becario)
    except ValueError as e:
        flash(str(e), "error")
        return redirect(url_for("tutor.dashboard"))
        
    return render_template("tutor/auditoria_academica.html", perfil=payload["perfil_becario"], datos=payload["datos_academicos"], id_usuario=id_becario)


@tutor_bp.route("/becario/<id_becario>/auditoria", methods=["POST"])
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
        
    return redirect(url_for("tutor.visualizar_auditoria_academica", id_becario=id_becario))

