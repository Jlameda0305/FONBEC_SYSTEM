"""
Administrador HTTP Controller (Flask Blueprint).
"""

import logging
from flask import Blueprint, g, render_template, request, flash, redirect, url_for

from src.web.auth_utils import requiere_rol
from src.infrastructure.repositories import (
    SQLAlchemyUsuarioRepository,
    SQLAlchemyPadrinoRepository,
    SQLAlchemyBecarioRepository
)
from src.application.use_cases.CU05_Admin_ListarActores import ListarActoresUseCase
from src.application.use_cases.CU06_Admin_ObtenerDatosBecario import AdminObtenerDatosBecarioUseCase
from src.application.use_cases.CU04_Admin_GestionarPadrinos import GestionarPadrinosUseCase
from src.application.use_cases.CU03_Admin_GestionarVinculaciones import GestionarVinculacionesUseCase
from src.application.use_cases.invitar_usuario import InvitarUsuarioUseCase
from src.infrastructure.database import get_supabase_client
from src.infrastructure.auth_service import SupabaseAuthService
from src.infrastructure.storage.supabase_storage import SupabaseStorageService
from src.application.use_cases.eliminar_becario import EliminarBecarioUseCase
from src.application.use_cases.eliminar_referente import EliminarReferenteUseCase


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def get_padrinos_use_case():
    repo = SQLAlchemyPadrinoRepository(g.db_session)
    return GestionarPadrinosUseCase(repo)

def get_vinculaciones_use_case():
    becario_repo = SQLAlchemyBecarioRepository(g.db_session)
    usuario_repo = SQLAlchemyUsuarioRepository(g.db_session)
    padrino_repo = SQLAlchemyPadrinoRepository(g.db_session)
    return GestionarVinculacionesUseCase(becario_repo, usuario_repo, padrino_repo)

def get_invitar_usuario_use_case():
    supabase_client = get_supabase_client()
    auth_service = SupabaseAuthService(supabase_client)
    usuario_repo = SQLAlchemyUsuarioRepository(g.db_session)
    return InvitarUsuarioUseCase(auth_service, usuario_repo)

def get_eliminar_becario_uc():
    supabase_client = get_supabase_client()
    repo = SQLAlchemyUsuarioRepository(g.db_session)
    storage = SupabaseStorageService(supabase_client)
    auth = SupabaseAuthService(supabase_client)
    return EliminarBecarioUseCase(repo, storage, auth)

def get_eliminar_referente_uc():
    repo = SQLAlchemyUsuarioRepository(g.db_session)
    auth = SupabaseAuthService(get_supabase_client())
    return EliminarReferenteUseCase(repo, auth)


@admin_bp.route("/dashboard", methods=["GET"])
@requiere_rol("administrador")
def dashboard():
    """
    GET /admin/dashboard
    
    Panel vacío, se implementará más adelante.
    """
    return render_template("admin/dashboard.html")


@admin_bp.route("/directorio/<rol>", methods=["GET"])
@requiere_rol("administrador")
def directorio_rol(rol):
    """
    GET /admin/directorio/<rol>
    
    Lista actores del sistema por rol (CU-ADM-05).
    """
    try:
        pagina = int(request.args.get("pagina", 1))
    except ValueError:
        pagina = 1
        
    busqueda = request.args.get("busqueda", "").strip() or None
    filtro_rol = rol.strip().lower()

    repo = SQLAlchemyUsuarioRepository(g.db_session)
    use_case = ListarActoresUseCase(repo)

    try:
        resultado_uc = use_case.execute(
            actor_admin=g.usuario_actual,
            tipo_actor=filtro_rol,
            pagina=pagina,
            limite=10,
            busqueda=busqueda
        )
        actores = resultado_uc.get("actores", [])
        total = resultado_uc.get("total", 0)
    except Exception as e:
        logging.error(f"CU-ADM-05: Fallo al listar actores. Detalles: {str(e)}")
        flash("Ocurrió un error al cargar los usuarios desde la base de datos.", "error")
        actores = []
        total = 0

    return render_template(
        "admin/actores_lista.html",
        actores=actores,
        total_actores=total,
        pagina_actual=pagina,
        busqueda=busqueda or "",
        filtro_rol=filtro_rol
    )


