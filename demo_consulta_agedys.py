#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demo para probar la consulta SQL corregida de AGEDYS
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from common.database import AccessDatabase
from common.config import Config
import logging

def test_consulta_corregida():
    """Prueba la consulta SQL corregida con el usuario específico"""
    
    # Configurar logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        # Inicializar configuración y base de datos
        config = Config()
        
        # Crear conexión usando AccessDatabase con la cadena de conexión de AGEDYS
        connection_string = config.get_db_agedys_connection_string()
        db = AccessDatabase(connection_string)
        
        # Usuario de prueba que proporcionaste
        usuario = "Ángel Luis Sánchez Cesteros"
        
        print("=" * 60)
        print("🧪 DEMO: Prueba de consulta SQL corregida")
        print("=" * 60)
        print(f"👤 Usuario de prueba: {usuario}")
        print()
        
        # Consulta corregida basada en tu ejemplo
        sql_corregida = """
        SELECT TbFacturasDetalle.NFactura, 
               TbProyectos.CODPROYECTOS, 
               TbProyectos.PETICIONARIO, 
               TbProyectos.DESCRIPCION, 
               TbNPedido.IMPORTEADJUDICADO, 
               TbSuministradoresSAP.Suministrador, 
               TbFacturasDetalle.ImporteFactura, 
               TbFacturasDetalle.NDOCUMENTO, 
               TbExpedientes1.CodExp 
        FROM ((((TbProyectos 
               INNER JOIN TbNPedido ON TbProyectos.CODPROYECTOS = TbNPedido.CODPPD) 
               INNER JOIN TbFacturasDetalle ON TbNPedido.NPEDIDO = TbFacturasDetalle.NPEDIDO) 
               INNER JOIN TbVisadoFacturas_Nueva ON TbFacturasDetalle.IDFactura = TbVisadoFacturas_Nueva.IDFactura) 
               INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente) 
               INNER JOIN TbSuministradoresSAP ON TbNPedido.NAcreedorSAP = TbSuministradoresSAP.AcreedorSAP 
        WHERE TbProyectos.PETICIONARIO = ? 
          AND TbFacturasDetalle.FechaAceptacion IS NULL 
          AND TbVisadoFacturas_Nueva.FRECHAZOTECNICO IS NULL 
          AND TbVisadoFacturas_Nueva.FVISADOTECNICO IS NULL 
          AND TbExpedientes1.AGEDYSGenerico = 'Sí' 
          AND TbExpedientes1.AGEDYSAplica = 'Sí'
        """
        
        print("📋 Consulta SQL a ejecutar:")
        print("-" * 40)
        print(sql_corregida.replace("?", f"'{usuario}'"))
        print()
        
        # Ejecutar consulta con parámetros
        print("⚡ Ejecutando consulta...")
        try:
            resultados = db.execute_query(sql_corregida, (usuario,))
            
            print(f"✅ Consulta ejecutada exitosamente")
            print(f"📊 Número de registros encontrados: {len(resultados)}")
            print()
            
            if resultados:
                print("📋 Primeros resultados:")
                print("-" * 40)
                for i, resultado in enumerate(resultados[:3]):  # Mostrar solo los primeros 3
                    print(f"Registro {i+1}:")
                    for campo, valor in resultado.items():
                        print(f"  {campo}: {valor}")
                    print()
                
                if len(resultados) > 3:
                    print(f"... y {len(resultados) - 3} registros más")
            else:
                print("ℹ️  No se encontraron registros para este usuario")
                
        except Exception as e:
            print(f"❌ Error al ejecutar la consulta: {str(e)}")
            print(f"🔍 Tipo de error: {type(e).__name__}")
            
            # Intentar con concatenación directa como fallback
            print("\n🔄 Intentando con concatenación directa...")
            sql_concatenada = sql_corregida.replace("?", f"'{usuario}'")
            
            try:
                resultados = db.execute_query(sql_concatenada)
                print(f"✅ Consulta con concatenación ejecutada exitosamente")
                print(f"📊 Número de registros encontrados: {len(resultados)}")
                
                if resultados:
                    print("\n📋 Primer resultado:")
                    print("-" * 40)
                    for campo, valor in resultados[0].items():
                        print(f"  {campo}: {valor}")
                        
            except Exception as e2:
                print(f"❌ Error también con concatenación: {str(e2)}")
                return False
        
        print("\n" + "=" * 60)
        print("✅ Demo completado")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"❌ Error general en el demo: {str(e)}")
        return False
    finally:
        try:
            db.disconnect()
        except:
            pass

if __name__ == "__main__":
    test_consulta_corregida()