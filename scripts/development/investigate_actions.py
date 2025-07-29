#!/usr/bin/env python3
"""
Script para investigar en detalle las 5 acciones sin acciones realizadas
"""

import sys
import os

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from common.config import Config
from common.database import get_database_instance

def investigar_acciones_detalle():
    """Investiga en detalle las acciones sin acciones realizadas"""
    print("=== Investigando las 5 acciones sin acciones realizadas ===")
    
    config = Config()
    nc_connection_string = config.get_db_no_conformidades_connection_string()
    db = get_database_instance(nc_connection_string)
    
    try:
        # 1. Obtener las 5 acciones sin acciones realizadas
        print("\n1. Las 5 acciones sin acciones realizadas:")
        sin_acciones_query = """
        SELECT 
            ac.IDAccionCorrectiva,
            ac.ESTADO,
            ac.FechaFinalUltima,
            ac.AccionCorrectiva,
            nc.CodigoNoConformidad,
            nc.FECHAAPERTURA,
            nc.FECHACIERRE
        FROM TbNCAccionCorrectivas ac
        INNER JOIN TbNoConformidades nc ON ac.IDNoConformidad = nc.IDNoConformidad
        WHERE NOT EXISTS (
            SELECT 1 FROM TbNCAccionesRealizadas ar 
            WHERE ar.IDAccionCorrectiva = ac.IDAccionCorrectiva
        )
        ORDER BY ac.FechaFinalUltima DESC
        """
        sin_acciones = db.execute_query(sin_acciones_query)
        
        for i, row in enumerate(sin_acciones, 1):
            print(f"\n  Acción {i}:")
            print(f"    ID: {row['IDAccionCorrectiva']}")
            print(f"    Estado: {row['ESTADO']}")
            print(f"    Fecha Final: {row['FechaFinalUltima']}")
            print(f"    Acción: {row['AccionCorrectiva']}")
            print(f"    NC: {row['CodigoNoConformidad']}")
            print(f"    NC Apertura: {row['FECHAAPERTURA']}")
            print(f"    NC Cierre: {row['FECHACIERRE']}")
        
        # 2. Verificar cuáles de estas NO están finalizadas
        print("\n2. De estas, cuáles NO están finalizadas:")
        no_finalizadas_query = """
        SELECT 
            ac.IDAccionCorrectiva,
            ac.ESTADO,
            ac.FechaFinalUltima,
            nc.CodigoNoConformidad
        FROM TbNCAccionCorrectivas ac
        INNER JOIN TbNoConformidades nc ON ac.IDNoConformidad = nc.IDNoConformidad
        WHERE ac.ESTADO <> 'FINALIZADA'
        AND NOT EXISTS (
            SELECT 1 FROM TbNCAccionesRealizadas ar 
            WHERE ar.IDAccionCorrectiva = ac.IDAccionCorrectiva
        )
        ORDER BY ac.FechaFinalUltima DESC
        """
        no_finalizadas = db.execute_query(no_finalizadas_query)
        
        print(f"  Total no finalizadas sin acciones: {len(no_finalizadas)}")
        for row in no_finalizadas:
            print(f"    ID: {row['IDAccionCorrectiva']}, Estado: {row['ESTADO']}, Fecha: {row['FechaFinalUltima']}, NC: {row['CodigoNoConformidad']}")
        
        # 3. Verificar todas las acciones no finalizadas (con o sin acciones realizadas)
        print("\n3. Todas las acciones no finalizadas:")
        todas_no_finalizadas_query = """
        SELECT 
            ac.IDAccionCorrectiva,
            ac.ESTADO,
            ac.FechaFinalUltima,
            nc.CodigoNoConformidad
        FROM TbNCAccionCorrectivas ac
        INNER JOIN TbNoConformidades nc ON ac.IDNoConformidad = nc.IDNoConformidad
        WHERE ac.ESTADO <> 'FINALIZADA'
        ORDER BY ac.FechaFinalUltima DESC
        """
        todas_no_finalizadas = db.execute_query(todas_no_finalizadas_query)
        
        print(f"  Total acciones no finalizadas: {len(todas_no_finalizadas)}")
        
        # Agrupar por estado
        estados = {}
        for row in todas_no_finalizadas:
            estado = row['ESTADO']
            if estado not in estados:
                estados[estado] = []
            estados[estado].append(row)
        
        for estado, acciones in estados.items():
            print(f"\n  Estado '{estado}': {len(acciones)} acciones")
            for row in acciones[:3]:  # Mostrar solo las primeras 3
                print(f"    ID: {row['IDAccionCorrectiva']}, Fecha: {row['FechaFinalUltima']}, NC: {row['CodigoNoConformidad']}")
            if len(acciones) > 3:
                print(f"    ... y {len(acciones) - 3} más")
        
        # 4. Verificar fechas futuras vs hoy
        print("\n4. Análisis de fechas vs hoy (2025-07-29):")
        fechas_futuras_query = """
        SELECT 
            ac.IDAccionCorrectiva,
            ac.ESTADO,
            ac.FechaFinalUltima,
            nc.CodigoNoConformidad
        FROM TbNCAccionCorrectivas ac
        INNER JOIN TbNoConformidades nc ON ac.IDNoConformidad = nc.IDNoConformidad
        WHERE ac.ESTADO <> 'FINALIZADA'
        AND ac.FechaFinalUltima > #07/29/2025#
        ORDER BY ac.FechaFinalUltima ASC
        """
        fechas_futuras = db.execute_query(fechas_futuras_query)
        
        print(f"  Acciones no finalizadas con fecha futura (> 2025-07-29): {len(fechas_futuras)}")
        for row in fechas_futuras:
            print(f"    ID: {row['IDAccionCorrectiva']}, Estado: {row['ESTADO']}, Fecha: {row['FechaFinalUltima']}, NC: {row['CodigoNoConformidad']}")
        
        # 5. Verificar fechas vencidas
        print("\n5. Acciones vencidas (fecha <= hoy):")
        fechas_vencidas_query = """
        SELECT 
            ac.IDAccionCorrectiva,
            ac.ESTADO,
            ac.FechaFinalUltima,
            nc.CodigoNoConformidad
        FROM TbNCAccionCorrectivas ac
        INNER JOIN TbNoConformidades nc ON ac.IDNoConformidad = nc.IDNoConformidad
        WHERE ac.ESTADO <> 'FINALIZADA'
        AND ac.FechaFinalUltima IS NOT NULL
        AND ac.FechaFinalUltima <= #07/29/2025#
        ORDER BY ac.FechaFinalUltima DESC
        """
        fechas_vencidas = db.execute_query(fechas_vencidas_query)
        
        print(f"  Acciones no finalizadas vencidas (<= 2025-07-29): {len(fechas_vencidas)}")
        for row in fechas_vencidas[:5]:  # Mostrar solo las primeras 5
            print(f"    ID: {row['IDAccionCorrectiva']}, Estado: {row['ESTADO']}, Fecha: {row['FechaFinalUltima']}, NC: {row['CodigoNoConformidad']}")
        if len(fechas_vencidas) > 5:
            print(f"    ... y {len(fechas_vencidas) - 5} más")
            
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        try:
            db.disconnect()
        except:
            pass

if __name__ == "__main__":
    investigar_acciones_detalle()