#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from common.database_adapter import AccessAdapter
from common.config import config

# Insertar un correo de prueba
with AccessAdapter(Path(config.db_correos_path), config.db_password) as db:
    insert_query = """
    INSERT INTO TbCorreosEnviados 
    (Aplicacion, Destinatarios, Asunto, Cuerpo, FechaEnvio) 
    VALUES (?, ?, ?, ?, ?)
    """
    
    db.execute_non_query(insert_query, (
        "TestApp",
        "test@example.com",
        "Correo de Prueba SMTP",
        "<h1>Prueba de Envío SMTP</h1><p>Este es un correo de prueba para verificar que el sistema SMTP funciona correctamente.</p>",
        None  # FechaEnvio NULL para que sea procesado
    ))
    
    print("Correo de prueba insertado exitosamente")