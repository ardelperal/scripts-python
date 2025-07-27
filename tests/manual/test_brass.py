#!/usr/bin/env python3
"""
Script de prueba para el módulo BRASS adaptado
"""

import sys
import os
import logging

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from brass.brass_manager import BrassManager

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Función principal de prueba"""
    try:
        logger.info("Iniciando prueba del módulo BRASS...")
        
        # Crear instancia del manager
        brass_manager = BrassManager()
        
        # Probar obtención de usuarios administradores
        logger.info("Probando obtención de usuarios administradores...")
        
        usuarios_admin = brass_manager.get_admin_users()
        logger.info(f"Usuarios administradores encontrados: {len(usuarios_admin)}")
        
        # Mostrar algunos detalles de los usuarios
        if usuarios_admin:
            logger.info(f"Primer usuario admin: {usuarios_admin[0].get('NombreUsuario', 'N/A')}")
        
        # Probar obtención de cadena de correos
        emails_admin = brass_manager.get_admin_emails_string()
        logger.info(f"Emails administradores: {emails_admin}")
        
        logger.info("Prueba completada exitosamente")
        
    except Exception as e:
        logger.error(f"Error en la prueba: {e}")
        raise
    finally:
        # Cerrar conexiones si existen
        if 'brass_manager' in locals():
            try:
                brass_manager.db_brass.close()
                brass_manager.db_tareas.close()
                logger.info("Conexiones cerradas")
            except:
                pass

if __name__ == "__main__":
    main()