@admin_bp.route("/padrinos", methods=["GET"])
@requiere_rol("administrador")
def listar_padrinos():
    try:
        pagina = int(request.args.get("pagina", 1))
    except ValueError:
        pagina = 1
        
    busqueda = request.args.get("busqueda", "").strip() or None

    repo = SQLAlchemyUsuarioRepository(g.db_session)
    use_case = ListarActoresUseCase(repo)
    
    try:
        resultado_uc = use_case.execute(
            actor_admin=g.usuario_actual,
            tipo_actor="padrino",
            pagina=pagina,
            limite=10,
            busqueda=busqueda
        )
        padrinos = resultado_uc.get("actores", [])
        total = resultado_uc.get("total", 0)
    except Exception as e:
        flash("Error al cargar la lista de padrinos.", "error")
        padrinos = []
        total = 0

    return render_template(
        "admin/actores_lista.html",
        actores=padrinos,
        total_actores=total,
        pagina_actual=pagina,
        busqueda=busqueda or "",
        filtro_rol="padrino"
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
    
    padrino = uc.obtener(actor_admin=g.usuario_actual, id_padrino=id_padrino)
    if not padrino:
        flash("El padrino no existe.", "error")
        return redirect(url_for("admin.listar_padrinos"))
        
    return render_template("admin/padrino_form.html", padrino=padrino)


@admin_bp.route("/referentes/<rol>/<id_referente>/eliminar", methods=["POST"])
@requiere_rol("administrador")
def eliminar_referente(rol, id_referente):
    email_confirmacion = request.form.get("email_confirmacion", "").strip()
    
    uc = get_eliminar_referente_uc()
    try:
        uc.execute(actor_admin=g.usuario_actual, referente_id=id_referente, rol=rol, email_confirmacion=email_confirmacion)
        # Commit to save DB changes because Saga pattern succeeded
        g.db_session.commit()
        flash(f"{rol.capitalize()} eliminado correctamente.", "success")
    except ValueError as e:
        g.db_session.rollback()
        flash(str(e), "error")
    except Exception as e:
        g.db_session.rollback()
        logging.error(f"Error eliminando referente: {e}")
        flash("Ocurrió un error inesperado al eliminar el usuario.", "error")
        
    if rol == "padrino":
        return redirect(url_for("admin.listar_padrinos"))
    return redirect(url_for("admin.directorio_rol", rol=rol))


@admin_bp.route("/becarios/<id_becario>/eliminar", methods=["POST"])
@requiere_rol("administrador")
def eliminar_becario(id_becario):
    email_confirmacion = request.form.get("email_confirmacion", "").strip()
    
    uc = get_eliminar_becario_uc()
    try:
        uc.execute(actor_admin=g.usuario_actual, becario_id=id_becario, email_confirmacion=email_confirmacion)
        # Commit to save DB changes because Saga pattern succeeded
        g.db_session.commit()
        flash("Becario eliminado correctamente.", "success")
    except ValueError as e:
        g.db_session.rollback()
        flash(str(e), "error")
    except Exception as e:
        g.db_session.rollback()
        logging.error(f"Error eliminando becario: {e}")
        flash("Ocurrió un error inesperado al eliminar el becario.", "error")
        
    return redirect(url_for("admin.directorio_rol", rol="becario"))


@admin_bp.route("/becarios/<id_becario>/detalle", methods=["GET"])
@requiere_rol("administrador")
def detalle_becario(id_becario):
    """
    GET /admin/becarios/<id_becario>/detalle
    Muestra la página unificada de detalles del becario (Perfil, Vinculaciones y Académico).
    """
    becario_repo = SQLAlchemyBecarioRepository(g.db_session)
    datos_uc = AdminObtenerDatosBecarioUseCase(becario_repo)
    
    try:
        datos = datos_uc.execute(actor_admin=g.usuario_actual, becario_id=id_becario)
    except ValueError as e:
        flash(str(e), "error")
        return redirect(url_for("admin.dashboard"))
    except PermissionError as e:
        flash(str(e), "error")
        return redirect(url_for("admin.dashboard"))
        
    usuario_repo = SQLAlchemyUsuarioRepository(g.db_session)
    listar_uc = ListarActoresUseCase(usuario_repo)
    
    try:
        tutores_res = listar_uc.execute(actor_admin=g.usuario_actual, tipo_actor="tutor", pagina=1, limite=1000)
        mediadores_res = listar_uc.execute(actor_admin=g.usuario_actual, tipo_actor="mediador", pagina=1, limite=1000)
        padrinos_res = listar_uc.execute(actor_admin=g.usuario_actual, tipo_actor="padrino", pagina=1, limite=1000)
        
        tutores_disponibles = tutores_res.get("actores", [])
        mediadores_disponibles = mediadores_res.get("actores", [])
        padrinos_disponibles = padrinos_res.get("actores", [])
    except Exception as e:
        logging.error(f"Error cargando actores disponibles: {str(e)}")
        flash("Error al cargar actores disponibles.", "error")
        tutores_disponibles = []
        mediadores_disponibles = []
        padrinos_disponibles = []
    
    return render_template(
        "shared/becario_detalle.html",
        datos=datos,
        id_usuario=id_becario,
        tutores=tutores_disponibles,
        mediadores=mediadores_disponibles,
        padrinos=padrinos_disponibles
    )

@admin_bp.route("/becarios/<id_becario>/vinculaciones/vincular", methods=["POST"])
@requiere_rol("administrador")
def vincular_actor(id_becario):
    tipo_vinculacion = request.form.get("tipo_vinculacion")
    id_objetivo = request.form.get("id_objetivo")
    
    if not id_objetivo:
        flash("Debe seleccionar un actor para vincular.", "error")
        return redirect(url_for("admin.detalle_becario", id_becario=id_becario))
        
    uc = get_vinculaciones_use_case()
    
    try:
        uc.asignar_vinculo(
            actor_admin=g.usuario_actual,
            id_becario=id_becario,
            tipo_vinculacion=tipo_vinculacion,
            id_objetivo=id_objetivo
        )
        flash(f"{tipo_vinculacion.capitalize()} asignado correctamente.", "success")
    except ValueError as e:
        flash(str(e), "error")
    except TypeError as e:
        flash(f"Error de dominio: {str(e)}", "error")
    except Exception as e:
        flash(f"Error inesperado al vincular: {str(e)}", "error")
        
    return redirect(url_for("admin.detalle_becario", id_becario=id_becario))

@admin_bp.route("/becarios/<id_becario>/vinculaciones/desvincular/<tipo_vinculacion>", methods=["POST"])
@requiere_rol("administrador")
def desvincular_actor(id_becario, tipo_vinculacion):
    uc = get_vinculaciones_use_case()
    
    try:
        uc.desasignar_vinculo(
            actor_admin=g.usuario_actual,
            id_becario=id_becario,
            tipo_vinculacion=tipo_vinculacion
        )
        flash(f"Vinculación de {tipo_vinculacion} removida correctamente.", "success")
    except ValueError as e:
        flash(str(e), "error")
    except Exception as e:
        flash(f"Error al desvincular: {str(e)}", "error")
        
    return redirect(url_for("admin.detalle_becario", id_becario=id_becario))


@admin_bp.route("/invitar", methods=["GET", "POST"])
@requiere_rol("administrador")
def invitar_usuario():
    """
    POST /admin/invitar
    Invita a un nuevo usuario al sistema delegando la operación al servicio de auth.
    """
    if request.method == "GET":
        return render_template("admin/invitar_usuario.html")

    email = request.form.get("email")
    rol = request.form.get("rol")

    if not email or not rol:
        flash("Email y rol son requeridos.", "error")
        return redirect(url_for("admin.dashboard"))

    try:
        uc = get_invitar_usuario_use_case()
        user_id = uc.execute(actor_admin=g.usuario_actual, email=email, rol=rol)
        flash(f"Invitación enviada exitosamente a {email}.", "success")
    except PermissionError as e:
        flash(str(e), "error")
    except ValueError as e:
        flash(str(e), "error")
    except Exception as e:
        logging.error(f"Error al invitar usuario: {str(e)}")
        flash("Error inesperado al procesar la invitación.", "error")
        
    return redirect(url_for("admin.dashboard"))
