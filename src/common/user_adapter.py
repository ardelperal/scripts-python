"""
Adaptador para manejar usuarios cuando la tabla TbUsuariosAplicacionesTareas no existe.
Este módulo proporciona funciones alternativas que usan TbUsuariosAplicacionesPermisos.
"""

import logging


def get_admin_users_alternative(db_connection) -> list[dict[str, str]]:
    """
    Obtiene la lista de usuarios administradores usando TbUsuariosAplicacionesPermisos
    como alternativa cuando TbUsuariosAplicacionesTareas no existe.

    Args:
        db_connection: Conexión a la base de datos de tareas

    Returns:
        Lista de usuarios administradores
    """
    try:
        query = """
            SELECT ua.UsuarioRed, ua.Nombre, ua.CorreoUsuario
            FROM TbUsuariosAplicaciones ua
            INNER JOIN TbUsuariosAplicacionesPermisos uap ON ua.CorreoUsuario = uap.CorreoUsuario
            WHERE ua.ParaTareasProgramadas = True
            AND ua.FechaBaja IS NULL
            AND uap.EsUsuarioAdministrador = 'Sí'
        """

        result = db_connection.execute_query(query)
        return result

    except Exception as e:
        logging.error(f"Error obteniendo usuarios administradores (alternativo): {e}")
        return []


def get_technical_users_alternative(
    app_id: str, config, logger
) -> list[dict[str, str]]:
    """
    Obtiene la lista de usuarios técnicos usando TbUsuariosAplicacionesPermisos
    como alternativa cuando TbUsuariosAplicacionesTareas no existe.

    Args:
        app_id: ID de la aplicación
        config: Configuración de la aplicación
        logger: Logger para registrar eventos

    Returns:
        Lista de usuarios técnicos
    """
    try:
        from .database import AccessDatabase

        # Usar la conexión de tareas para obtener usuarios
        db_connection = AccessDatabase(config.get_db_tareas_connection_string())

        # Para usuarios técnicos, obtenemos usuarios que NO tienen permisos específicos
        # (usuarios que están en TbUsuariosAplicaciones pero no en TbUsuariosAplicacionesPermisos)
        query = """
            SELECT ua.UsuarioRed, ua.Nombre, ua.CorreoUsuario
            FROM TbUsuariosAplicaciones ua
            LEFT JOIN TbUsuariosAplicacionesPermisos uap ON ua.CorreoUsuario = uap.CorreoUsuario
            WHERE ua.ParaTareasProgramadas = True
            AND ua.FechaBaja IS NULL
            AND uap.CorreoUsuario IS NULL
        """

        result = db_connection.execute_query(query)
        return result

    except Exception as e:
        logger.error(
            f"Error obteniendo usuarios técnicos para {app_id} (alternativo): {e}"
        )
        return []


def get_quality_users_alternative(app_id: str, config, logger) -> list[dict[str, str]]:
    """
    Obtiene la lista de usuarios de calidad usando TbUsuariosAplicacionesPermisos
    como alternativa cuando TbUsuariosAplicacionesTareas no existe.

    Args:
        app_id: ID de la aplicación
        config: Configuración de la aplicación
        logger: Logger para registrar eventos

    Returns:
        Lista de usuarios de calidad
    """
    # Estrategia: intentar con filtro numérico, si mismatch (-3030) probar con filtro entre comillas,
    # si vuelve a fallar, quitar filtro IDAplicacion y devolver todos los de calidad.
    base_select = (
        "SELECT ua.UsuarioRed, ua.Nombre, ua.CorreoUsuario "
        "FROM TbUsuariosAplicaciones ua "
        "INNER JOIN TbUsuariosAplicacionesPermisos uap ON ua.CorreoUsuario = uap.CorreoUsuario "
        "WHERE ua.ParaTareasProgramadas = True "
        "AND ua.FechaBaja IS NULL "
        "AND uap.EsUsuarioCalidad = 'Sí' "
    )
    attempts = []
    try:
        app_id_int = (
            int(app_id)
            if app_id is not None
            else int(getattr(config, "app_id_agedys", 3))
        )
    except Exception:
        app_id_int = int(getattr(config, "app_id_agedys", 3))
    # 1) Filtro numérico inline
    attempts.append((f"{base_select}AND uap.IDAplicacion = {app_id_int}", "numeric"))
    # 2) Filtro quoted
    attempts.append((f"{base_select}AND uap.IDAplicacion = '{app_id_int}'", "quoted"))
    # 3) Sin filtro
    attempts.append((base_select, "nofilter"))

    from .database import AccessDatabase

    db_connection = AccessDatabase(config.get_db_tareas_connection_string())

    selected_mode = None
    selected_rows = []
    for sql, mode in attempts:
        try:
            res = db_connection.execute_query(sql)
            logger.info(
                f"Intento usuarios calidad modo={mode} filas={len(res)}",
                extra={
                    "event": "quality_users_attempt",
                    "mode": mode,
                    "rows": len(res),
                },
            )
            if res:  # devolver primera opción exitosa con resultados
                selected_mode = mode
                selected_rows = res
                break
            # Si no hay resultados seguimos intentando (excepto nofilter que ya es último)
            if mode == "nofilter":
                logger.warning(
                    "Sin usuarios de calidad tras modo nofilter",
                    extra={
                        "event": "quality_users_empty",
                        "modes_tried": [m for _, m in attempts],
                    },
                )
        except Exception as e:
            if "-3030" in str(e) or "No coinciden los tipos de datos" in str(e):
                logger.warning(
                    f"Data type mismatch modo={mode} intentando siguiente variante",
                    extra={"event": "quality_users_type_mismatch", "mode": mode},
                )
                continue
            logger.error(
                f"Error consulta usuarios calidad modo={mode}: {e}",
                extra={"event": "quality_users_error", "mode": mode, "error": str(e)},
            )
            continue

    if selected_mode:
        logger.info(
            f"Usuarios de calidad seleccionados modo={selected_mode} total={len(selected_rows)}",
            extra={
                "event": "quality_users_selected",
                "mode": selected_mode,
                "rows": len(selected_rows),
            },
        )
        return selected_rows

    logger.info(
        "Sin usuarios de calidad tras todos los intentos",
        extra={
            "event": "quality_users_all_attempts_failed",
            "modes_tried": [m for _, m in attempts],
        },
    )
    return []


