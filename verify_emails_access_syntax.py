#!/usr/bin/env python3
"""
Script para verificar correos usando la sintaxis SQL exacta del test de integración
"""

import sys
import os
from datetime import datetime

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from common.database import AccessDatabase
from common.config import Config

def verificar_correos_access_syntax():
    """Verificar correos usando la sintaxis SQL exacta del test de integración"""
    
    print("=== VERIFICACIÓN CON SINTAXIS ACCESS ===")
    print(f"Fecha/Hora actual: {datetime.now()}")
    print()
    
    # Cargar configuración
    config = Config()
    
    # Conectar a la base de datos de tareas
    db_tareas = AccessDatabase(config.get_db_tareas_connection_string())
    
    try:
        # Verificar correos específicos usando la sintaxis del test
        print("--- Correos específicos (7516 y 7517) ---")
        
        # Primero obtener todos los correos y filtrar en Python
        query_all = """
        SELECT TbCorreosEnviados.*
        FROM TbCorreosEnviados
        """
        todos_correos = db_tareas.execute_query(query_all)
        
        # Filtrar correos específicos en Python
        correos_especificos = [c for c in todos_correos if c['IDCorreo'] in [7516, 7517]]
        
        for correo in correos_especificos:
            print(f"--- Correo ID: {correo['IDCorreo']} ---")
            print(f"  Asunto: {correo.get('Asunto', 'N/A')}")
            print(f"  Destinatarios: {correo.get('Destinatarios', 'N/A')}")
            print(f"  FechaCreacion: {correo.get('FechaCreacion', 'N/A')}")
            print(f"  FechaEnvio: {correo.get('FechaEnvio', 'N/A')}")
            
            if correo.get('FechaEnvio'):
                print(f"  ✅ ESTADO: ENVIADO")
            else:
                print(f"  ❌ ESTADO: PENDIENTE")
            print()
        
        if not correos_especificos:
            print("⚠️  Correos 7516 y 7517 no encontrados")
            print()
        
        # Verificar correos pendientes usando la consulta exacta del test
        print("--- CORREOS PENDIENTES (consulta del legacy) ---")
        query_pendientes = """
        SELECT TbCorreosEnviados.*
        FROM TbCorreosEnviados
        WHERE TbCorreosEnviados.FechaEnvio Is Null
        """
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
        query_enviados = """
        SELECT IDCorreo, FechaEnvio, Asunto
        FROM TbCorreosEnviados
        WHERE FechaEnvio IS NOT NULL
        ORDER BY FechaEnvio DESC
        """
        enviados = db_tareas.execute_query(query_enviados)
        
        if enviados:
            print(f"Mostrando últimos {min(len(enviados), 10)} correos enviados:")
            for i, correo in enumerate(enviados):
                if i >= 10:  # Mostrar solo los primeros 10
                    break
                print(f"  ID: {correo['IDCorreo']}, FechaEnvio: {correo['FechaEnvio']}")
        else:
            print("⚠️  No hay correos marcados como enviados")
        
        print()
        
        # Contar correos pendientes vs enviados
        print("--- ESTADÍSTICAS ---")
        
        # Contar correos pendientes
        query_count_pendientes = """
        SELECT COUNT(*) as total_pendientes
        FROM TbCorreosEnviados
        WHERE FechaEnvio IS NULL
        """
        result_pendientes = db_tareas.execute_query(query_count_pendientes)
        total_pendientes = result_pendientes[0]['total_pendientes']
        
        # Contar correos enviados
        query_count_enviados = """
        SELECT COUNT(*) as total_enviados
        FROM TbCorreosEnviados
        WHERE FechaEnvio IS NOT NULL
        """
        result_enviados = db_tareas.execute_query(query_count_enviados)
        total_enviados = result_enviados[0]['total_enviados']
        
        print(f"Total correos pendientes: {total_pendientes}")
        print(f"Total correos enviados: {total_enviados}")
        print(f"Total correos: {total_pendientes + total_enviados}")
            
    except Exception as e:
        print(f"❌ Error durante la verificación: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db_tareas.disconnect()

if __name__ == "__main__":
    verificar_correos_access_syntax()