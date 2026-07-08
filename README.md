<div align="center">
  <img src="docs/images/VARIACION%203%20NEGRO.png" alt="FONBEC Logo" width="250">
</div>

# FONBEC System — Gestión Integral de Becas

Plataforma Web empresarial para gestionar el programa de becas de la Fundación FONBEC. Permite administrar de manera segura el ciclo de vida académico de los becarios y coordinar la interacción con Tutores, Mediadores y Padrinos en un entorno unificado.

[![Backend](https://img.shields.io/badge/Backend-Flask_3.1-blue.svg)]()
[![Base de Datos](https://img.shields.io/badge/Database-Supabase-336791.svg)]()
[![Arquitectura](https://img.shields.io/badge/Arquitectura-Clean_Architecture-green.svg)](docs/arc42/)

## Quick Path (Arranque Local)

1. **Clonar e ingresar al repositorio:**
   ```bash
   git clone https://github.com/tu-usuario/fonbec-system.git
   cd fonbec-system
   ```

2. **Crear entorno virtual e instalar dependencias:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows usa: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configurar variables de entorno:**
   Crea un archivo `.env` en la raíz del proyecto. Completa las variables detalladas en la sección *Detalles*.

4. **Ejecutar el servidor:**
   ```bash
   python run.py
   ```
   > [!NOTE]
   > El servidor de desarrollo de Flask se iniciará en `http://127.0.0.1:5000`.

## Detalles

| Tópico | Decisión y Recursos |
|---|---|
| **Arquitectura** | Usamos **Clean Architecture** (Dominio, Aplicación, Infraestructura, Web). Todo está documentado bajo el estándar arc42 en `/docs/`. |
| **Glosario (Lenguaje Oblicuo)** | Lectura obligatoria para alinear conceptos de código y negocio: [12-Glosario](docs/12-glosario.md). |
| **Variables `.env` Clave** | `FLASK_ENV`, `SECRET_KEY`, `SUPABASE_URL`, `SUPABASE_KEY` (Role Key de admin API), y `SUPABASE_DATABASE_URL` (para el ORM de SQLAlchemy). |
| **Seguridad y Estado** | La sesión local depende enteramente de un `SECRET_KEY` robusto. Ver la [Matriz de Riesgos y Deuda Técnica](docs/arc42/11-riesgos-y-deuda-tecnica.md) documentada. |

## ✅ Checklist para Desarrolladores

- [ ] ¿Leíste el [Glosario de Negocio](docs/12-glosario.md) para comprender la diferencia entre Tutor, Mediador y Padrino?
- [ ] ¿Validaste que tu entorno local tiene el archivo `.env` configurado y `SUPABASE_DATABASE_URL` conectado?
- [ ] ¿Comprendes que el *Becario* es el Aggregate Root del dominio sobre el que navega el sistema?

## Siguientes Pasos

Para entender la estructura y límites del sistema, comienza por la [Visión General y Metas](docs/01-introduccion-y-metas.md) y luego explora el [Alcance y Contexto](docs/03-alcance-y-contexto.md).
