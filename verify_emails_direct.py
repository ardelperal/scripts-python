#!/usr/bin/env python3
"""
Script directo para verificar correos usando consultas SQL básicas
"""

import sys
import os
from datetime import datetime

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from common.database import AccessDatabase
from common.config import Config

def verificar_correos_directo():
    """Verificar correos usando consultas SQL directas"""
    
    print("=== VERIFICACIÓN DIRECTA DE CORREOS ===")
    print(f"Fecha/Hora actual: {datetime.now()}")
    print()
    
    # Cargar configuración
    config = Config()
    
    # Conectar a la base de datos de tareas
    db_tareas = AccessDatabase(config.get_db_tareas_connection_string())
    
    try:
        # Verificar correo 7516
        print("--- Correo ID: 7516 ---")
        query1 = "SELECT IDCorreo, Asunto, Destinatarios, FechaEnvio, FechaCreacion FROM TbCorreosEnviados WHERE IDCorreo = 7516"
        resultado1 = db_tareas.execute_query(query1)
        
        if resultado1:
            correo = resultado1[0]
            print(f"  Asunto: {correo.get('Asunto', 'N/A')}")
            print(f"  Destinatarios: {correo.get('Destinatarios', 'N/A')}")
            print(f"  FechaCreacion: {correo.get('FechaCreacion', 'N/A')}")
            print(f"  FechaEnvio: {correo.get('FechaEnvio', 'N/A')}")
            
            if correo.get('FechaEnvio'):
                print(f"  ✅ ESTADO: ENVIADO")
            else:
                print(f"  ❌ ESTADO: PENDIENTE")
        else:
            print(f"  ⚠️  Correo no encontrado")
        
        print()
        
        # Verificar correo 7517
        print("--- Correo ID: 7517 ---")
        query2 = "SELECT IDCorreo, Asunto, Destinatarios, FechaEnvio, FechaCreacion FROM TbCorreosEnviados WHERE IDCorreo = 7517"
        resultado2 = db_tareas.execute_query(query2)
        
        if resultado2:
            correo = resultado2[0]
            print(f"  Asunto: {correo.get('Asunto', 'N/A')}")
            print(f"  Destinatarios: {correo.get('Destinatarios', 'N/A')}")
            print(f"  FechaCreacion: {correo.get('FechaCreacion', 'N/A')}")
            print(f"  FechaEnvio: {correo.get('FechaEnvio', 'N/A')}")
            
            if correo.get('FechaEnvio'):
                print(f"  ✅ ESTADO: ENVIADO")
            else:
                print(f"  ❌ ESTADO: PENDIENTE")
        else:
            print(f"  ⚠️  Correo no encontrado")
        
        print()
        
        # Verificar todos los correos pendientes
        print("--- CORREOS PENDIENTES ---")
        query_pendientes = "SELECT IDCorreo, Asunto, FechaCreacion FROM TbCorreosEnviados WHERE FechaEnvio IS NULL ORDER BY IDCorreo DESC"
        pendientes = db_tareas.execute_query(query_pendientes)
        
        if pendientes:
            print(f"Total de correos pendientes: {len(pendientes)}")
            for i, correo in enumerate(pendientes):
                if i >= 10:  # Mostrar solo los primeros 10
                    break
                asunto = correo.get('Asunto', 'N/A')
                if asunto and len(asunto) > 50:
                    asunto = asunto[:50] + "..."
                print(f"  ID: {correo['IDCorreo']}, Asunto: {asunto}")
        else:
            print("✅ No hay correos pendientes")
        
        print()
        
        # Verificar últimos correos enviados
        print("--- ÚLTIMOS CORREOS ENVIADOS ---")
        query_enviados = "SELECT IDCorreo, Asunto, FechaEnvio FROM TbCorreosEnviados WHERE FechaEnvio IS NOT NULL ORDER BY FechaEnvio DESC"
        enviados = db_tareas.execute_query(query_enviados)
        
        if enviados:
            print(f"Mostrando últimos {min(len(enviados), 10)} correos enviados:")
            for i, correo in enumerate(enviados):
                if i >= 10:  # Mostrar solo los primeros 10
                    break
                print(f"  ID: {correo['IDCorreo']}, FechaEnvio: {correo['FechaEnvio']}")
        else:
            print("⚠️  No hay correos marcados como enviados")
            
    except Exception as e:
        print(f"❌ Error durante la verificación: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db_tareas.disconnect()

if __name__ == "__main__":
    verificar_correos_directo()