#!/usr/bin/env python3
"""
Script para preparar datos de prueba de correos
Limpia FechaEnvio de algunos registros para que se envíen en la próxima ejecución
"""
import sys
from pathlib import Path
SRC_ROOT = Path(__file__).parent.parent / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from src.common.database import AccessDatabase
from src.common.config import config
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def prepare_correos_data():
    """Prepara datos de prueba en correos_datos.accdb"""
    db_path = Path(config.db_correos_path)
    logger.info(f"Preparando datos de prueba en: {db_path}")
    
    try:
        # Construir connection string reutilizando métodos de config
        conn_str = config.get_db_correos_connection_string()
        db = AccessDatabase(conn_str)
        with db.get_connection() as conn:
            from pyodbc import ProgrammingError
            cursor = conn.cursor()
            # Verificar correos existentes
            query = "SELECT TOP 5 IDCorreo, Aplicacion, Asunto, FechaEnvio FROM TbCorreosEnviados ORDER BY IDCorreo DESC"
            cursor.execute(query)
            columns = [c[0] for c in cursor.description]
            correos = [dict(zip(columns, r)) for r in cursor.fetchall()]
            
            if not correos:
                logger.warning("No hay correos en la base de datos")
                return
            
            logger.info(f"Encontrados {len(correos)} correos recientes")
            
            # Limpiar FechaEnvio de los primeros 2 correos para que se reenvíen
            correos_to_reset = correos[:2]
            
            for correo in correos_to_reset:
                id_correo = correo['IDCorreo']
                logger.info(f"Limpiando FechaEnvio del correo ID: {id_correo} - {correo['Asunto']}")
                
                update_query = f"UPDATE TbCorreosEnviados SET FechaEnvio = NULL WHERE IDCorreo = {id_correo}"
                try:
                    cursor.execute(update_query)
                    conn.commit()
                    logger.info(f"✓ Correo ID {id_correo} actualizado correctamente")
                except Exception as e:
                    logger.error(f"Error actualizando correo ID {id_correo}: {e}")
            
            # Verificar cambios
            query_check = "SELECT COUNT(*) as Total FROM TbCorreosEnviados WHERE FechaEnvio IS NULL"
            cursor.execute(query_check)
            row = cursor.fetchone()
            total_pendientes = row[0] if row else 0
            
            logger.info(f"Total de correos pendientes de envío: {total_pendientes}")
            
    except Exception as e:
        logger.error(f"Error preparando datos de correos: {e}")

def prepare_tareas_data():
    """Prepara datos de prueba en Tareas_datos1.accdb"""
    db_path = Path("c:/Users/adm1/Desktop/Proyectos/scripts-python/dbs-locales/Tareas_datos1.accdb")
    logger.info(f"Preparando datos de prueba en: {db_path}")
    
    try:
        conn_str = config.get_db_tareas_connection_string()
        db = AccessDatabase(conn_str)
        with db.get_connection() as conn:
            cursor = conn.cursor()
            # Verificar correos existentes
            query = "SELECT TOP 5 IDCorreo, Aplicacion, Asunto, FechaEnvio FROM TbCorreosEnviados ORDER BY IDCorreo DESC"
            cursor.execute(query)
            columns = [c[0] for c in cursor.description]
            correos = [dict(zip(columns, r)) for r in cursor.fetchall()]
            
            if not correos:
                logger.warning("No hay correos en la base de datos de tareas")
                return
            
            logger.info(f"Encontrados {len(correos)} correos recientes en tareas")
            
            # Limpiar FechaEnvio de los primeros 2 correos para que se reenvíen
            correos_to_reset = correos[:2]
            
            for correo in correos_to_reset:
                id_correo = correo['IDCorreo']
                logger.info(f"Limpiando FechaEnvio del correo ID: {id_correo} - {correo['Asunto']}")
                
                update_query = f"UPDATE TbCorreosEnviados SET FechaEnvio = NULL WHERE IDCorreo = {id_correo}"
                try:
                    cursor.execute(update_query)
                    conn.commit()
                    logger.info(f"✓ Correo ID {id_correo} actualizado correctamente")
                except Exception as e:
                    logger.error(f"Error actualizando correo ID {id_correo}: {e}")
            
            # Verificar cambios
            query_check = "SELECT COUNT(*) as Total FROM TbCorreosEnviados WHERE FechaEnvio IS NULL"
            cursor.execute(query_check)
            row = cursor.fetchone()
            total_pendientes = row[0] if row else 0
            
            logger.info(f"Total de correos pendientes de envío en tareas: {total_pendientes}")
            
    except Exception as e:
        logger.error(f"Error preparando datos de tareas: {e}")

if __name__ == "__main__":
    logger.info("=== Preparando datos de prueba para correos ===")
    prepare_correos_data()
    prepare_tareas_data()
    logger.info("=== Preparación completada ===")