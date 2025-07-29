#!/usr/bin/env python3
"""
Script simplificado para verificar datos usando sintaxis compatible con Access
"""

import sys
import os
from datetime import datetime, timedelta

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from common.config import Config
from common.database import get_database_instance

def verificar_datos_simple():
    """Verifica los datos usando consultas simples compatibles con Access"""
    print("=== Verificando datos con sintaxis Access ===")
    
    config = Config()
    nc_connection_string = config.get_db_no_conformidades_connection_string()
    db = get_database_instance(nc_connection_string)
    
    try:
        # 1. Contar registros básico
        print("\n1. Conteo básico de registros:")
        
        tables = ['TbNoConformidades', 'TbNCAccionCorrectivas', 'TbNCAccionesRealizadas']
        for table in tables:
            try:
                count_query = f"SELECT COUNT(*) FROM {table}"
                result = db.execute_query(count_query)
                count = result[0][0] if result else 0
                print(f"  {table}: {count} registros")
            except Exception as e:
                print(f"  Error contando {table}: {e}")
        
        # 2. Estados únicos en TbNCAccionCorrectivas
        print("\n2. Estados en TbNCAccionCorrectivas:")
        try:
            estados_query = "SELECT DISTINCT ESTADO FROM TbNCAccionCorrectivas"
            estados = db.execute_query(estados_query)
            for estado in estados:
                print(f"  Estado encontrado: {estado[0]}")
                
            # Contar por cada estado
            for estado in estados:
                count_query = f"SELECT COUNT(*) FROM TbNCAccionCorrectivas WHERE ESTADO = '{estado[0]}'"
                count_result = db.execute_query(count_query)
                count = count_result[0][0] if count_result else 0
                print(f"    {estado[0]}: {count} registros")
                
        except Exception as e:
            print(f"  Error verificando estados: {e}")
        
        # 3. Verificar fechas no nulas
        print("\n3. Fechas en TbNCAccionCorrectivas:")
        try:
            total_query = "SELECT COUNT(*) FROM TbNCAccionCorrectivas"
            total_result = db.execute_query(total_query)
            total = total_result[0][0] if total_result else 0
            
            con_fecha_query = "SELECT COUNT(*) FROM TbNCAccionCorrectivas WHERE FechaFinalUltima IS NOT NULL"
            con_fecha_result = db.execute_query(con_fecha_query)
            con_fecha = con_fecha_result[0][0] if con_fecha_result else 0
            
            print(f"  Total registros: {total}")
            print(f"  Con FechaFinalUltima: {con_fecha}")
            
            if con_fecha > 0:
                min_fecha_query = "SELECT MIN(FechaFinalUltima) FROM TbNCAccionCorrectivas WHERE FechaFinalUltima IS NOT NULL"
                max_fecha_query = "SELECT MAX(FechaFinalUltima) FROM TbNCAccionCorrectivas WHERE FechaFinalUltima IS NOT NULL"
                
                min_result = db.execute_query(min_fecha_query)
                max_result = db.execute_query(max_fecha_query)
                
                print(f"  Fecha mínima: {min_result[0][0] if min_result else 'N/A'}")
                print(f"  Fecha máxima: {max_result[0][0] if max_result else 'N/A'}")
                
        except Exception as e:
            print(f"  Error verificando fechas: {e}")
        
        # 4. Verificar acciones sin realizar
        print("\n4. Acciones correctivas sin acciones realizadas:")
        try:
            # Contar total de acciones correctivas
            total_ac_query = "SELECT COUNT(*) FROM TbNCAccionCorrectivas"
            total_ac = db.execute_query(total_ac_query)[0][0]
            
            # Contar acciones correctivas que tienen acciones realizadas
            con_ar_query = """
            SELECT COUNT(DISTINCT ac.IDAccionCorrectiva) 
            FROM TbNCAccionCorrectivas ac 
            INNER JOIN TbNCAccionesRealizadas ar ON ac.IDAccionCorrectiva = ar.IDAccionCorrectiva
            """
            con_ar = db.execute_query(con_ar_query)[0][0]
            
            sin_ar = total_ac - con_ar
            print(f"  Total acciones correctivas: {total_ac}")
            print(f"  Con acciones realizadas: {con_ar}")
            print(f"  Sin acciones realizadas: {sin_ar}")
            
        except Exception as e:
            print(f"  Error verificando acciones sin realizar: {e}")
        
        # 5. Estados en TbNCAccionesRealizadas
        print("\n5. Estados en TbNCAccionesRealizadas:")
        try:
            estados_ar_query = "SELECT DISTINCT ESTADO FROM TbNCAccionesRealizadas"
            estados_ar = db.execute_query(estados_ar_query)
            for estado in estados_ar:
                count_query = f"SELECT COUNT(*) FROM TbNCAccionesRealizadas WHERE ESTADO = '{estado[0]}'"
                count_result = db.execute_query(count_query)
                count = count_result[0][0] if count_result else 0
                print(f"  {estado[0]}: {count} registros")
                
        except Exception as e:
            print(f"  Error verificando estados AR: {e}")
        
        # 6. Muestra de datos
        print("\n6. Muestra de datos:")
        try:
            muestra_query = """
            SELECT TOP 5 ac.IDAccionCorrectiva, ac.ESTADO, ac.FechaFinalUltima
            FROM TbNCAccionCorrectivas ac
            ORDER BY ac.IDAccionCorrectiva
            """
            muestra = db.execute_query(muestra_query)
            print("  Primeras 5 acciones correctivas:")
            for row in muestra:
                print(f"    ID: {row[0]}, Estado: {row[1]}, Fecha: {row[2]}")
                
        except Exception as e:
            print(f"  Error obteniendo muestra: {e}")
        
        # 7. Verificar fechas actuales vs futuras
        print("\n7. Análisis de fechas futuras:")
        try:
            hoy = datetime.now()
            fecha_limite = hoy + timedelta(days=15)
            
            print(f"  Fecha actual: {hoy.strftime('%Y-%m-%d')}")
            print(f"  Buscando fechas hasta: {fecha_limite.strftime('%Y-%m-%d')}")
            
            # Usar formato de fecha compatible con Access
            fecha_access = fecha_limite.strftime('%m/%d/%Y')
            
            futuras_query = f"""
            SELECT COUNT(*) 
            FROM TbNCAccionCorrectivas 
            WHERE FechaFinalUltima IS NOT NULL 
            AND FechaFinalUltima <= #{fecha_access}#
            """
            futuras = db.execute_query(futuras_query)
            print(f"  Acciones con fecha <= {fecha_access}: {futuras[0][0] if futuras else 0}")
            
            # Verificar acciones no finalizadas
            no_finalizadas_query = """
            SELECT COUNT(*) 
            FROM TbNCAccionCorrectivas 
            WHERE ESTADO <> 'FINALIZADA'
            """
            no_finalizadas = db.execute_query(no_finalizadas_query)
            print(f"  Acciones no finalizadas: {no_finalizadas[0][0] if no_finalizadas else 0}")
            
        except Exception as e:
            print(f"  Error verificando fechas futuras: {e}")
            
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
    verificar_datos_simple()