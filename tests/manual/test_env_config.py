#!/usr/bin/env python3
"""
Script de prueba para verificar la configuración del .env
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Configurar logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def test_env_configuration():
    """Prueba la configuración del .env"""
    
    # Cargar variables de entorno
    project_root = Path(__file__).parent
    env_path = project_root / '.env'
    
    if not env_path.exists():
        logger.error(f"Archivo .env no encontrado en: {env_path}")
        return False
    
    load_dotenv(env_path)
    logger.info(f"Cargando configuración desde: {env_path}")
    
    # Definir pares de variables esperadas
    database_pairs = [
        ('DB_BRASS_PATH_OFFICE', 'DB_BRASS_PATH_LOCAL', 'Brass_Datos.accdb'),
        ('DB_TAREAS_PATH_OFFICE', 'DB_TAREAS_PATH_LOCAL', 'Tareas_datos1.accdb'),
        ('DB_CORREOS_PATH_OFFICE', 'DB_CORREOS_PATH_LOCAL', 'Correos_Datos.accdb'),
        ('DB_NOCONFORMIDADES_PATH_OFFICE', 'DB_NOCONFORMIDADES_PATH_LOCAL', 'NoConformidades_Datos.accdb'),
        ('DB_LANZADERA_PATH_OFFICE', 'DB_LANZADERA_PATH_LOCAL', 'Lanzadera_Datos.accdb'),
        ('DB_RIESGOS_PATH_OFFICE', 'DB_RIESGOS_PATH_LOCAL', 'Riesgos_Datos.accdb'),
    ]
    
    logger.info("=== CONFIGURACIÓN DE BASES DE DATOS ===")
    
    all_configured = True
    
    for office_var, local_var, expected_filename in database_pairs:
        office_path = os.getenv(office_var)
        local_path = os.getenv(local_var)
        
        db_name = office_var.replace('DB_', '').replace('_PATH_OFFICE', '')
        
        logger.info(f"\n📁 {db_name}:")
        logger.info(f"  Archivo esperado: {expected_filename}")
        
        # Verificar variable de oficina
        if office_path:
            logger.info(f"  Oficina ({office_var}): {office_path}")
            office_exists = os.path.exists(office_path)
            logger.info(f"  Estado oficina: {'✅' if office_exists else '❌'}")
            
            # Verificar nombre de archivo
            office_filename = os.path.basename(office_path)
            if office_filename.lower() == expected_filename.lower():
                logger.info(f"  Nombre archivo: ✅")
            else:
                logger.warning(f"  Nombre archivo: ❌ (esperado: {expected_filename}, encontrado: {office_filename})")
        else:
            logger.warning(f"  Oficina ({office_var}): ❌ NO CONFIGURADO")
            all_configured = False
        
        # Verificar variable local
        if local_path:
            # Convertir a ruta absoluta si es relativa
            if not os.path.isabs(local_path):
                local_path_abs = str(project_root / local_path)
            else:
                local_path_abs = local_path
                
            logger.info(f"  Local ({local_var}): {local_path}")
            logger.info(f"  Ruta absoluta local: {local_path_abs}")
            
            local_exists = os.path.exists(local_path_abs)
            logger.info(f"  Estado local: {'✅' if local_exists else '❌'}")
            
            # Verificar directorio padre
            local_dir = os.path.dirname(local_path_abs)
            dir_exists = os.path.exists(local_dir)
            logger.info(f"  Directorio local: {'✅' if dir_exists else '❌'}")
            
        else:
            logger.warning(f"  Local ({local_var}): ❌ NO CONFIGURADO")
            all_configured = False
    
    # Verificar otras configuraciones importantes
    logger.info("\n=== OTRAS CONFIGURACIONES ===")
    
    other_vars = [
        'ENVIRONMENT',
        'SMTP_SERVER',
        'SMTP_PORT',
        'SMTP_USER',
        'SMTP_PASSWORD',
        'APP_ID_BRASS',
        'APP_ID_TAREAS',
        'APP_ID_CORREOS',
        'APP_ID_NOCONFORMIDADES',
        'APP_ID_LANZADERA',
        'APP_ID_RIESGOS'
    ]
    
    for var in other_vars:
        value = os.getenv(var)
        if value:
            # Ocultar contraseñas
            if 'PASSWORD' in var:
                display_value = '*' * len(value)
            else:
                display_value = value
            logger.info(f"  {var}: {display_value}")
        else:
            logger.warning(f"  {var}: ❌ NO CONFIGURADO")
    
    logger.info("=" * 50)
    
    if all_configured:
        logger.info("✅ Todas las bases de datos están configuradas")
        return True
    else:
        logger.warning("⚠️ Algunas configuraciones están incompletas")
        return False

def main():
    """Función principal"""
    print("=" * 60)
    print("VERIFICACIÓN DE CONFIGURACIÓN .ENV")
    print("=" * 60)
    print()
    
    try:
        success = test_env_configuration()
        
        print()
        print("=" * 60)
        if success:
            print("✅ CONFIGURACIÓN VERIFICADA CORRECTAMENTE")
        else:
            print("⚠️ CONFIGURACIÓN INCOMPLETA")
        print("=" * 60)
        
        return 0 if success else 1
        
    except Exception as e:
        logger.error(f"❌ Error verificando configuración: {e}")
        return 1

if __name__ == "__main__":
    exit(main())