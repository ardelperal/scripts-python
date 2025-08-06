"""
Script de migración para agregar los campos 'Enviado' y 'Notas' a la tabla 'TbCorreosEnviados'
en la base de datos de Tareas.
"""
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / 'src'))

from common.database import AccessDatabase
from common.config import config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def migrate_database():
    """Añade las columnas necesarias a la base de datos de tareas."""
    logging.info("Iniciando migración de la base de datos de Tareas...")
    
    db_path = config._get_db_path('tareas')
    if not db_path or not Path(db_path).exists():
        logging.error(f"La ruta de la base de datos de tareas no es válida o no existe: {db_path}")
        return

    try:
        db = AccessDatabase(db_path)
        conn = db.get_connection()
        cursor = conn.cursor()

        # Verificar si la columna 'Enviado' existe
        try:
            cursor.execute("SELECT Enviado FROM TbCorreosEnviados")
            logging.info("La columna 'Enviado' ya existe en 'TbCorreosEnviados'.")
        except Exception:
            logging.info("Añadiendo columna 'Enviado' a 'TbCorreosEnviados'...")
            cursor.execute("ALTER TABLE TbCorreosEnviados ADD COLUMN Enviado YESNO")
            conn.commit()
            logging.info("Columna 'Enviado' añadida correctamente.")

        # Verificar si la columna 'Notas' existe
        try:
            cursor.execute("SELECT Notas FROM TbCorreosEnviados")
            logging.info("La columna 'Notas' ya existe en 'TbCorreosEnviados'.")
        except Exception:
            logging.info("Añadiendo columna 'Notas' a 'TbCorreosEnviados'...")
            cursor.execute("ALTER TABLE TbCorreosEnviados ADD COLUMN Notas TEXT(255)")
            conn.commit()
            logging.info("Columna 'Notas' añadida correctamente.")

        cursor.close()
        conn.close()
        logging.info("Migración de la base de datos de Tareas completada con éxito.")

    except Exception as e:
        logging.error(f"Error durante la migración de la base de datos: {e}")

if __name__ == "__main__":
    migrate_database()