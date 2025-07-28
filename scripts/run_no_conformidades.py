"""
Script principal para ejecutar las tareas de No Conformidades
Equivalente al NoConformidades.vbs original
"""

import sys
import os
from datetime import datetime

# Agregar el directorio padre al path para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.common.logger import setup_logger
from src.no_conformidades.no_conformidades_manager import NoConformidadesManager
from src.no_conformidades.email_notifications import EmailNotificationManager


def ejecutar_tarea_calidad():
    """Ejecuta la tarea de calidad (equivalente a RealizarTareaCalidad)"""
    logger = setup_logger(__name__)
    logger.info("=== INICIANDO TAREA DE CALIDAD ===")
    
    nc_manager = None
    email_manager = EmailNotificationManager()
    
    try:
        # Inicializar el gestor de No Conformidades
        nc_manager = NoConformidadesManager()
        nc_manager.conectar_bases_datos()
        nc_manager.cargar_usuarios()
        
        # Obtener datos para el reporte de calidad
        logger.info("Obteniendo datos para reporte de calidad...")
        
        ncs_eficacia = nc_manager.obtener_nc_resueltas_pendientes_eficacia()
        ncs_caducar = nc_manager.obtener_nc_proximas_caducar()
        ncs_sin_acciones = nc_manager.obtener_nc_registradas_sin_acciones()
        
        # Log de resultados
        logger.info(f"NCs pendientes eficacia: {len(ncs_eficacia)}")
        logger.info(f"NCs próximas a caducar: {len(ncs_caducar)}")
        logger.info(f"NCs sin acciones: {len(ncs_sin_acciones)}")
        
        # Verificar si hay datos para reportar
        total_items = len(ncs_eficacia) + len(ncs_caducar) + len(ncs_sin_acciones)
        
        if total_items == 0:
            logger.info("No hay elementos para reportar en la tarea de calidad")
        else:
            # Obtener destinatarios
            correos_calidad = nc_manager.obtener_cadena_correos_calidad()
            correos_admin = nc_manager.obtener_cadena_correos_administradores()
            
            logger.info(f"Destinatarios calidad: {correos_calidad}")
            logger.info(f"Destinatarios admin: {correos_admin}")
            
            # Enviar notificación
            if correos_calidad or correos_admin:
                resultado_email = email_manager.enviar_notificacion_calidad(
                    ncs_eficacia=ncs_eficacia,
                    ncs_caducar=ncs_caducar,
                    ncs_sin_acciones=ncs_sin_acciones,
                    destinatarios_calidad=correos_calidad,
                    destinatarios_admin=correos_admin
                )
                
                if resultado_email:
                    logger.info("Reporte de calidad enviado correctamente")
                    email_manager.marcar_email_como_enviado("calidad")
                else:
                    logger.error("Error enviando reporte de calidad")
            else:
                logger.warning("No hay destinatarios configurados para el reporte de calidad")
        
        # Registrar la ejecución de la tarea
        nc_manager.registrar_tarea_calidad()
        logger.info("=== TAREA DE CALIDAD COMPLETADA ===")
        
        return True
        
    except Exception as e:
        logger.error(f"Error ejecutando tarea de calidad: {e}")
        return False
        
    finally:
        if nc_manager:
            nc_manager.desconectar_bases_datos()


