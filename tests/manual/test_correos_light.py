#!/usr/bin/env python3
"""
Script de prueba para verificar la funcionalidad de base de datos de correos ligera
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv
import win32com.client
import pythoncom

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_correos_light.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def test_correos_database_structure():
    """Prueba la estructura de la base de datos de correos"""
    load_dotenv()
    
    # Obtener rutas
    office_path = os.getenv('OFFICE_DB_CORREOS')
    local_path = os.getenv('LOCAL_DB_CORREOS')
    db_password = os.getenv('DB_PASSWORD', '')
    
    if not office_path or not local_path:
        logger.error("Variables de entorno no encontradas")
        return False
    
    # Convertir a ruta absoluta si es relativa
    project_root = Path(__file__).parent
    if not os.path.isabs(local_path):
        local_path = project_root / local_path
    
    logger.info(f"Base de datos oficina: {office_path}")
    logger.info(f"Base de datos local: {local_path}")
    
    if not os.path.exists(office_path):
        logger.error(f"Base de datos de oficina no encontrada: {office_path}")
        return False
    
    access_app = None
    
    try:
        # Inicializar COM
        pythoncom.CoInitialize()
        
        # Crear aplicación Access
        access_app = win32com.client.Dispatch("Access.Application")
        access_app.Visible = False
        access_app.UserControl = False
        
        # Abrir base de datos de oficina
        logger.info("Conectando a base de datos de oficina...")
        if db_password:
            access_app.OpenCurrentDatabase(office_path, True, db_password)
        else:
            access_app.OpenCurrentDatabase(office_path, True)
        
        access_app.DoCmd.SetWarnings(False)
        
        # Obtener información de tablas
        db = access_app.CurrentDb()
        logger.info(f"Tablas encontradas en la base de datos:")
        
        tables_info = []
        for i in range(db.TableDefs.Count):
            table_def = db.TableDefs(i)
            table_name = table_def.Name
            
            # Filtrar tablas del sistema
            if (not table_name.startswith('MSys') and 
                not table_name.startswith('~')):
                
                is_linked = hasattr(table_def, 'Connect') and table_def.Connect
                table_type = "Vinculada" if is_linked else "Local"
                
                # Contar registros si es tabla local
                record_count = "N/A"
                if not is_linked:
                    try:
                        rs = access_app.CurrentDb().OpenRecordset(f"SELECT COUNT(*) FROM [{table_name}]")
                        if not rs.EOF:
                            record_count = rs.Fields(0).Value
                        rs.Close()
                    except Exception as e:
                        record_count = f"Error: {e}"
                
                tables_info.append((table_name, table_type, record_count))
                logger.info(f"  - {table_name} ({table_type}) - {record_count} registros")
        
        # Identificar tabla principal
        main_tables = [t for t in tables_info if t[1] == "Local" and isinstance(t[2], int)]
        if main_tables:
            # Ordenar por número de registros (descendente)
            main_tables.sort(key=lambda x: x[2], reverse=True)
            main_table = main_tables[0]
            logger.info(f"Tabla principal identificada: {main_table[0]} con {main_table[2]} registros")
            
            # Mostrar estructura de la tabla principal
            logger.info(f"Estructura de la tabla {main_table[0]}:")
            table_def = db.TableDefs(main_table[0])
            for j in range(table_def.Fields.Count):
                field = table_def.Fields(j)
                logger.info(f"  - {field.Name}: {field.Type}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error analizando base de datos: {e}")
        return False
        
    finally:
        try:
            if access_app:
                access_app.DoCmd.SetWarnings(True)
                access_app.CloseCurrentDatabase()
                access_app.Quit()
        except:
            pass
        
        try:
            pythoncom.CoUninitialize()
        except:
            pass

def test_local_correos_database():
    """Prueba la base de datos local de correos después de la configuración ligera"""
    load_dotenv()
    
    local_path = os.getenv('LOCAL_DB_CORREOS')
    db_password = os.getenv('DB_PASSWORD', '')
    
    if not local_path:
        logger.error("Variable LOCAL_DB_CORREOS no encontrada")
        return False
    
    # Convertir a ruta absoluta si es relativa
    project_root = Path(__file__).parent
    if not os.path.isabs(local_path):
        local_path = project_root / local_path
    
    if not os.path.exists(local_path):
        logger.warning(f"Base de datos local no existe: {local_path}")
        return False
    
    access_app = None
    
    try:
        # Inicializar COM
        pythoncom.CoInitialize()
        
        # Crear aplicación Access
        access_app = win32com.client.Dispatch("Access.Application")
        access_app.Visible = False
        access_app.UserControl = False
        
        # Abrir base de datos local
        logger.info("Conectando a base de datos local...")
        if db_password:
            access_app.OpenCurrentDatabase(str(local_path), False, db_password)
        else:
            access_app.OpenCurrentDatabase(str(local_path), False)
        
        access_app.DoCmd.SetWarnings(False)
        
        # Verificar contenido
        db = access_app.CurrentDb()
        logger.info("Contenido de la base de datos local:")
        
        for i in range(db.TableDefs.Count):
            table_def = db.TableDefs(i)
            table_name = table_def.Name
            
            if (not table_name.startswith('MSys') and 
                not table_name.startswith('~')):
                
                try:
                    rs = access_app.CurrentDb().OpenRecordset(f"SELECT COUNT(*) FROM [{table_name}]")
                    if not rs.EOF:
                        record_count = rs.Fields(0).Value
                    rs.Close()
                    
                    logger.info(f"  - {table_name}: {record_count} registros")
                    
                    if record_count > 0:
                        # Mostrar algunos datos de ejemplo
                        rs = access_app.CurrentDb().OpenRecordset(f"SELECT TOP 3 * FROM [{table_name}]")
                        field_names = [rs.Fields(j).Name for j in range(rs.Fields.Count)]
                        logger.info(f"    Campos: {', '.join(field_names)}")
                        rs.Close()
                        
                except Exception as e:
                    logger.error(f"    Error accediendo a {table_name}: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error verificando base de datos local: {e}")
        return False
        
    finally:
        try:
            if access_app:
                access_app.DoCmd.SetWarnings(True)
                access_app.CloseCurrentDatabase()
                access_app.Quit()
        except:
            pass
        
        try:
            pythoncom.CoUninitialize()
        except:
            pass

def main():
    """Función principal"""
    logger.info("=== PRUEBA DE BASE DE DATOS DE CORREOS LIGERA ===")
    
    logger.info("\n1. Analizando estructura de base de datos de oficina...")
    if test_correos_database_structure():
        logger.info("✓ Análisis de estructura completado")
    else:
        logger.error("✗ Error en análisis de estructura")
        return 1
    
    logger.info("\n2. Verificando base de datos local...")
    if test_local_correos_database():
        logger.info("✓ Verificación de base local completada")
    else:
        logger.info("ℹ Base de datos local no existe o está vacía (normal antes de ejecutar setup)")
    
    logger.info("\n=== PRUEBA COMPLETADA ===")
    return 0

if __name__ == "__main__":
    exit(main())