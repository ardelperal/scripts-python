#!/usr/bin/env python3
"""
Herramienta para probar las consultas SQL de get_distinct_technical_users
en la base de datos de riesgos y diagnosticar por qué no se obtienen usuarios.
"""

import os
import sys
from pathlib import Path

# Agregar el directorio src al path para importar módulos
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from common.database import AccessDatabase
from common.config import Config

def test_riesgos_queries():
    """
    Ejecuta las 8 consultas SQL de get_distinct_technical_users para diagnosticar
    por qué no se están obteniendo usuarios técnicos con tareas pendientes.
    """
    
    # Las 8 consultas exactas de get_distinct_technical_users
    queries = {
        "1. Ediciones que necesitan publicación": """
            SELECT DISTINCT TbProyectosEdiciones.UsuarioRed, TbUsuariosAplicaciones.Nombre, TbUsuariosAplicaciones.CorreoUsuario
            FROM TbProyectosEdiciones 
            INNER JOIN TbUsuariosAplicaciones ON TbProyectosEdiciones.UsuarioRed = TbUsuariosAplicaciones.UsuarioRed
            WHERE TbProyectosEdiciones.FechaPublicacion IS NULL 
              AND TbProyectosEdiciones.FechaPropuestaPublicacion IS NOT NULL 
              AND TbProyectosEdiciones.FechaPropuestaPublicacionRechazada IS NULL
        """,
        
        "2. Ediciones con propuesta de publicación rechazada": """
            SELECT DISTINCT TbProyectosEdiciones.UsuarioRed, TbUsuariosAplicaciones.Nombre, TbUsuariosAplicaciones.CorreoUsuario
            FROM TbProyectosEdiciones 
            INNER JOIN TbUsuariosAplicaciones ON TbProyectosEdiciones.UsuarioRed = TbUsuariosAplicaciones.UsuarioRed
            WHERE TbProyectosEdiciones.FechaPropuestaPublicacionRechazada IS NOT NULL 
              AND TbProyectosEdiciones.FechaPublicacion IS NULL
        """,
        
        "3. Riesgos aceptados no motivados": """
            SELECT DISTINCT TbRiesgos.UsuarioRed, TbUsuariosAplicaciones.Nombre, TbUsuariosAplicaciones.CorreoUsuario
            FROM TbRiesgos 
            INNER JOIN TbUsuariosAplicaciones ON TbRiesgos.UsuarioRed = TbUsuariosAplicaciones.UsuarioRed
            WHERE TbRiesgos.FechaJustificacionAceptacionRiesgo IS NOT NULL 
              AND TbRiesgos.ParaInformeAvisos <> 'No' 
              AND TbRiesgos.FechaJustificacionAceptacionRiesgoRechazada IS NULL 
              AND TbRiesgos.JustificacionAceptacionRiesgo IS NULL
        """,
        
        "4. Riesgos aceptados rechazados": """
            SELECT DISTINCT TbRiesgos.UsuarioRed, TbUsuariosAplicaciones.Nombre, TbUsuariosAplicaciones.CorreoUsuario
            FROM TbRiesgos 
            INNER JOIN TbUsuariosAplicaciones ON TbRiesgos.UsuarioRed = TbUsuariosAplicaciones.UsuarioRed
            WHERE TbRiesgos.FechaJustificacionAceptacionRiesgoRechazada IS NOT NULL 
              AND TbRiesgos.ParaInformeAvisos <> 'No'
        """,
        
        "5. Riesgos retirados no motivados": """
            SELECT DISTINCT TbRiesgos.UsuarioRed, TbUsuariosAplicaciones.Nombre, TbUsuariosAplicaciones.CorreoUsuario
            FROM TbRiesgos 
            INNER JOIN TbUsuariosAplicaciones ON TbRiesgos.UsuarioRed = TbUsuariosAplicaciones.UsuarioRed
            WHERE TbRiesgos.FechaJustificacionRetiroRiesgo IS NOT NULL 
              AND TbRiesgos.ParaInformeAvisos <> 'No' 
              AND TbRiesgos.FechaJustificacionRetiroRiesgoRechazada IS NULL 
              AND TbRiesgos.JustificacionRetiroRiesgo IS NULL
        """,
        
        "6. Riesgos retirados rechazados": """
            SELECT DISTINCT TbRiesgos.UsuarioRed, TbUsuariosAplicaciones.Nombre, TbUsuariosAplicaciones.CorreoUsuario
            FROM TbRiesgos 
            INNER JOIN TbUsuariosAplicaciones ON TbRiesgos.UsuarioRed = TbUsuariosAplicaciones.UsuarioRed
            WHERE TbRiesgos.FechaJustificacionRetiroRiesgoRechazada IS NOT NULL 
              AND TbRiesgos.ParaInformeAvisos <> 'No'
        """,
        
        "7. Riesgos con acciones de mitigación para replanificar": """
            SELECT DISTINCT TbRiesgos.UsuarioRed, TbUsuariosAplicaciones.Nombre, TbUsuariosAplicaciones.CorreoUsuario
            FROM TbRiesgos 
            INNER JOIN TbUsuariosAplicaciones ON TbRiesgos.UsuarioRed = TbUsuariosAplicaciones.UsuarioRed
            WHERE TbRiesgos.AccionMitigacion IS NOT NULL 
              AND TbRiesgos.ParaInformeAvisos <> 'No' 
              AND TbRiesgos.FechaFinAccionMitigacion IS NOT NULL 
              AND TbRiesgos.FechaFinAccionMitigacion < Date() 
              AND TbRiesgos.FechaFinRealAccionMitigacion IS NULL
        """,
        
        "8. Riesgos con acciones de contingencia para replanificar": """
            SELECT DISTINCT TbRiesgos.UsuarioRed, TbUsuariosAplicaciones.Nombre, TbUsuariosAplicaciones.CorreoUsuario
            FROM TbRiesgos 
            INNER JOIN TbUsuariosAplicaciones ON TbRiesgos.UsuarioRed = TbUsuariosAplicaciones.UsuarioRed
            WHERE TbRiesgos.AccionContingencia IS NOT NULL 
              AND TbRiesgos.ParaInformeAvisos <> 'No' 
              AND TbRiesgos.FechaFinAccionContingencia IS NOT NULL 
              AND TbRiesgos.FechaFinAccionContingencia < Date() 
              AND TbRiesgos.FechaFinRealAccionContingencia IS NULL
        """
    }
    
    try:
        # Obtener configuración
        config = Config()
        
        # Conectar a la base de datos de riesgos
        print("Conectando a la base de datos de riesgos...")
        db = AccessDatabase(config.get_db_riesgos_connection_string())
        db.connect()
        cursor = db.get_cursor()
        
        print(f"Conexión exitosa a: {config.riesgos_db_path}")
        print("=" * 80)
        
        total_users = set()
        
        # Ejecutar cada consulta
        for query_name, query_sql in queries.items():
            print(f"\n{query_name}")
            print("-" * len(query_name))
            
            try:
                cursor.execute(query_sql)
                results = cursor.fetchall()
                
                if results:
                    print(f"Encontrados {len(results)} usuarios:")
                    for row in results:
                        usuario_red, nombre, correo = row
                        print(f"  - {usuario_red} ({nombre}) - {correo}")
                        total_users.add(usuario_red)
                else:
                    print("  No se encontraron usuarios.")
                    
            except Exception as e:
                print(f"  ERROR al ejecutar consulta: {e}")
        
        print("\n" + "=" * 80)
        print(f"RESUMEN TOTAL:")
        print(f"Usuarios únicos encontrados: {len(total_users)}")
        if total_users:
            print("Lista de usuarios únicos:")
            for user in sorted(total_users):
                print(f"  - {user}")
        else:
            print("No se encontraron usuarios técnicos con tareas pendientes.")
            print("\nPosibles causas:")
            print("1. No hay datos en las tablas TbRiesgos o TbProyectosEdiciones")
            print("2. No hay usuarios técnicos registrados en TbUsuariosAplicaciones")
            print("3. Todos los riesgos/ediciones están completados")
            print("4. Los campos de fecha o estado no tienen los valores esperados")
        
    except Exception as e:
        print(f"Error al conectar o ejecutar consultas: {e}")
        return False
    
    finally:
        if 'db' in locals():
            db.disconnect()
            print(f"\nConexión cerrada.")
    
    return True

