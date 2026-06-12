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
from src.application.use_cases.CU04_Admin_GestionarPadrinos import GestionarPadrinosUseCase
from src.application.use_cases.CU03_Admin_GestionarVinculaciones import GestionarVinculacionesUseCase


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def get_padrinos_use_case():
    repo = SQLAlchemyPadrinoRepository(g.db_session)
    return GestionarPadrinosUseCase(repo)

def get_vinculaciones_use_case():
    becario_repo = SQLAlchemyBecarioRepository(g.db_session)
    usuario_repo = SQLAlchemyUsuarioRepository(g.db_session)
    padrino_repo = SQLAlchemyPadrinoRepository(g.db_session)
    return GestionarVinculacionesUseCase(becario_repo, usuario_repo, padrino_repo)


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
        actores = use_case.ejecutar(
            actor_admin=g.usuario_actual,
            tipo_actor=filtro_rol,
            pagina=pagina,
            limite=10,
            busqueda=busqueda
        )
    except Exception as e:
        logging.error(f"CU-ADM-05: Fallo al listar actores. Detalles: {str(e)}")
        flash("Ocurrió un error al cargar los usuarios desde la base de datos.", "error")
        actores = []

    return render_template(
        "admin/actores_lista.html",
        actores=actores,
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


@admin_bp.route("/becarios/<id_becario>/detalle", methods=["GET"])
@requiere_rol("administrador")
def detalle_becario(id_becario):
    """
    GET /admin/becarios/<id_becario>/detalle
    Muestra la página unificada de detalles del becario (Perfil, Vinculaciones y Académico).
    """
    becario_repo = SQLAlchemyBecarioRepository(g.db_session)
    becario = becario_repo.obtener_por_id(id_becario)
    
    if not becario:
        flash("Becario no encontrado.", "error")
        return redirect(url_for("admin.dashboard"))
        
    usuario_repo = SQLAlchemyUsuarioRepository(g.db_session)
    listar_uc = ListarActoresUseCase(usuario_repo)
    
    try:
        tutores_disponibles = listar_uc.ejecutar(actor_admin=g.usuario_actual, tipo_actor="tutor", pagina=1, limite=1000)
        mediadores_disponibles = listar_uc.ejecutar(actor_admin=g.usuario_actual, tipo_actor="mediador", pagina=1, limite=1000)
        padrinos_disponibles = listar_uc.ejecutar(actor_admin=g.usuario_actual, tipo_actor="padrino", pagina=1, limite=1000)
    except Exception as e:
        logging.error(f"Error cargando actores disponibles: {str(e)}")
        flash("Error al cargar actores disponibles.", "error")
        tutores_disponibles = []
        mediadores_disponibles = []
        padrinos_disponibles = []
    
    return render_template(
        "shared/becario_detalle.html",
        becario=becario,
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