def ejecutar_tarea_tecnica():
    """Ejecuta la tarea técnica (equivalente a RealizarTareaTecnica)"""
    logger = setup_logger(__name__)
    logger.info("=== INICIANDO TAREA TÉCNICA ===")
    
    nc_manager = None
    email_manager = EmailNotificationManager()
    
    try:
        # Inicializar el gestor de No Conformidades
        nc_manager = NoConformidadesManager()
        nc_manager.conectar_bases_datos()
        nc_manager.cargar_usuarios()
        
        # Obtener ARAPs próximas a vencer
        logger.info("Obteniendo ARAPs próximas a vencer...")
        
        arapcs = nc_manager.obtener_arapc_proximas_vencer()
        
        # Log de resultados
        logger.info(f"ARAPs próximas a vencer: {len(arapcs)}")
        
        if len(arapcs) == 0:
            logger.info("No hay ARAPs próximas a vencer")
        else:
            # Obtener destinatarios
            correos_admin = nc_manager.obtener_cadena_correos_administradores()
            
            logger.info(f"Destinatarios admin: {correos_admin}")
            
            # Enviar reporte general técnico
            if correos_admin:
                resultado_email = email_manager.enviar_notificacion_tecnica(
                    arapcs=arapcs,
                    destinatarios_tecnicos="",  # No hay lista específica de técnicos
                    destinatarios_admin=correos_admin
                )
                
                if resultado_email:
                    logger.info("Reporte técnico general enviado correctamente")
                    email_manager.marcar_email_como_enviado("tecnica_general")
                else:
                    logger.error("Error enviando reporte técnico general")
            
            # Enviar notificaciones individuales a responsables
            logger.info("Enviando notificaciones individuales a responsables...")
            resultados_individuales = email_manager.enviar_notificaciones_individuales_arapcs(
                arapcs=arapcs,
                usuarios_tecnicos=nc_manager.usuarios_tecnicos
            )
            
            exitosos = sum(1 for r in resultados_individuales.values() if r)
            total = len(resultados_individuales)
            logger.info(f"Notificaciones individuales: {exitosos}/{total} enviadas")
        
        # Registrar la ejecución de la tarea
        nc_manager.registrar_tarea_tecnica()
        logger.info("=== TAREA TÉCNICA COMPLETADA ===")
        
        return True
        
    except Exception as e:
        logger.error(f"Error ejecutando tarea técnica: {e}")
        return False
        
    finally:
        if nc_manager:
            nc_manager.desconectar_bases_datos()


def main():
    """Función principal que determina qué tareas ejecutar"""
    logger = setup_logger(__name__)
    logger.info("=== INICIANDO PROCESAMIENTO DE NO CONFORMIDADES ===")
    
    nc_manager = None
    
    try:
        # Inicializar el gestor para verificar qué tareas se requieren
        nc_manager = NoConformidadesManager()
        nc_manager.conectar_bases_datos()
        
        # Verificar si se requiere ejecutar tarea de calidad
        requiere_calidad = nc_manager.determinar_si_requiere_tarea_calidad()
        logger.info(f"Requiere tarea de calidad: {requiere_calidad}")
        
        # Verificar si se requiere ejecutar tarea técnica
        requiere_tecnica = nc_manager.determinar_si_requiere_tarea_tecnica()
        logger.info(f"Requiere tarea técnica: {requiere_tecnica}")
        
        # Desconectar temporalmente para que cada tarea maneje sus propias conexiones
        nc_manager.desconectar_bases_datos()
        nc_manager = None
        
        # Ejecutar tareas según sea necesario
        resultados = []
        
        if requiere_calidad:
            logger.info("Ejecutando tarea de calidad...")
            resultado_calidad = ejecutar_tarea_calidad()
            resultados.append(("Calidad", resultado_calidad))
        
        if requiere_tecnica:
            logger.info("Ejecutando tarea técnica...")
            resultado_tecnica = ejecutar_tarea_tecnica()
            resultados.append(("Técnica", resultado_tecnica))
        
        # Resumen de resultados
        if resultados:
            logger.info("=== RESUMEN DE EJECUCIÓN ===")
            for tarea, resultado in resultados:
                estado = "EXITOSA" if resultado else "FALLIDA"
                logger.info(f"Tarea {tarea}: {estado}")
        else:
            logger.info("No se requirió ejecutar ninguna tarea")
        
        logger.info("=== PROCESAMIENTO COMPLETADO ===")
        
        # Retornar True si todas las tareas fueron exitosas
        return all(resultado for _, resultado in resultados) if resultados else True
        
    except Exception as e:
        logger.error(f"Error en procesamiento principal: {e}")
        return False
        
    finally:
        if nc_manager:
            nc_manager.desconectar_bases_datos()


if __name__ == "__main__":
    try:
        exito = main()
        sys.exit(0 if exito else 1)
    except Exception as e:
        logger = setup_logger(__name__)
        logger.error(f"Error crítico en ejecución: {e}")
        sys.exit(1)