def check_basic_tables():
    """
    Verifica que las tablas principales tengan datos básicos.
    """
    print("\n" + "=" * 80)
    print("VERIFICACIÓN DE TABLAS BÁSICAS")
    print("=" * 80)
    
    basic_queries = {
        "Total usuarios en TbUsuariosAplicaciones": "SELECT COUNT(*) FROM TbUsuariosAplicaciones",
        "Total riesgos en TbRiesgos": "SELECT COUNT(*) FROM TbRiesgos",
        "Total ediciones en TbProyectosEdiciones": "SELECT COUNT(*) FROM TbProyectosEdiciones",
        "Usuarios técnicos en aplicación Riesgos": """
            SELECT COUNT(*) FROM TbUsuariosAplicaciones 
            WHERE Aplicacion = 'Riesgos' AND TipoUsuario = 'Técnico'
        """
    }
    
    try:
        config = get_config()
        conn = get_database_connection(config.riesgos_db_path, config.db_password)
        cursor = conn.cursor()
        
        for description, query in basic_queries.items():
            try:
                cursor.execute(query)
                result = cursor.fetchone()
                count = result[0] if result else 0
                print(f"{description}: {count}")
            except Exception as e:
                print(f"{description}: ERROR - {e}")
        
    except Exception as e:
        print(f"Error en verificación básica: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("HERRAMIENTA DE DIAGNÓSTICO - CONSULTAS DE RIESGOS")
    print("=" * 80)
    print("Esta herramienta ejecuta las 8 consultas SQL de get_distinct_technical_users")
    print("para diagnosticar por qué no se obtienen usuarios técnicos con tareas pendientes.")
    print()
    
    # Verificar tablas básicas primero
    check_basic_tables()
    
    # Ejecutar las consultas principales
    test_riesgos_queries()