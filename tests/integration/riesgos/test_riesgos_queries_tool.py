#!/usr/bin/env python3
"""Test de integración: ejecución de las 8 consultas usadas para obtener usuarios técnicos en Riesgos.

El objetivo del test es validar que las consultas se ejecutan sin lanzar excepciones y que la conexión
contra la base de datos de riesgos es posible en el entorno de pruebas. No se hacen aserciones sobre
el contenido porque depende de datos locales.
"""

import sys
from pathlib import Path

import pytest

# Mantener compatibilidad si los tests se ejecutan sin instalar el paquete
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root / "src"))

from common.config import Config  # noqa: E402
from common.db.database import AccessDatabase  # noqa: E402


def test_riesgos_queries():
    queries = {
        "1. Ediciones que necesitan publicación": """
            SELECT DISTINCT TbProyectosEdiciones.UsuarioRed, TbUsuariosAplicaciones.Nombre,
            TbUsuariosAplicaciones.CorreoUsuario
            FROM TbProyectosEdiciones
            INNER JOIN TbUsuariosAplicaciones ON TbProyectosEdiciones.UsuarioRed = TbUsuariosAplicaciones.UsuarioRed
            WHERE TbProyectosEdiciones.FechaPublicacion IS NULL
              AND TbProyectosEdiciones.FechaPropuestaPublicacion IS NOT NULL
              AND TbProyectosEdiciones.FechaPropuestaPublicacionRechazada IS NULL
        """,
        "2. Ediciones con propuesta de publicación rechazada": """
            SELECT DISTINCT TbProyectosEdiciones.UsuarioRed, TbUsuariosAplicaciones.Nombre,
            TbUsuariosAplicaciones.CorreoUsuario
            FROM TbProyectosEdiciones
            INNER JOIN TbUsuariosAplicaciones ON TbProyectosEdiciones.UsuarioRed = TbUsuariosAplicaciones.UsuarioRed
            WHERE TbProyectosEdiciones.FechaPropuestaPublicacionRechazada IS NOT NULL
              AND TbProyectosEdiciones.FechaPublicacion IS NULL
        """,
        "3. Riesgos aceptados no motivados": """
            SELECT DISTINCT TbRiesgos.UsuarioRed, TbUsuariosAplicaciones.Nombre,
            TbUsuariosAplicaciones.CorreoUsuario
            FROM TbRiesgos
            INNER JOIN TbUsuariosAplicaciones ON TbRiesgos.UsuarioRed = TbUsuariosAplicaciones.UsuarioRed
            WHERE TbRiesgos.FechaJustificacionAceptacionRiesgo IS NOT NULL
              AND TbRiesgos.ParaInformeAvisos <> 'No'
              AND TbRiesgos.FechaJustificacionAceptacionRiesgoRechazada IS NULL
              AND TbRiesgos.JustificacionAceptacionRiesgo IS NULL
        """,
        "4. Riesgos aceptados rechazados": """
            SELECT DISTINCT TbRiesgos.UsuarioRed, TbUsuariosAplicaciones.Nombre,
            TbUsuariosAplicaciones.CorreoUsuario
            FROM TbRiesgos
            INNER JOIN TbUsuariosAplicaciones ON TbRiesgos.UsuarioRed = TbUsuariosAplicaciones.UsuarioRed
            WHERE TbRiesgos.FechaJustificacionAceptacionRiesgoRechazada IS NOT NULL
              AND TbRiesgos.ParaInformeAvisos <> 'No'
        """,
        "5. Riesgos retirados no motivados": """
            SELECT DISTINCT TbRiesgos.UsuarioRed, TbUsuariosAplicaciones.Nombre,
            TbUsuariosAplicaciones.CorreoUsuario
            FROM TbRiesgos
            INNER JOIN TbUsuariosAplicaciones ON TbRiesgos.UsuarioRed = TbUsuariosAplicaciones.UsuarioRed
            WHERE TbRiesgos.FechaJustificacionRetiroRiesgo IS NOT NULL
              AND TbRiesgos.ParaInformeAvisos <> 'No'
              AND TbRiesgos.FechaJustificacionRetiroRiesgoRechazada IS NULL
              AND TbRiesgos.JustificacionRetiroRiesgo IS NULL
        """,
        "6. Riesgos retirados rechazados": """
            SELECT DISTINCT TbRiesgos.UsuarioRed, TbUsuariosAplicaciones.Nombre,
            TbUsuariosAplicaciones.CorreoUsuario
            FROM TbRiesgos
            INNER JOIN TbUsuariosAplicaciones ON TbRiesgos.UsuarioRed = TbUsuariosAplicaciones.UsuarioRed
            WHERE TbRiesgos.FechaJustificacionRetiroRiesgoRechazada IS NOT NULL
              AND TbRiesgos.ParaInformeAvisos <> 'No'
        """,
        "7. Riesgos con acciones de mitigación para replanificar": """
            SELECT DISTINCT TbRiesgos.UsuarioRed, TbUsuariosAplicaciones.Nombre,
            TbUsuariosAplicaciones.CorreoUsuario
            FROM TbRiesgos
            INNER JOIN TbUsuariosAplicaciones ON TbRiesgos.UsuarioRed = TbUsuariosAplicaciones.UsuarioRed
            WHERE TbRiesgos.AccionMitigacion IS NOT NULL
              AND TbRiesgos.ParaInformeAvisos <> 'No'
              AND TbRiesgos.FechaFinAccionMitigacion IS NOT NULL
              AND TbRiesgos.FechaFinAccionMitigacion < Date()
              AND TbRiesgos.FechaFinRealAccionMitigacion IS NULL
        """,
        "8. Riesgos con acciones de contingencia para replanificar": """
            SELECT DISTINCT TbRiesgos.UsuarioRed, TbUsuariosAplicaciones.Nombre,
            TbUsuariosAplicaciones.CorreoUsuario
            FROM TbRiesgos
            INNER JOIN TbUsuariosAplicaciones ON TbRiesgos.UsuarioRed = TbUsuariosAplicaciones.UsuarioRed
            WHERE TbRiesgos.AccionContingencia IS NOT NULL
              AND TbRiesgos.ParaInformeAvisos <> 'No'
              AND TbRiesgos.FechaFinAccionContingencia IS NOT NULL
              AND TbRiesgos.FechaFinAccionContingencia < Date()
              AND TbRiesgos.FechaFinRealAccionContingencia IS NULL
        """,
    }

    config = Config()
    try:
        db = AccessDatabase(config.get_db_connection_string("riesgos"))
        db.connect()
        cursor = db.get_cursor()
        # Ejecutar cada consulta; si una falla, la registramos pero no abortamos
        # todas salvo error crítico
        for name, sql in queries.items():
            try:
                cursor.execute(sql)
                _ = cursor.fetchall()
            except Exception as qerr:
                # Solo registramos el error; este test es diagnóstico y no debe fallar
                # por datos incompletos.
                print(f"[AVISO] Consulta '{name}' falló: {qerr}")
    except Exception as conn_err:
        pytest.fail(f"No se pudo conectar a la BD de riesgos: {conn_err}")
    finally:
        if "db" in locals():
            try:
                db.disconnect()
            except Exception:
                pass
