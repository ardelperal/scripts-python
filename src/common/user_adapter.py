"""
Adaptador para manejar usuarios cuando la tabla TbUsuariosAplicacionesTareas no existe.
Este módulo proporciona funciones alternativas que usan TbUsuariosAplicacionesPermisos.
"""

import logging
from typing import List, Dict


def get_admin_users_alternative(db_connection) -> List[Dict[str, str]]:
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


def get_technical_users_alternative(app_id: str, config, logger) -> List[Dict[str, str]]:
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
        logger.error(f"Error obteniendo usuarios técnicos para {app_id} (alternativo): {e}")
        return []


def get_quality_users_alternative(app_id: str, config, logger) -> List[Dict[str, str]]:
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
    try:
        from .database import AccessDatabase
        
        # Usar la conexión de tareas para obtener usuarios
        db_connection = AccessDatabase(config.get_db_tareas_connection_string())
        
        query = """
            SELECT ua.UsuarioRed, ua.Nombre, ua.CorreoUsuario 
            FROM TbUsuariosAplicaciones ua 
            INNER JOIN TbUsuariosAplicacionesPermisos uap ON ua.CorreoUsuario = uap.CorreoUsuario 
            WHERE ua.ParaTareasProgramadas = True 
            AND ua.FechaBaja IS NULL 
            AND uap.EsUsuarioCalidad = 'Sí'
            AND uap.IDAplicacion = ?
        """
        
        result = db_connection.execute_query(query, (app_id,))
        return result
        
    except Exception as e:
        logger.error(f"Error obteniendo usuarios de calidad para {app_id} (alternativo): {e}")
        return []


def get_economy_users_alternative(config, logger) -> List[Dict[str, str]]:
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
        
        # Para usuarios de economía, usamos la tabla de permisos con ID de aplicación
        query = """
            SELECT ua.UsuarioRed, ua.Nombre, ua.CorreoUsuario 
            FROM TbUsuariosAplicaciones ua 
            INNER JOIN TbUsuariosAplicacionesPermisos uap ON ua.CorreoUsuario = uap.CorreoUsuario 
            WHERE ua.ParaTareasProgramadas = True 
            AND ua.FechaBaja IS NULL 
            AND uap.EsEconomia = 'Sí'
            AND uap.IDAplicacion = ?
        """
        
        result = db_connection.execute_query(query, [config.app_id_agedys])
        return result
        
    except Exception as e:
        logger.error(f"Error obteniendo usuarios de economía (alternativo): {e}")
        return []


def get_users_with_fallback(user_type: str, app_id: str = None, config=None, logger=None, db_connection=None):
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
        # Intentar usar las funciones originales primero
        if user_type == 'admin':
            from .utils import get_admin_users
            return get_admin_users(db_connection)
        elif user_type == 'technical':
            from .utils import get_technical_users
            return get_technical_users(app_id, config, logger)
        elif user_type == 'quality':
            from .utils import get_quality_users
            return get_quality_users(app_id, config, logger)
            
    except Exception as e:
        # Si hay error (probablemente tabla inexistente), usar funciones alternativas
        if "TbUsuariosAplicacionesTareas" in str(e) or "no such table" in str(e).lower():
            logger.warning(f"Tabla TbUsuariosAplicacionesTareas no encontrada, usando método alternativo para {user_type}")
            
            if user_type == 'admin':
                return get_admin_users_alternative(db_connection)
            elif user_type == 'technical':
                return get_technical_users_alternative(app_id, config, logger)
            elif user_type == 'quality':
                return get_quality_users_alternative(app_id, config, logger)
        else:
            # Re-lanzar el error si no es por tabla inexistente
            raise e
    
    return []