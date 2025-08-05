#!/usr/bin/env python3
"""
Script para verificar el estado específico de los correos 7516 y 7517
que aparecen en los logs como enviados pero en el diagnóstico como pendientes
"""

import sys
import os
from datetime import datetime

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from common.database import AccessDatabase
from common.config import Config

def verificar_correos_especificos():
    """Verificar el estado de los correos 7516 y 7517"""
    
    print("=== VERIFICACIÓN DE CORREOS ESPECÍFICOS ===")
    print(f"Fecha/Hora actual: {datetime.now()}")
    print()
    
    # Cargar configuración
    config = Config()
    
    # Conectar a la base de datos de tareas
    db_tareas = AccessDatabase(config.get_db_tareas_connection_string())
    
    try:
        # Verificar correos específicos
        correos_ids = [7516, 7517]
        
        for correo_id in correos_ids:
            print(f"--- Correo ID: {correo_id} ---")
            
            # Consulta específica para este correo
            query = """
                SELECT IDCorreo, Asunto, Destinatarios, FechaEnvio, FechaCreacion
                FROM TbCorreosEnviados 
                WHERE IDCorreo = {}
            """.format(correo_id)
            
            resultado = db_tareas.execute_query(query)
            
            if resultado:
                correo = resultado[0]
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
        
        # Verificar todos los correos pendientes actuales
        print("--- TODOS LOS CORREOS PENDIENTES ACTUALES ---")
        query_pendientes = """
            SELECT IDCorreo, Asunto, FechaCreacion, FechaEnvio
            FROM TbCorreosEnviados 
            WHERE FechaEnvio IS NULL
            ORDER BY IDCorreo DESC
        """
        
        pendientes = db_tareas.execute_query(query_pendientes)
        
        if pendientes:
            print(f"Total de correos pendientes: {len(pendientes)}")
            for correo in pendientes[:10]:  # Mostrar solo los primeros 10
                print(f"  ID: {correo['IDCorreo']}, Asunto: {correo.get('Asunto', 'N/A')[:50]}...")
        else:
            print("✅ No hay correos pendientes")
        
        print()
        
        # Verificar los últimos correos enviados
        print("--- ÚLTIMOS 10 CORREOS ENVIADOS ---")
        query_enviados = """
            SELECT IDCorreo, Asunto, FechaEnvio
            FROM TbCorreosEnviados 
            WHERE FechaEnvio IS NOT NULL
            ORDER BY FechaEnvio DESC
        """
        
        enviados = db_tareas.execute_query(query_enviados)
        
        if enviados:
            print(f"Total de correos enviados: {len(enviados)}")
            for correo in enviados[:10]:  # Mostrar solo los primeros 10
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
    verificar_correos_especificos()