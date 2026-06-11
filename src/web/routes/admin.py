"""
Administrador HTTP Controller (Flask Blueprint).
"""

from flask import Blueprint, g, render_template, request
from src.web.auth_utils import requiere_rol
from src.infrastructure.repositories import SQLAlchemyUsuarioRepository
from src.application.use_cases.CU05_Admin_ListarActores import ListarActoresUseCase

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/dashboard", methods=["GET"])
@requiere_rol("administrador")
def dashboard():
    """
    GET /admin/dashboard
    
    Dashboard panel for Administrador. Lists system actors (CU-ADM-05).
    """
    # 1. Recuperar parámetros con defaults seguros
    try:
        pagina = int(request.args.get("pagina", 1))
    except ValueError:
        pagina = 1
        
    busqueda = request.args.get("busqueda", "").strip() or None
    filtro_rol = request.args.get("filtro_rol", "becario").strip().lower()

    # 2. Instanciar Infraestructura y Caso de Uso
    repo = SQLAlchemyUsuarioRepository(g.db_session)
    use_case = ListarActoresUseCase(repo)

    # 3. Ejecutar el Caso de Uso (g.usuario_actual inyectado por el decorador)
    try:
        actores = use_case.ejecutar(
            actor_admin=g.usuario_actual,
            tipo_actor=filtro_rol,
            pagina=pagina,
            limite=10,  # 10 por página por defecto para el panel
            busqueda=busqueda
        )
    except Exception as e:
        from flask import flash
        print(f"[ERROR] CU-ADM-05: Fallo al listar actores. Detalles: {str(e)}")
        flash("Ocurrió un error al cargar los usuarios desde la base de datos.", "error")
        actores = []

    # 4. Renderizar vista con la data
    return render_template(
        "admin/dashboard.html",
        actores=actores,
        pagina_actual=pagina,
        busqueda=busqueda or "",
        filtro_rol=filtro_rol
    )