def get_economy_users_alternative(config, logger) -> list[dict[str, str]]:
    """
    Obtiene la lista de usuarios de economía usando TbUsuariosAplicacionesPermisos
    como alternativa cuando TbUsuariosAplicacionesTareas no existe.

    Args:
        config: Configuración de la aplicación
        logger: Logger para registrar eventos

    Returns:
        Lista de usuarios de economía
    """
    try:
        from .database import AccessDatabase

        # Usar la conexión de tareas para obtener usuarios
        db_connection = AccessDatabase(config.get_db_tareas_connection_string())

        # Para usuarios de economía, usamos la tabla de permisos con ID de aplicación (boolean o texto)
        app_id_int = getattr(config, "app_id_agedys", 3)
        query = f"""
            SELECT ua.UsuarioRed, ua.Nombre, ua.CorreoUsuario
            FROM TbUsuariosAplicaciones ua
            INNER JOIN TbUsuariosAplicacionesPermisos uap ON ua.CorreoUsuario = uap.CorreoUsuario
            WHERE ua.ParaTareasProgramadas = True
            AND ua.FechaBaja IS NULL
            AND (uap.EsEconomia = True OR uap.EsEconomia = 'Sí')
            AND uap.IDAplicacion = {app_id_int}
        """

        result = db_connection.execute_query(query)
        return result

    except Exception as e:
        logger.error(f"Error obteniendo usuarios de economía (alternativo): {e}")
        return []


def get_users_with_fallback(
    user_type: str, db_connection, config, logger, app_id: str = None
):
    """
    Función que intenta usar las funciones originales de utils y si fallan por tabla inexistente,
    usa las funciones alternativas.

    Args:
        user_type: Tipo de usuario ('admin', 'technical', 'quality')
        app_id: ID de la aplicación (para technical y quality)
        config: Configuración de la aplicación
        logger: Logger para registrar eventos
        db_connection: Conexión a la base de datos (para admin)

    Returns:
        Lista de usuarios del tipo solicitado
    """
    try:
        # Determinar qué función de obtención de usuarios usar
        if user_type == "admin":
            from .utils import get_admin_users

            return get_admin_users(db_connection)
        elif user_type == "technical":
            # No existe una función específica para técnicos en utils, se usa la alternativa
            return get_technical_users_alternative(app_id, config, logger)
        elif user_type == "quality":
            # No existe una función específica para calidad en utils, se usa la alternativa
            return get_quality_users_alternative(app_id, config, logger)

    except Exception as e:
        # Si hay error (probablemente tabla inexistente), usar funciones alternativas
        if (
            "TbUsuariosAplicacionesTareas" in str(e)
            or "no such table" in str(e).lower()
        ):
            logger.warning(
                f"Tabla TbUsuariosAplicacionesTareas no encontrada, usando método alternativo para {user_type}"
            )

            if user_type == "admin":
                return get_admin_users_alternative(db_connection)
            elif user_type == "technical":
                return get_technical_users_alternative(app_id, config, logger)
            elif user_type == "quality":
                return get_quality_users_alternative(app_id, config, logger)
        else:
            # Re-lanzar el error si no es por tabla inexistente
            raise e

    return []
