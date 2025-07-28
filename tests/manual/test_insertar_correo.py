#!/usr/bin/env python3
"""
Script para probar el método insertar_correo del CorreosManager
que usa la regla del máximo + 1 para obtener el IDCorreo
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from correos.correos_manager import CorreosManager

def main():
    print("=== Prueba del método insertar_correo ===")
    
    # Crear instancia del gestor de correos
    correos_manager = CorreosManager()
    
    # Insertar un correo de prueba usando el método correcto
    id_correo = correos_manager.insertar_correo(
        aplicacion="TestApp",
        asunto="Correo de Prueba SMTP - Con ID Correcto",
        cuerpo="<h1>Prueba de Envío SMTP</h1><p>Este correo usa el método insertar_correo que implementa la regla del máximo + 1 para el IDCorreo.</p>",
        destinatarios="test@example.com",
        destinatarios_bcc="admin@example.com"
    )
    
    if id_correo > 0:
        print(f"✅ Correo insertado exitosamente con ID: {id_correo}")
    else:
        print("❌ Error insertando el correo")
        return False
    
    # Verificar que el correo se insertó correctamente
    from common.database_adapter import AccessAdapter
    from common.config import config
    
    with AccessAdapter(Path(config.db_correos_path), config.db_password) as db:
        query = "SELECT * FROM TbCorreosEnviados WHERE IDCorreo = ?"
        result = db.execute_query(query, (id_correo,))
        
        if result:
            print("\n📧 Datos del correo insertado:")
            for key, value in result[0].items():
                print(f"  {key}: {value}")
        else:
            print("❌ No se encontró el correo insertado")
            return False
    
    print("\n✅ Prueba completada exitosamente")
    return True

if __name__ == "__main__":
    main()