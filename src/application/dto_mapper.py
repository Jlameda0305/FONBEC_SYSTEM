"""
DTO Mapping logic.
Extracts serialization/presentation concerns from Domain Entities.
"""

def usuario_to_dict(usuario) -> dict:
    return {
        "id_usuario": getattr(usuario, "id_usuario", None) or getattr(usuario, "id_padrino", None),
        "nombre": usuario.nombre,
        "apellido": usuario.apellido,
        "email": usuario.email,
        "telefono": usuario.telefono,
        "edad": getattr(usuario, "edad", None),
        "sexo": getattr(usuario, "sexo", None),
        "direccion": getattr(usuario, "direccion", None),
        "rol": getattr(usuario, "rol", "padrino" if hasattr(usuario, "id_padrino") else None)
    }

def datos_academicos_to_dict(datos) -> dict:
    if not datos:
        return {}
    
    documentos = {
        doc.tipo_documento: {
            "ruta_archivo": doc.ruta_archivo,
            "fecha_carga": doc.fecha_carga.isoformat() if doc.fecha_carga else None,
        }
        for doc in getattr(datos, "lista_documentos", [])
    }
    
    documentos_requeridos_info = [
        ("Programa", "Programa de la carrera"),
        ("CartaCompromiso", "Carta de compromiso"),
        ("Inscripcion", "Inscripción al año en curso")
    ]
    
    return {
        "nombre_carrera": datos.nombre_carrera,
        "anio_ingreso": datos.anio_ingreso,
        "anio_en_curso": datos.anio_en_curso,
        "materias_a_cursar": datos.materias_a_cursar,
        "materias_adeudadas": datos.materias_adeudadas,
        "estado_verificacion": datos.estado_verificacion.value if hasattr(datos.estado_verificacion, "value") else datos.estado_verificacion,
        "observaciones": datos.observaciones,
        "fecha_observacion": datos.fecha_observacion.isoformat() if datos.fecha_observacion else None,
        "documentos": documentos,
        "documentos_requeridos": documentos_requeridos_info,
    }
