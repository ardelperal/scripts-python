#!/usr/bin/env python3
"""
Script de prueba para verificar las consultas SQL corregidas
"""

import os
import sys
sys.path.append('src')

from common.database import get_database_instance
from common.config import Config

def test_arapc_query():
    """Prueba la consulta de ARAPs próximas a vencer"""
    print("=== Probando consulta de ARAPs próximas a vencer ===")
    
    config = Config()
    nc_connection_string = config.get_db_no_conformidades_connection_string()
    db = get_database_instance(nc_connection_string)
    
    try:
        from datetime import datetime, timedelta
        
        # Calcular fechas en Python
        fecha_hoy = datetime.now().date()
        dias_alerta = 7
        fecha_limite_superior = fecha_hoy + timedelta(days=dias_alerta)
        
        # Query SQL sin DATEDIFF
        sql_query = """SELECT nc.IDNoConformidad, nc.CodigoNoConformidad, nc.DESCRIPCION, nc.FECHAAPERTURA, ac.IDAccionCorrectiva, ac.AccionCorrectiva, ac.FechaFinalUltima, ac.Responsable FROM TbNoConformidades nc INNER JOIN TbNCAccionCorrectivas ac ON nc.IDNoConformidad = ac.IDNoConformidad WHERE ac.FechaFinalUltima IS NOT NULL AND ac.FechaFinalUltima >= ? AND ac.FechaFinalUltima <= ? AND NOT EXISTS (SELECT 1 FROM TbNCAccionesRealizadas ar WHERE ar.IDAccionCorrectiva = ac.IDAccionCorrectiva) ORDER BY ac.FechaFinalUltima ASC"""
        
        resultados = db.execute_query(sql_query, [fecha_hoy, fecha_limite_superior])
        print(f"✓ Consulta ARAPs ejecutada exitosamente. Resultados: {len(resultados)}")
        
        if resultados:
            print("Primeros 3 resultados:")
            for i, row in enumerate(resultados[:3]):
                fecha_limite = row[6]
                if fecha_limite:
                    dias_para_vencer = (fecha_limite - fecha_hoy).days
                    print(f"  {i+1}. NC: {row[1]}, Acción: {row[5]}, Responsable: {row[7]}, Días: {dias_para_vencer}")
        
    except Exception as e:
        print(f"✗ Error en consulta ARAPs: {e}")
    
    finally:
        db.disconnect()

def test_nc_eficacia_query():
    """Prueba la consulta de NCs próximas a caducar por eficacia"""
    print("\n=== Probando consulta de NCs próximas a caducar por eficacia ===")
    
    config = Config()
    nc_connection_string = config.get_db_no_conformidades_connection_string()
    db = get_database_instance(nc_connection_string)
    
    try:
        from datetime import datetime, timedelta
        
        # Calcular fechas en Python
        fecha_hoy = datetime.now().date()
        fecha_limite_inferior = fecha_hoy - timedelta(days=365)  # Hace 365 días
        fecha_limite_superior = fecha_hoy - timedelta(days=30)   # Hace 30 días
        
        # Query SQL sin DATEDIFF
        sql_query = ("SELECT nc.IDNoConformidad, nc.CodigoNoConformidad, nc.DESCRIPCION, nc.FECHAAPERTURA, "
                    "ac.IDAccionCorrectiva, ac.AccionCorrectiva, ac.FechaFinalUltima, ac.Responsable "
                    "FROM TbNoConformidades nc "
                    "INNER JOIN TbNCAccionCorrectivas ac ON nc.IDNoConformidad = ac.IDNoConformidad "
                    "WHERE ac.FechaFinalUltima IS NOT NULL "
                    "AND ac.FechaFinalUltima >= ? "
                    "AND ac.FechaFinalUltima <= ? "
                    "AND NOT EXISTS (SELECT 1 FROM TbNCAccionesRealizadas ar "
                    "WHERE ar.IDAccionCorrectiva = ac.IDAccionCorrectiva) "
                    "ORDER BY ac.FechaFinalUltima ASC")
        
        resultados = db.execute_query(sql_query, [fecha_limite_inferior, fecha_limite_superior])
        print(f"✓ Consulta NCs eficacia ejecutada exitosamente. Resultados: {len(resultados)}")
        
        if resultados:
            print("Primeros 3 resultados:")
            for i, row in enumerate(resultados[:3]):
                fecha_fin = row[6]
                if fecha_fin:
                    dias_transcurridos = (fecha_hoy - fecha_fin).days
                    dias_restantes_eficacia = 365 - dias_transcurridos
                    print(f"  {i+1}. NC: {row[1]}, Acción: {row[5]}, Responsable: {row[7]}, Días restantes para eficacia: {dias_restantes_eficacia}")
        
    except Exception as e:
        print(f"✗ Error en consulta NCs eficacia: {e}")
    
    finally:
        db.disconnect()

def test_nc_sin_acciones_query():
    """Prueba la consulta de NCs sin acciones"""
    print("\n=== Probando consulta de NCs sin acciones ===")
    
    config = Config()
    nc_connection_string = config.get_db_no_conformidades_connection_string()
    db = get_database_instance(nc_connection_string)
    
    try:
        from datetime import datetime, timedelta
        
        # Calcular fechas en Python
        fecha_hoy = datetime.now().date()
        dias_alerta = 16
        fecha_limite = fecha_hoy + timedelta(days=dias_alerta)
        
        # Query SQL sin DATEDIFF
        sql_query = """SELECT nc.IDNoConformidad, nc.CodigoNoConformidad, nc.Nemotecnico, nc.DESCRIPCION, nc.RESPONSABLECALIDAD, nc.FECHAAPERTURA, nc.FPREVCIERRE FROM TbNoConformidades nc LEFT JOIN TbNCAccionCorrectivas ac ON nc.IDNoConformidad = ac.IDNoConformidad WHERE ac.IDAccionCorrectiva IS NULL AND nc.FPREVCIERRE IS NOT NULL AND nc.FPREVCIERRE <= ? ORDER BY nc.FECHAAPERTURA ASC"""
        
        resultados = db.execute_query(sql_query, [fecha_limite])
        print(f"✓ Consulta NCs sin acciones ejecutada exitosamente. Resultados: {len(resultados)}")
        
        if resultados:
            print("Primeros 3 resultados:")
            for i, row in enumerate(resultados[:3]):
                fecha_cierre = row[6]
                if fecha_cierre:
                    dias_para_cierre = (fecha_cierre - fecha_hoy).days
                    print(f"  {i+1}. NC: {row[1]}, Descripción: {row[3][:50]}..., Días: {dias_para_cierre}")
        
    except Exception as e:
        print(f"✗ Error en consulta NCs sin acciones: {e}")
    
    finally:
        db.disconnect()

if __name__ == "__main__":
    print("Iniciando pruebas de consultas SQL corregidas...")
    
    test_arapc_query()
    test_nc_eficacia_query()
    test_nc_sin_acciones_query()
    
    print("\n=== Pruebas completadas ===")