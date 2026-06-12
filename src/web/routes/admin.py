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
        import logging
        from flask import flash
        logging.error(f"CU-ADM-05: Fallo al listar actores. Detalles: {str(e)}")
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


from flask import flash, redirect, url_for
from src.infrastructure.repositories import SQLAlchemyPadrinoRepository
from src.application.use_cases.CU04_Admin_GestionarPadrinos import GestionarPadrinosUseCase

def get_padrinos_use_case():
    repo = SQLAlchemyPadrinoRepository(g.db_session)
    return GestionarPadrinosUseCase(repo)

@admin_bp.route("/padrinos", methods=["GET"])
@requiere_rol("administrador")
def listar_padrinos():
    try:
        pagina = int(request.args.get("pagina", 1))
    except ValueError:
        pagina = 1
        
    busqueda = request.args.get("busqueda", "").strip() or None

    # Usamos ListarActoresUseCase para listar padrinos paginados
    repo = SQLAlchemyUsuarioRepository(g.db_session)
    use_case = ListarActoresUseCase(repo)
    
    try:
        padrinos = use_case.ejecutar(
            actor_admin=g.usuario_actual,
            tipo_actor="padrino",
            pagina=pagina,
            limite=10,
            busqueda=busqueda
        )
    except Exception as e:
        flash("Error al cargar la lista de padrinos.", "error")
        padrinos = []

    return render_template(
        "admin/padrinos_lista.html",
        padrinos=padrinos,
        pagina_actual=pagina,
        busqueda=busqueda or ""
    )


@admin_bp.route("/padrinos/nuevo", methods=["GET", "POST"])
@requiere_rol("administrador")
def nuevo_padrino():
    if request.method == "POST":
        datos = {
            "nombre": request.form.get("nombre", "").strip(),
            "apellido": request.form.get("apellido", "").strip(),
            "email": request.form.get("email", "").strip(),
            "telefono": request.form.get("telefono", "").strip(),
            "direccion": request.form.get("direccion", "").strip()
        }
        
        try:
            uc = get_padrinos_use_case()
            uc.crear(actor_admin=g.usuario_actual, datos=datos)
            flash("Padrino creado exitosamente.", "success")
            return redirect(url_for("admin.listar_padrinos"))
        except Exception as e:
            flash(f"Error al crear: {str(e)}", "error")
            
    return render_template("admin/padrino_form.html", padrino=None)


@admin_bp.route("/padrinos/<id_padrino>/editar", methods=["GET", "POST"])
@requiere_rol("administrador")
def editar_padrino(id_padrino):
    uc = get_padrinos_use_case()
    
    if request.method == "POST":
        datos = {
            "nombre": request.form.get("nombre", "").strip(),
            "apellido": request.form.get("apellido", "").strip(),
            "email": request.form.get("email", "").strip(),
            "telefono": request.form.get("telefono", "").strip(),
            "direccion": request.form.get("direccion", "").strip()
        }
        
        try:
            uc.modificar(actor_admin=g.usuario_actual, id_padrino=id_padrino, datos=datos)
            flash("Padrino actualizado exitosamente.", "success")
            return redirect(url_for("admin.listar_padrinos"))
        except Exception as e:
            flash(f"Error al actualizar: {str(e)}", "error")
    
    # GET or POST (if error)
    padrino = uc.obtener(actor_admin=g.usuario_actual, id_padrino=id_padrino)
    if not padrino:
        flash("El padrino no existe.", "error")
        return redirect(url_for("admin.listar_padrinos"))
        
    return render_template("admin/padrino_form.html", padrino=padrino)


@admin_bp.route("/padrinos/<id_padrino>/eliminar", methods=["POST"])
@requiere_rol("administrador")
def eliminar_padrino(id_padrino):
    uc = get_padrinos_use_case()
    try:
        uc.eliminar(actor_admin=g.usuario_actual, id_padrino=id_padrino)
        flash("Padrino eliminado correctamente.", "success")
    except ValueError as e:
        flash(str(e), "error")
    except Exception as e:
        flash("Ocurrió un error inesperado al eliminar el padrino.", "error")
        
    return redirect(url_for("admin.listar_padrinos"))
