#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from common.database_adapter import AccessAdapter
from common.config import config

with AccessAdapter(Path(config.db_correos_path), config.db_password) as db:
    query = "SELECT IDCorreo, Aplicacion, Asunto, Destinatarios, FechaEnvio FROM TbCorreosEnviados WHERE IDCorreo = 16879"
    result = db.execute_query(query)
    if result:
        for row in result:
            print(f"ID: {row['IDCorreo']}, Asunto: {row['Asunto']}, FechaEnvio: {row['FechaEnvio']}")
    else:
        print("No se encontró el correo ID 16879")