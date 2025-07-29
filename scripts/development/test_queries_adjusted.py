#!/usr/bin/env python3
"""
Script para probar las consultas originales con fechas ajustadas
"""

import sys
import os
from datetime import datetime, timedelta

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from common.config import Config
from common.database import get_database_instance

def probar_consultas_originales_ajustadas():
    """Prueba las consultas originales con fechas ajustadas al pasado"""
    print("=== Probando consultas originales con fechas ajustadas ===")
    
    config = Config()
    nc_connection_string = config.get_db_no_conformidades_connection_string()
    db = get_database_instance(nc_connection_string)
    
    try:
        # Usar una fecha base en el pasado cuando había fechas activas
        fecha_base = datetime(2025, 7, 20)  # Unos días antes de la fecha máxima
        
        print(f"Fecha base para pruebas: {fecha_base.strftime('%Y-%m-%d')}")
        print("Fecha máxima en BD: 2025-07-24")
        
        # 1. Consulta ARAPC con fecha ajustada (15 días)
        print("\n1. Consulta ARAPC (15 días desde fecha base):")
        try:
            fecha_limite_15 = fecha_base + timedelta(days=15)
            fecha_access_15 = fecha_limite_15.strftime('%m/%d/%Y')
            
            arapc_15_query = f"""
            SELECT COUNT(*) as total
            FROM TbNCAccionCorrectivas ac
            INNER JOIN TbNoConformidades nc ON ac.IDNoConformidad = nc.IDNoConformidad
            WHERE ac.ESTADO <> 'FINALIZADA'
            AND ac.FechaFinalUltima IS NOT NULL
            AND ac.FechaFinalUltima <= #{fecha_access_15}#
            AND NOT EXISTS (
                SELECT 1 FROM TbNCAccionesRealizadas ar 
                WHERE ar.IDAccionCorrectiva = ac.IDAccionCorrectiva
            )
            """
            arapc_15 = db.execute_query(arapc_15_query)[0]['total']
            print(f"  Resultados con fecha <= {fecha_access_15}: {arapc_15}")
            
        except Exception as e:
            print(f"  Error en ARAPC 15 días: {e}")
        
        # 2. Consulta ARAPC con fecha ajustada (7 días)
        print("\n2. Consulta ARAPC (7 días desde fecha base):")
        try:
            fecha_limite_7 = fecha_base + timedelta(days=7)
            fecha_access_7 = fecha_limite_7.strftime('%m/%d/%Y')
            
            arapc_7_query = f"""
            SELECT COUNT(*) as total
            FROM TbNCAccionCorrectivas ac
            INNER JOIN TbNoConformidades nc ON ac.IDNoConformidad = nc.IDNoConformidad
            WHERE ac.ESTADO <> 'FINALIZADA'
            AND ac.FechaFinalUltima IS NOT NULL
            AND ac.FechaFinalUltima <= #{fecha_access_7}#
            AND NOT EXISTS (
                SELECT 1 FROM TbNCAccionesRealizadas ar 
                WHERE ar.IDAccionCorrectiva = ac.IDAccionCorrectiva
            )
            """
            arapc_7 = db.execute_query(arapc_7_query)[0]['total']
            print(f"  Resultados con fecha <= {fecha_access_7}: {arapc_7}")
            
        except Exception as e:
            print(f"  Error en ARAPC 7 días: {e}")
        
        # 3. Consulta ARAPC con fecha exacta
        print("\n3. Consulta ARAPC (fecha exacta):")
        try:
            fecha_access_exacta = fecha_base.strftime('%m/%d/%Y')
            
            arapc_exacta_query = f"""
            SELECT COUNT(*) as total
            FROM TbNCAccionCorrectivas ac
            INNER JOIN TbNoConformidades nc ON ac.IDNoConformidad = nc.IDNoConformidad
            WHERE ac.ESTADO <> 'FINALIZADA'
            AND ac.FechaFinalUltima IS NOT NULL
            AND ac.FechaFinalUltima <= #{fecha_access_exacta}#
            AND NOT EXISTS (
                SELECT 1 FROM TbNCAccionesRealizadas ar 
                WHERE ar.IDAccionCorrectiva = ac.IDAccionCorrectiva
            )
            """
            arapc_exacta = db.execute_query(arapc_exacta_query)[0]['total']
            print(f"  Resultados con fecha <= {fecha_access_exacta}: {arapc_exacta}")
            
        except Exception as e:
            print(f"  Error en ARAPC fecha exacta: {e}")
        
        # 4. Verificar qué acciones están cerca de la fecha máxima
        print("\n4. Acciones cerca de la fecha máxima:")
        try:
            cerca_max_query = """
            SELECT 
                ac.IDAccionCorrectiva,
                ac.ESTADO,
                ac.FechaFinalUltima,
                nc.CodigoNoConformidad
            FROM TbNCAccionCorrectivas ac
            INNER JOIN TbNoConformidades nc ON ac.IDNoConformidad = nc.IDNoConformidad
            WHERE ac.FechaFinalUltima >= #07/20/2025#
            AND ac.ESTADO <> 'FINALIZADA'
            ORDER BY ac.FechaFinalUltima DESC
            """
            cerca_max = db.execute_query(cerca_max_query)
            print(f"  Acciones con fecha >= 2025-07-20 y no finalizadas:")
            for row in cerca_max:
                print(f"    ID: {row['IDAccionCorrectiva']}, Estado: {row['ESTADO']}, Fecha: {row['FechaFinalUltima']}, NC: {row['CodigoNoConformidad']}")
                
        except Exception as e:
            print(f"  Error verificando fechas cercanas: {e}")
        
        # 5. Verificar si hay acciones sin acciones realizadas en esas fechas
        print("\n5. Verificar acciones sin realizar en fechas recientes:")
        try:
            sin_realizar_query = """
            SELECT 
                ac.IDAccionCorrectiva,
                ac.ESTADO,
                ac.FechaFinalUltima,
                nc.CodigoNoConformidad
            FROM TbNCAccionCorrectivas ac
            INNER JOIN TbNoConformidades nc ON ac.IDNoConformidad = nc.IDNoConformidad
            WHERE ac.FechaFinalUltima >= #07/20/2025#
            AND ac.ESTADO <> 'FINALIZADA'
            AND NOT EXISTS (
                SELECT 1 FROM TbNCAccionesRealizadas ar 
                WHERE ar.IDAccionCorrectiva = ac.IDAccionCorrectiva
            )
            ORDER BY ac.FechaFinalUltima DESC
            """
            sin_realizar = db.execute_query(sin_realizar_query)
            print(f"  Acciones sin realizar con fecha >= 2025-07-20:")
            for row in sin_realizar:
                print(f"    ID: {row['IDAccionCorrectiva']}, Estado: {row['ESTADO']}, Fecha: {row['FechaFinalUltima']}, NC: {row['CodigoNoConformidad']}")
                
        except Exception as e:
            print(f"  Error verificando sin realizar: {e}")
            
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
    probar_consultas_originales_ajustadas()