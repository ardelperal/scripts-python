"""
Script para verificar los destinatarios de los correos en la tabla TbCorreosEnviados
de la base de datos de Tareas.
"""
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))

from common.database import AccessDatabase
from common.config import Config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def check_recipients():
    """Verifica los destinatarios de los correos en la base de datos."""
    logging.info("Iniciando la verificación de destinatarios de correos...")
    
    config = Config()
    connection_string = config.get_db_tareas_connection_string()

    try:
        db = AccessDatabase(connection_string)
        db.connect()

        # 1. Analizar el correo específico IDCorreo = 7590
        logging.info("--- ANÁLISIS DEL CORREO ID: 7590 ---")
        query_specific = "SELECT * FROM TbCorreosEnviados WHERE IDCorreo = ?"
        results = db.execute_query(query_specific, (7590,))
        if results:
            record = results[0]
            logging.info(f"IDCorreo: {record['IDCorreo']}")
            logging.info(f"Asunto: {record['Asunto']}")
            logging.info(f"Destinatarios: '{record['Destinatarios']}'")
            logging.info(f"Copia: '{record['DestinatariosConCopia']}'")
            logging.info(f"Copia Oculta: '{record['DestinatariosConCopiaOculta']}'")
        else:
            logging.warning("No se encontró el correo con ID: 7590")

        # 2. Buscar todos los correos sin ningún destinatario
        logging.info("\n--- ANÁLISIS DE CORREOS SIN DESTINATARIOS ---")
        query_all = """
        SELECT IDCorreo, Asunto, Destinatarios, DestinatariosConCopia, DestinatariosConCopiaOculta
        FROM TbCorreosEnviados
        WHERE (Destinatarios IS NULL OR Destinatarios = '')
          AND (DestinatariosConCopia IS NULL OR DestinatariosConCopia = '')
          AND (DestinatariosConCopiaOculta IS NULL OR DestinatariosConCopiaOculta = '')
        """
        records = db.execute_query(query_all)

        if records:
            logging.warning(f"Se encontraron {len(records)} correos sin ningún destinatario:")
            for rec in records:
                logging.warning(f"  - IDCorreo: {rec['IDCorreo']}, Asunto: {rec['Asunto']}")
        else:
            logging.info("Todos los correos tienen al menos un destinatario en los campos 'Para', 'CC' o 'CCO'.")
        logging.info("\nVerificación completada.")

    except Exception as e:
        logging.error(f"Error durante la verificación: {e}")

if __name__ == "__main__":
    check_recipients()