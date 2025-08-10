#!/usr/bin/env python3
"""
Script para probar individualmente las consultas SQL de get_distinct_technical_users
y diagnosticar errores específicos en cada una.
"""

import sys
from pathlib import Path

# Agregar el directorio raíz del proyecto al path
sys.path.insert(0, str(Path(__file__).parent))

from common.config import Config
from common.database import AccessDatabase

def test_individual_queries():
    """Prueba cada consulta SQL individualmente para diagnosticar errores."""
    
    # Configuración
    config = Config()
    
    try:
        # Configurar la conexión
        connection_string = config.get_db_riesgos_connection_string()
        
        print(f"Conectando a base de datos de riesgos")
        
        # Crear instancia de AccessDatabase
        db = AccessDatabase(connection_string)
        db.connect()
        print("Conexión establecida exitosamente")
        
        # Lista de consultas SQL
        queries = [
            # 1. EDICIONESNECESITANPROPUESTAPUBLICACION
            """
            SELECT DISTINCT TbUsuariosAplicaciones.UsuarioRed, TbUsuariosAplicaciones.Nombre, TbUsuariosAplicaciones.CorreoUsuario
            FROM (((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente)
            INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente)
            INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id)
            INNER JOIN TbProyectosEdiciones ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto
            WHERE TbProyectos.ParaInformeAvisos <> 'No'
              AND TbProyectos.FechaCierre IS NULL
              AND TbProyectosEdiciones.FechaPublicacion IS NULL
              AND DateDiff('d',Now(),TbProyectos.FechaMaxProximaPublicacion) <= 15
              AND TbExpedientesResponsables.EsJefeProyecto = 'Sí'
              AND TbExpedientesResponsables.CorreoSiempre = 'Sí'
              AND TbProyectosEdiciones.FechaPreparadaParaPublicar IS NULL
              AND TbUsuariosAplicaciones.FechaBaja IS NULL
            """,
            
            # 2. EDICIONESCONPROPUESTADEPUBLICACIONRECHAZADAS
            """
            SELECT DISTINCT TbUsuariosAplicaciones.UsuarioRed, TbUsuariosAplicaciones.Nombre, TbUsuariosAplicaciones.CorreoUsuario
            FROM (((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente)
            INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente)
            INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id)
            INNER JOIN TbProyectosEdiciones ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto
            WHERE TbProyectos.ParaInformeAvisos <> 'No'
              AND TbProyectos.FechaCierre IS NULL
              AND TbProyectosEdiciones.FechaPublicacion IS NULL
              AND TbExpedientesResponsables.EsJefeProyecto = 'Sí'
              AND TbExpedientesResponsables.CorreoSiempre = 'Sí'
              AND TbUsuariosAplicaciones.FechaBaja IS NULL
              AND TbProyectosEdiciones.FechaPreparadaParaPublicar IS NOT NULL
              AND TbProyectosEdiciones.PropuestaRechazadaPorCalidadFecha IS NOT NULL
            """,
            
            # 3. RIESGOSACEPTADOSNOMOTIVADOS
            """
            SELECT DISTINCT TbUsuariosAplicaciones.UsuarioRed, TbUsuariosAplicaciones.Nombre, TbUsuariosAplicaciones.CorreoUsuario
            FROM (((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente)
            INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente)
            INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id)
            INNER JOIN (TbProyectosEdiciones INNER JOIN TbRiesgos ON TbProyectosEdiciones.IDEdicion = TbRiesgos.IDEdicion)
            ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto
            WHERE TbProyectos.ParaInformeAvisos <> 'No'
              AND TbProyectos.FechaCierre IS NULL
              AND TbProyectosEdiciones.FechaPublicacion IS NULL
              AND TbExpedientesResponsables.EsJefeProyecto = 'Sí'
              AND TbExpedientesResponsables.CorreoSiempre = 'Sí'
              AND TbUsuariosAplicaciones.FechaBaja IS NULL
              AND TbRiesgos.Mitigacion = 'Aceptar'
              AND TbRiesgos.JustificacionAceptacionRiesgo IS NULL
            """,
            
            # 4. RIESGOSACEPTADOSRECHAZADOS
            """
            SELECT DISTINCT TbUsuariosAplicaciones.UsuarioRed, TbUsuariosAplicaciones.Nombre, TbUsuariosAplicaciones.CorreoUsuario
            FROM (((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente)
            INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente)
            INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id)
            INNER JOIN (TbProyectosEdiciones INNER JOIN TbRiesgos ON TbProyectosEdiciones.IDEdicion = TbRiesgos.IDEdicion)
            ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto
            WHERE TbProyectos.ParaInformeAvisos <> 'No'
              AND TbProyectos.FechaCierre IS NULL
              AND TbProyectosEdiciones.FechaPublicacion IS NULL
              AND TbExpedientesResponsables.EsJefeProyecto = 'Sí'
              AND TbExpedientesResponsables.CorreoSiempre = 'Sí'
              AND TbUsuariosAplicaciones.FechaBaja IS NULL
              AND TbRiesgos.Mitigacion = 'Aceptar'
              AND TbRiesgos.FechaRechazoAceptacionPorCalidad IS NOT NULL
            """,
            
            # 5. RIESGOSRETIRADOSNOMOTIVADOS
            """
            SELECT DISTINCT TbUsuariosAplicaciones.UsuarioRed, TbUsuariosAplicaciones.Nombre, TbUsuariosAplicaciones.CorreoUsuario
            FROM (((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente)
            INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente)
            INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id)
            INNER JOIN (TbProyectosEdiciones INNER JOIN TbRiesgos ON TbProyectosEdiciones.IDEdicion = TbRiesgos.IDEdicion)
            ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto
            WHERE TbProyectos.ParaInformeAvisos <> 'No'
              AND TbProyectos.FechaCierre IS NULL
              AND TbProyectosEdiciones.FechaPublicacion IS NULL
              AND TbExpedientesResponsables.EsJefeProyecto = 'Sí'
              AND TbExpedientesResponsables.CorreoSiempre = 'Sí'
              AND TbUsuariosAplicaciones.FechaBaja IS NULL
              AND TbRiesgos.FechaRetirado IS NOT NULL
              AND TbRiesgos.JustificacionRetiroRiesgo IS NULL
            """,
            
            # 6. RIESGOSRETIRADOSRECHAZADOS
            """
            SELECT DISTINCT TbUsuariosAplicaciones.UsuarioRed, TbUsuariosAplicaciones.Nombre, TbUsuariosAplicaciones.CorreoUsuario
            FROM (((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente)
            INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente)
            INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id)
            INNER JOIN (TbProyectosEdiciones INNER JOIN TbRiesgos ON TbProyectosEdiciones.IDEdicion = TbRiesgos.IDEdicion)
            ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto
            WHERE TbProyectos.ParaInformeAvisos <> 'No'
              AND TbProyectos.FechaCierre IS NULL
              AND TbProyectosEdiciones.FechaPublicacion IS NULL
              AND TbExpedientesResponsables.EsJefeProyecto = 'Sí'
              AND TbExpedientesResponsables.CorreoSiempre = 'Sí'
              AND TbUsuariosAplicaciones.FechaBaja IS NULL
              AND TbRiesgos.FechaRetirado IS NOT NULL
              AND TbRiesgos.FechaRechazoRetiroPorCalidad IS NOT NULL
            """,
            
            # 7. RIESGOSCONACCIONESMITIGACIONPARAREPLANIFICAR
            """
            SELECT DISTINCT TbUsuariosAplicaciones.UsuarioRed, TbUsuariosAplicaciones.Nombre, TbUsuariosAplicaciones.CorreoUsuario
            FROM (((((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente)
            INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente)
            INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id)
            INNER JOIN (TbProyectosEdiciones INNER JOIN TbRiesgos ON TbProyectosEdiciones.IDEdicion = TbRiesgos.IDEdicion)
            ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto) INNER JOIN TbRiesgosPlanMitigacionPpal
            ON TbRiesgos.IDRiesgo = TbRiesgosPlanMitigacionPpal.IDRiesgo) INNER JOIN TbRiesgosPlanMitigacionDetalle
            ON TbRiesgosPlanMitigacionPpal.IDMitigacion = TbRiesgosPlanMitigacionDetalle.IDMitigacion
            WHERE TbProyectos.ParaInformeAvisos <> 'No'
              AND TbProyectos.FechaCierre IS NULL
              AND TbProyectosEdiciones.FechaPublicacion IS NULL
              AND TbExpedientesResponsables.EsJefeProyecto = 'Sí'
              AND TbExpedientesResponsables.CorreoSiempre = 'Sí'
              AND TbUsuariosAplicaciones.FechaBaja IS NULL
              AND TbRiesgos.FechaRetirado IS NULL
              AND TbRiesgos.Mitigacion <> 'Aceptar'
              AND TbRiesgosPlanMitigacionDetalle.FechaFinReal IS NULL
              AND TbRiesgosPlanMitigacionDetalle.FechaFinPrevista <= Date()
            """,
            
            # 8. RIESGOSCONACCIONESCONTINGENCIAPARAREPLANIFICAR
            """
            SELECT DISTINCT TbUsuariosAplicaciones.UsuarioRed, TbUsuariosAplicaciones.Nombre, TbUsuariosAplicaciones.CorreoUsuario
            FROM (((((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente)
            INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente)
            INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id)
            INNER JOIN (TbProyectosEdiciones INNER JOIN TbRiesgos ON TbProyectosEdiciones.IDEdicion = TbRiesgos.IDEdicion)
            ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto) INNER JOIN TbRiesgosPlanContingenciaPpal
            ON TbRiesgos.IDRiesgo = TbRiesgosPlanContingenciaPpal.IDRiesgo) INNER JOIN TbRiesgosPlanContingenciaDetalle
            ON TbRiesgosPlanContingenciaPpal.IDContingencia = TbRiesgosPlanContingenciaDetalle.IDContingencia
            WHERE TbProyectos.ParaInformeAvisos <> 'No'
              AND TbProyectos.FechaCierre IS NULL
              AND TbProyectosEdiciones.FechaPublicacion IS NULL
              AND TbExpedientesResponsables.EsJefeProyecto = 'Sí'
              AND TbExpedientesResponsables.CorreoSiempre = 'Sí'
              AND TbUsuariosAplicaciones.FechaBaja IS NULL
              AND TbRiesgos.FechaRetirado IS NULL
              AND TbRiesgos.Mitigacion <> 'Aceptar'
              AND TbRiesgosPlanContingenciaDetalle.FechaFinReal IS NULL
              AND TbRiesgosPlanContingenciaDetalle.FechaFinPrevista <= Date()
            """
        ]
        
        query_names = [
            "EDICIONESNECESITANPROPUESTAPUBLICACION",
            "EDICIONESCONPROPUESTADEPUBLICACIONRECHAZADAS", 
            "RIESGOSACEPTADOSNOMOTIVADOS",
            "RIESGOSACEPTADOSRECHAZADOS",
            "RIESGOSRETIRADOSNOMOTIVADOS",
            "RIESGOSRETIRADOSRECHAZADOS",
            "RIESGOSCONACCIONESMITIGACIONPARAREPLANIFICAR",
            "RIESGOSCONACCIONESCONTINGENCIAPARAREPLANIFICAR"
        ]
        
        print("\n" + "="*80)
        print("PROBANDO CONSULTAS SQL INDIVIDUALMENTE")
        print("="*80)
        
        # Probar cada consulta individualmente
        for i, query in enumerate(queries):
            query_name = query_names[i]
            print(f"\n--- Consulta {i+1}/8: {query_name} ---")
            
            try:
                result = db.execute_query(query)
                if result:
                    print(f"✓ ÉXITO: {len(result)} registros encontrados")
                    # Mostrar los primeros 3 registros como muestra
                    for j, row in enumerate(result[:3]):
                        print(f"  Registro {j+1}: {row[0]} | {row[1]} | {row[2]}")
                    if len(result) > 3:
                        print(f"  ... y {len(result) - 3} registros más")
                else:
                    print("✓ ÉXITO: 0 registros encontrados")
                    
            except Exception as e:
                print(f"✗ ERROR: {str(e)}")
                print(f"  Tipo de error: {type(e).__name__}")
        
        print("\n" + "="*80)
        print("RESUMEN DE PRUEBAS COMPLETADO")
        print("="*80)
        
    except Exception as e:
        print(f"Error conectando a la base de datos: {e}")
        
    finally:
        try:
            db.disconnect()
            print("\nConexión cerrada")
        except:
            pass

if __name__ == "__main__":
    test_individual_queries()