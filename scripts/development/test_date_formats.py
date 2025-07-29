#!/usr/bin/env python3
"""
Script para probar diferentes formatos de fecha en Access
"""

import sys
import os
from datetime import datetime, timedelta

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from common.config import Config
from common.database import get_database_instance

def _formatear_fecha_access(fecha):
    """
    Formatear fecha para consultas de Access
    
    Args:
        fecha: Fecha a formatear (datetime.date, datetime.datetime o string)
        
    Returns:
        str: Fecha formateada como #MM/dd/yyyy# para Access
    """
    from datetime import datetime, date
    
    if fecha is None:
        return None
        
    # Si es string, intentar parsearlo
    if isinstance(fecha, str):
        try:
            # Intentar formato YYYY-MM-DD
            fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()
        except ValueError:
            try:
                # Intentar formato MM/DD/YYYY
                fecha_obj = datetime.strptime(fecha, '%m/%d/%Y').date()
            except ValueError:
                print(f"No se pudo parsear la fecha: {fecha}")
                return None
    elif isinstance(fecha, datetime):
        fecha_obj = fecha.date()
    elif isinstance(fecha, date):
        fecha_obj = fecha
    else:
        print(f"Tipo de fecha no soportado: {type(fecha)}")
        return None
    
    # Formatear para Access: #MM/dd/yyyy#
    return f"#{fecha_obj.strftime('%m/%d/%Y')}#"

def probar_formatos_fecha():
    """Prueba diferentes formatos de fecha en Access"""
    print("=== Probando formatos de fecha en Access ===")
    
    config = Config()
    nc_connection_string = config.get_db_no_conformidades_connection_string()
    db = get_database_instance(nc_connection_string)
    
    try:
        fecha_hoy = datetime.now().date()
        fecha_limite = fecha_hoy + timedelta(days=15)
        
        print(f"Fecha hoy: {fecha_hoy}")
        print(f"Fecha límite: {fecha_limite}")
        
        # 1. Método recomendado - usando formato Access directo (MM/dd/yyyy)
        print("\n1. Método recomendado con formato Access (#MM/dd/yyyy#):")
        try:
            fecha_hoy_str = _formatear_fecha_access(fecha_hoy)
            fecha_limite_str = _formatear_fecha_access(fecha_limite)
            
            query_access = f"""
            SELECT COUNT(*) as total
            FROM TbNCAccionCorrectivas ac
            WHERE ac.FechaFinalUltima IS NOT NULL
            AND ac.FechaFinalUltima <= {fecha_limite_str}
            """
            print(f"  Query: {query_access}")
            resultado_access = db.execute_query(query_access)
            print(f"  Resultado con formato Access: {resultado_access[0]['total']}")
        except Exception as e:
            print(f"  Error con formato Access: {e}")
        
        # 2. Método con parámetros (para comparación)
        print("\n2. Método con parámetros (para comparación):")
        try:
            query_parametros = """
            SELECT COUNT(*) as total
            FROM TbNCAccionCorrectivas ac
            WHERE ac.FechaFinalUltima IS NOT NULL
            AND ac.FechaFinalUltima <= ?
            """
            resultado_param = db.execute_query(query_parametros, [fecha_limite])
            print(f"  Resultado con parámetros: {resultado_param[0]['total']}")
        except Exception as e:
            print(f"  Error con parámetros: {e}")
        
        # 3. Probar la consulta ARAPC completa con formato Access
        print("\n3. Consulta ARAPC completa con formato Access:")
        try:
            fecha_hoy_str = _formatear_fecha_access(fecha_hoy)
            fecha_limite_str = _formatear_fecha_access(fecha_limite)
            
            arapc_query = f"""
            SELECT COUNT(*) as total
            FROM TbNCAccionCorrectivas ac
            INNER JOIN TbNoConformidades nc ON ac.IDNoConformidad = nc.IDNoConformidad
            WHERE ac.ESTADO <> 'FINALIZADA'
            AND ac.FechaFinalUltima IS NOT NULL
            AND ac.FechaFinalUltima >= {fecha_hoy_str}
            AND ac.FechaFinalUltima <= {fecha_limite_str}
            AND NOT EXISTS (
                SELECT 1 FROM TbNCAccionesRealizadas ar 
                WHERE ar.IDAccionCorrectiva = ac.IDAccionCorrectiva
            )
            """
            print(f"  Query ARAPC: {arapc_query}")
            resultado_arapc = db.execute_query(arapc_query)
            print(f"  Resultado ARAPC: {resultado_arapc[0]['total']}")
        except Exception as e:
            print(f"  Error ARAPC: {e}")
        
        # 4. Probar con fechas en el pasado
        print("\n4. Consulta ARAPC con fechas en el pasado:")
        try:
            fecha_pasado = datetime(2025, 7, 1).date()
            fecha_limite_pasado = datetime(2025, 7, 25).date()
            
            fecha_pasado_str = _formatear_fecha_access(fecha_pasado)
            fecha_limite_pasado_str = _formatear_fecha_access(fecha_limite_pasado)
            
            arapc_pasado_query = f"""
            SELECT COUNT(*) as total
            FROM TbNCAccionCorrectivas ac
            INNER JOIN TbNoConformidades nc ON ac.IDNoConformidad = nc.IDNoConformidad
            WHERE ac.ESTADO <> 'FINALIZADA'
            AND ac.FechaFinalUltima IS NOT NULL
            AND ac.FechaFinalUltima >= {fecha_pasado_str}
            AND ac.FechaFinalUltima <= {fecha_limite_pasado_str}
            AND NOT EXISTS (
                SELECT 1 FROM TbNCAccionesRealizadas ar 
                WHERE ar.IDAccionCorrectiva = ac.IDAccionCorrectiva
            )
            """
            print(f"  Query ARAPC pasado: {arapc_pasado_query}")
            resultado_arapc_pasado = db.execute_query(arapc_pasado_query)
            print(f"  Resultado ARAPC pasado: {resultado_arapc_pasado[0]['total']}")
        except Exception as e:
            print(f"  Error ARAPC pasado: {e}")
        
        # 5. Mostrar algunas fechas de la base de datos para comparar
        print("\n5. Muestra de fechas en la base de datos:")
        try:
            fechas_query = """
            SELECT TOP 5
                ac.IDAccionCorrectiva,
                ac.ESTADO,
                ac.FechaFinalUltima
            FROM TbNCAccionCorrectivas ac
            WHERE ac.FechaFinalUltima IS NOT NULL
            ORDER BY ac.FechaFinalUltima DESC
            """
            fechas_resultado = db.execute_query(fechas_query)
            for row in fechas_resultado:
                print(f"  ID: {row['IDAccionCorrectiva']}, Estado: {row['ESTADO']}, Fecha: {row['FechaFinalUltima']}")
        except Exception as e:
            print(f"  Error obteniendo fechas: {e}")
            
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
    probar_formatos_fecha()