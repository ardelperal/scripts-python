#!/usr/bin/env python3
"""
Script para verificar los datos en las tablas y entender por qué las consultas devuelven 0
"""

import sys
import os
from datetime import datetime, timedelta

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from common.config import Config
from common.database import get_database_instance

def verificar_datos():
    """Verifica los datos en las tablas principales"""
    print("=== Verificando datos en las tablas ===")
    
    config = Config()
    nc_connection_string = config.get_db_no_conformidades_connection_string()
    db = get_database_instance(nc_connection_string)
    
    try:
        # 1. Contar registros en cada tabla
        print("\n1. Conteo de registros por tabla:")
        
        tables = ['TbNoConformidades', 'TbNCAccionCorrectivas', 'TbNCAccionesRealizadas']
        for table in tables:
            try:
                count_query = f"SELECT COUNT(*) as total FROM {table}"
                result = db.execute_query(count_query)
                count = result[0][0] if result else 0
                print(f"  {table}: {count} registros")
            except Exception as e:
                print(f"  Error contando {table}: {e}")
        
        # 2. Verificar estados en TbNCAccionCorrectivas
        print("\n2. Estados en TbNCAccionCorrectivas:")
        try:
            estados_query = """
            SELECT ESTADO, COUNT(*) as cantidad 
            FROM TbNCAccionCorrectivas 
            GROUP BY ESTADO
            """
            estados = db.execute_query(estados_query)
            for estado in estados:
                print(f"  {estado[0]}: {estado[1]} registros")
        except Exception as e:
            print(f"  Error verificando estados: {e}")
        
        # 3. Verificar fechas en TbNCAccionCorrectivas
        print("\n3. Análisis de fechas en TbNCAccionCorrectivas:")
        try:
            fechas_query = """
            SELECT 
                COUNT(*) as total,
                COUNT(FechaFinalUltima) as con_fecha_final,
                MIN(FechaFinalUltima) as fecha_min,
                MAX(FechaFinalUltima) as fecha_max
            FROM TbNCAccionCorrectivas
            """
            fechas = db.execute_query(fechas_query)
            if fechas:
                row = fechas[0]
                print(f"  Total registros: {row[0]}")
                print(f"  Con FechaFinalUltima: {row[1]}")
                print(f"  Fecha mínima: {row[2]}")
                print(f"  Fecha máxima: {row[3]}")
        except Exception as e:
            print(f"  Error verificando fechas: {e}")
        
        # 4. Verificar acciones realizadas pendientes
        print("\n4. Análisis de acciones realizadas:")
        try:
            # Verificar si hay acciones correctivas sin acciones realizadas
            sin_acciones_query = """
            SELECT COUNT(*) as cantidad
            FROM TbNCAccionCorrectivas ac
            WHERE NOT EXISTS (
                SELECT 1 FROM TbNCAccionesRealizadas ar 
                WHERE ar.IDAccionCorrectiva = ac.IDAccionCorrectiva
            )
            """
            sin_acciones = db.execute_query(sin_acciones_query)
            print(f"  Acciones correctivas sin acciones realizadas: {sin_acciones[0][0] if sin_acciones else 0}")
            
            # Verificar estados de acciones realizadas
            estados_ar_query = """
            SELECT ESTADO, COUNT(*) as cantidad 
            FROM TbNCAccionesRealizadas 
            GROUP BY ESTADO
            """
            estados_ar = db.execute_query(estados_ar_query)
            print("  Estados en TbNCAccionesRealizadas:")
            for estado in estados_ar:
                print(f"    {estado[0]}: {estado[1]} registros")
                
        except Exception as e:
            print(f"  Error verificando acciones realizadas: {e}")
        
        # 5. Verificar fechas próximas a vencer
        print("\n5. Verificando fechas próximas a vencer:")
        try:
            hoy = datetime.now()
            fecha_limite_15 = hoy + timedelta(days=15)
            fecha_limite_7 = hoy + timedelta(days=7)
            
            print(f"  Fecha actual: {hoy.strftime('%Y-%m-%d')}")
            print(f"  Límite 15 días: {fecha_limite_15.strftime('%Y-%m-%d')}")
            print(f"  Límite 7 días: {fecha_limite_7.strftime('%Y-%m-%d')}")
            
            # Contar acciones que vencen en 15 días - usando formato Access
            fecha_limite_access = fecha_limite_15.strftime('%m/%d/%Y')
            vencen_15_query = f"""
            SELECT COUNT(*) as cantidad
            FROM TbNCAccionCorrectivas ac
            WHERE ac.ESTADO <> 'FINALIZADA' 
            AND ac.FechaFinalUltima IS NOT NULL
            AND ac.FechaFinalUltima <= #{fecha_limite_access}#
            AND NOT EXISTS (
                SELECT 1 FROM TbNCAccionesRealizadas ar 
                WHERE ar.IDAccionCorrectiva = ac.IDAccionCorrectiva
            )
            """
            vencen_15 = db.execute_query(vencen_15_query)
            print(f"  Acciones que vencen en 15 días: {vencen_15[0][0] if vencen_15 else 0}")
            
        except Exception as e:
            print(f"  Error verificando fechas próximas: {e}")
        
        # 6. Verificar NCs con control de eficacia
        print("\n6. Verificando NCs con control de eficacia:")
        try:
            eficacia_query = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN RequiereControlEficacia = 'Si' THEN 1 ELSE 0 END) as requiere_eficacia,
                SUM(CASE WHEN FechaControlEficacia IS NOT NULL THEN 1 ELSE 0 END) as con_fecha_control
            FROM TbNoConformidades
            WHERE Borrado = False
            """
            eficacia = db.execute_query(eficacia_query)
            if eficacia:
                row = eficacia[0]
                print(f"  Total NCs activas: {row[0]}")
                print(f"  Requieren control eficacia: {row[1]}")
                print(f"  Con fecha de control: {row[2]}")
        except Exception as e:
            print(f"  Error verificando control de eficacia: {e}")
        
        # 7. Muestra de datos reales
        print("\n7. Muestra de datos reales:")
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
                print(f"    ID: {row[0]}, Estado: {row[1]}, Fecha: {row[2]}, NC: {row[3]}")
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
    verificar_datos()