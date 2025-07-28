#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from common.database_adapter import AccessAdapter
from common.config import config

# Eliminar el correo de prueba con IDCorreo NULL y crear uno nuevo correctamente
with AccessAdapter(Path(config.db_correos_path), config.db_password) as db:
    # Primero eliminar el correo con IDCorreo NULL
    delete_query = "DELETE FROM TbCorreosEnviados WHERE IDCorreo IS NULL"
    db.execute_non_query(delete_query)
    print("Correo con IDCorreo NULL eliminado")
    
    # Insertar un nuevo correo de prueba sin especificar IDCorreo (para que sea autonumérico)
    insert_query = """
    INSERT INTO TbCorreosEnviados 
    (Aplicacion, Destinatarios, Asunto, Cuerpo) 
    VALUES (?, ?, ?, ?)
    """
    
    db.execute_non_query(insert_query, (
        "TestApp",
        "test@example.com",
        "Correo de Prueba SMTP - Nuevo",
        "<h1>Prueba de Envío SMTP</h1><p>Este es un correo de prueba para verificar que el sistema SMTP funciona correctamente con ID autonumérico.</p>"
    ))
    
    print("Nuevo correo de prueba insertado exitosamente")
    
    # Verificar el correo insertado
    query = "SELECT TOP 1 * FROM TbCorreosEnviados WHERE FechaEnvio IS NULL ORDER BY IDCorreo DESC"
    result = db.execute_query(query)
    
    if result:
        print("Correo insertado:")
        for key, value in result[0].items():
            print(f"  {key}: {value}")
    else:
        print("No se encontró el correo insertado")