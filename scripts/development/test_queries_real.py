#!/usr/bin/env python3
"""
Script para probar las consultas reales con criterios más amplios
"""

import sys
import os
from datetime import datetime, timedelta

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from common.config import Config
from common.database import get_database_instance

def probar_consultas_reales():
    """Prueba las consultas reales con diferentes criterios"""
    print("=== Probando consultas reales con criterios amplios ===")
    
    config = Config()
    nc_connection_string = config.get_db_no_conformidades_connection_string()
    db = get_database_instance(nc_connection_string)
    
    try:
        # 1. Contar registros básicos en cada tabla
        print("\n1. Conteos básicos:")
        
        count_nc = db.execute_query("SELECT COUNT(*) as total FROM TbNoConformidades")[0]['total']
        count_ac = db.execute_query("SELECT COUNT(*) as total FROM TbNCAccionCorrectivas")[0]['total']
        count_ar = db.execute_query("SELECT COUNT(*) as total FROM TbNCAccionesRealizadas")[0]['total']
        
        print(f"  TbNoConformidades: {count_nc}")
        print(f"  TbNCAccionCorrectivas: {count_ac}")
        print(f"  TbNCAccionesRealizadas: {count_ar}")
        
        # 2. Probar consulta ARAPC simplificada (sin filtros de fecha)
        print("\n2. Consulta ARAPC simplificada:")
        try:
            arapc_simple_query = """
            SELECT COUNT(*) as total
            FROM TbNCAccionCorrectivas ac
            INNER JOIN TbNoConformidades nc ON ac.IDNoConformidad = nc.IDNoConformidad
            WHERE ac.ESTADO <> 'FINALIZADA'
            AND NOT EXISTS (
                SELECT 1 FROM TbNCAccionesRealizadas ar 
                WHERE ar.IDAccionCorrectiva = ac.IDAccionCorrectiva
            )
            """
            arapc_simple = db.execute_query(arapc_simple_query)[0]['total']
            print(f"  Acciones correctivas no finalizadas sin acciones realizadas: {arapc_simple}")
            
        except Exception as e:
            print(f"  Error en ARAPC simplificada: {e}")
        
        # 3. Probar con fechas más amplias
        print("\n3. Consulta ARAPC con fechas amplias:")
        try:
            # Usar una fecha muy futura para capturar más registros
            fecha_futura = datetime.now() + timedelta(days=365)  # 1 año en el futuro
            fecha_access = fecha_futura.strftime('%m/%d/%Y')
            
            arapc_amplia_query = f"""
            SELECT COUNT(*) as total
            FROM TbNCAccionCorrectivas ac
            INNER JOIN TbNoConformidades nc ON ac.IDNoConformidad = nc.IDNoConformidad
            WHERE ac.ESTADO <> 'FINALIZADA'
            AND ac.FechaFinalUltima IS NOT NULL
            AND ac.FechaFinalUltima <= #{fecha_access}#
            AND NOT EXISTS (
                SELECT 1 FROM TbNCAccionesRealizadas ar 
                WHERE ar.IDAccionCorrectiva = ac.IDAccionCorrectiva
            )
            """
            arapc_amplia = db.execute_query(arapc_amplia_query)[0]['total']
            print(f"  Con fecha hasta {fecha_access}: {arapc_amplia}")
            
        except Exception as e:
            print(f"  Error en ARAPC amplia: {e}")
        
        # 4. Verificar estados específicos
        print("\n4. Estados en TbNCAccionCorrectivas:")
        try:
            estados_query = """
            SELECT ac.ESTADO, COUNT(*) as cantidad
            FROM TbNCAccionCorrectivas ac
            GROUP BY ac.ESTADO
            """
            estados = db.execute_query(estados_query)
            for estado in estados:
                print(f"  {estado['ESTADO']}: {estado['cantidad']}")
                
        except Exception as e:
            print(f"  Error verificando estados: {e}")
        
        # 5. Verificar fechas en TbNCAccionCorrectivas
        print("\n5. Análisis de fechas:")
        try:
            fechas_query = """
            SELECT 
                COUNT(*) as total,
                COUNT(FechaFinalUltima) as con_fecha
            FROM TbNCAccionCorrectivas
            """
            fechas = db.execute_query(fechas_query)[0]
            print(f"  Total: {fechas['total']}, Con FechaFinalUltima: {fechas['con_fecha']}")
            
            if fechas['con_fecha'] > 0:
                min_max_query = """
                SELECT 
                    MIN(FechaFinalUltima) as fecha_min,
                    MAX(FechaFinalUltima) as fecha_max
                FROM TbNCAccionCorrectivas
                WHERE FechaFinalUltima IS NOT NULL
                """
                min_max = db.execute_query(min_max_query)[0]
                print(f"  Rango de fechas: {min_max['fecha_min']} a {min_max['fecha_max']}")
                
        except Exception as e:
            print(f"  Error verificando fechas: {e}")
        
        # 6. Consulta de NCs con control de eficacia simplificada
        print("\n6. NCs con control de eficacia:")
        try:
            eficacia_query = """
            SELECT COUNT(*) as total
            FROM TbNoConformidades
            WHERE RequiereControlEficacia = 'Si'
            AND Borrado = False
            """
            eficacia_total = db.execute_query(eficacia_query)[0]['total']
            print(f"  NCs que requieren control de eficacia: {eficacia_total}")
            
            if eficacia_total > 0:
                # Verificar cuántas tienen fecha de control
                con_fecha_query = """
                SELECT COUNT(*) as total
                FROM TbNoConformidades
                WHERE RequiereControlEficacia = 'Si'
                AND FechaControlEficacia IS NOT NULL
                AND Borrado = False
                """
                con_fecha = db.execute_query(con_fecha_query)[0]['total']
                print(f"  Con fecha de control: {con_fecha}")
                
        except Exception as e:
            print(f"  Error verificando eficacia: {e}")
        
        # 7. Muestra de datos reales
        print("\n7. Muestra de datos:")
        try:
            muestra_query = """
            SELECT TOP 3
                ac.IDAccionCorrectiva,
                ac.ESTADO,
                ac.FechaFinalUltima,
                nc.CodigoNoConformidad
            FROM TbNCAccionCorrectivas ac
            INNER JOIN TbNoConformidades nc ON ac.IDNoConformidad = nc.IDNoConformidad
            ORDER BY ac.IDAccionCorrectiva
            """
            muestra = db.execute_query(muestra_query)
            print("  Muestra de acciones correctivas:")
            for row in muestra:
                print(f"    ID: {row['IDAccionCorrectiva']}, Estado: {row['ESTADO']}, Fecha: {row['FechaFinalUltima']}, NC: {row['CodigoNoConformidad']}")
                
        except Exception as e:
            print(f"  Error obteniendo muestra: {e}")
            
    except Exception as e:
        print(f"✗ Error general: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        try:
            db.disconnect()
        except:
            pass

if __name__ == "__main__":
    probar_consultas_reales()