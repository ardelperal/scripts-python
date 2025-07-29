"""
Script principal para ejecutar las tareas de No Conformidades
Equivalente al NoConformidades.vbs original

Uso:
    python run_no_conformidades.py                    # Ejecución normal (verifica horarios)
    python run_no_conformidades.py --force-calidad    # Fuerza ejecución de tarea de calidad
    python run_no_conformidades.py --force-tecnica    # Fuerza ejecución de tarea técnica
    python run_no_conformidades.py --force-all        # Fuerza ejecución de todas las tareas
"""

import sys
import os
import argparse
from datetime import datetime
from pathlib import Path

# Agregar el directorio src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from common.logger import setup_logger
from common.utils import (
    should_execute_task, get_admin_emails_string, get_quality_emails_string, 
    register_task_completion
)
from no_conformidades.no_conformidades_manager import NoConformidadesManager
from no_conformidades.email_notifications import EmailNotificationManager


def parse_arguments():
    """Parsea los argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(
        description="Script para ejecutar tareas de No Conformidades",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  %(prog)s                    # Ejecución normal (verifica horarios)
  %(prog)s --force-calidad    # Fuerza ejecución de tarea de calidad
  %(prog)s --force-tecnica    # Fuerza ejecución de tarea técnica  
  %(prog)s --force-all        # Fuerza ejecución de todas las tareas
  %(prog)s --dry-run          # Simula ejecución sin enviar emails
        """
    )
    
    # Grupo de opciones de forzado (mutuamente excluyentes)
    force_group = parser.add_mutually_exclusive_group()
    force_group.add_argument(
        '--force-calidad', 
        action='store_true',
        help='Fuerza la ejecución de la tarea de calidad independientemente del horario'
    )
    force_group.add_argument(
        '--force-tecnica', 
        action='store_true',
        help='Fuerza la ejecución de la tarea técnica independientemente del horario'
    )
    force_group.add_argument(
        '--force-all', 
        action='store_true',
        help='Fuerza la ejecución de todas las tareas independientemente del horario'
    )
    
    # Opciones adicionales
    parser.add_argument(
        '--dry-run', 
        action='store_true',
        help='Simula la ejecución sin enviar emails reales'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Habilita logging detallado'
    )
    
    return parser.parse_args()


def ejecutar_tarea_calidad(dry_run=False):
    """Ejecuta la tarea de calidad (equivalente a RealizarTareaCalidad)"""
    logger = setup_logger(__name__)
    logger.info("=== INICIANDO TAREA DE CALIDAD ===")
    
    if dry_run:
        logger.info("MODO DRY-RUN: No se enviarán emails reales")
    
    email_manager = EmailNotificationManager()
    
    try:
        # Usar context manager para manejo automático de conexiones
        with NoConformidadesManager() as nc_manager:
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
                # Obtener destinatarios usando funciones comunes
                correos_calidad = get_quality_emails_string(nc_manager.db_nc, 1)  # App ID 1 para NC
                correos_admin = get_admin_emails_string(nc_manager.db_nc)
                
                logger.info(f"Destinatarios calidad: {correos_calidad}")
                logger.info(f"Destinatarios admin: {correos_admin}")
                
                # Enviar notificación
                if correos_calidad or correos_admin:
                    if dry_run:
                        logger.info("DRY-RUN: Se habría enviado reporte de calidad")
                        resultado_email = True  # Simular éxito
                    else:
                        resultado_email = email_manager.enviar_notificacion_calidad(
                            ncs_eficacia=ncs_eficacia,
                            ncs_caducar=ncs_caducar,
                            ncs_sin_acciones=ncs_sin_acciones,
                            destinatarios_calidad=correos_calidad,
                            destinatarios_admin=correos_admin
                        )
                    
                    if resultado_email:
                        logger.info("Reporte de calidad enviado correctamente")
                        if not dry_run:
                            email_manager.marcar_email_como_enviado("calidad")
                    else:
                        logger.error("Error enviando reporte de calidad")
                else:
                    logger.warning("No hay destinatarios configurados para el reporte de calidad")
            
            # Registrar la ejecución de la tarea usando función común
            if not dry_run:
                register_task_completion(nc_manager.db_tareas, "NoConformidadesCalidad")
            else:
                logger.info("DRY-RUN: Se habría registrado la ejecución de la tarea")
        
        logger.info("=== TAREA DE CALIDAD COMPLETADA ===")
        return True
        
    except Exception as e:
        logger.error(f"Error ejecutando tarea de calidad: {e}")
        return False


def ejecutar_tarea_tecnica(dry_run=False):
    """Ejecuta la tarea técnica (equivalente a RealizarTareaTecnica)"""
    logger = setup_logger(__name__)
    logger.info("=== INICIANDO TAREA TÉCNICA ===")
    
    if dry_run:
        logger.info("MODO DRY-RUN: No se enviarán emails reales")
    
    email_manager = EmailNotificationManager()
    
    try:
        # Usar context manager para manejo automático de conexiones
        with NoConformidadesManager() as nc_manager:
            # Obtener ARAPs próximas a vencer
            logger.info("Obteniendo ARAPs próximas a vencer...")
            
            arapcs = nc_manager.obtener_arapc_proximas_vencer()
            
            # Log de resultados
            logger.info(f"ARAPs próximas a vencer: {len(arapcs)}")
            
            if len(arapcs) == 0:
                logger.info("No hay ARAPs próximas a vencer")
            else:
                # Obtener destinatarios usando función común
                correos_admin = get_admin_emails_string(nc_manager.db_nc)
                
                logger.info(f"Destinatarios admin: {correos_admin}")
                
                # Enviar reporte general técnico
                if correos_admin:
                    if dry_run:
                        logger.info("DRY-RUN: Se habría enviado reporte técnico general")
                        resultado_email = True  # Simular éxito
                    else:
                        resultado_email = email_manager.enviar_notificacion_tecnica(
                            arapcs=arapcs,
                            destinatarios_tecnicos="",  # No hay lista específica de técnicos
                            destinatarios_admin=correos_admin
                        )
                    
                    if resultado_email:
                        logger.info("Reporte técnico general enviado correctamente")
                        if not dry_run:
                            email_manager.marcar_email_como_enviado("tecnica_general")
                    else:
                        logger.error("Error enviando reporte técnico general")
                
                # Enviar notificaciones individuales a responsables
                logger.info("Enviando notificaciones individuales a responsables...")
                # Obtener usuarios técnicos usando función común
                from common.utils import get_technical_users
                usuarios_tecnicos = get_technical_users(nc_manager.db_nc, 1)  # App ID 1 para NC
                
                if dry_run:
                    logger.info(f"DRY-RUN: Se habrían enviado {len(arapcs)} notificaciones individuales")
                    exitosos = len(arapcs)
                    total = len(arapcs)
                else:
                    resultados_individuales = email_manager.enviar_notificaciones_individuales_arapcs(
                        arapcs=arapcs,
                        usuarios_tecnicos=usuarios_tecnicos
                    )
                    
                    exitosos = sum(1 for r in resultados_individuales.values() if r)
                    total = len(resultados_individuales)
                
                logger.info(f"Notificaciones individuales: {exitosos}/{total} enviadas")
            
            # Registrar la ejecución de la tarea usando función común
            if not dry_run:
                register_task_completion(nc_manager.db_tareas, "NoConformidadesTecnica")
            else:
                logger.info("DRY-RUN: Se habría registrado la ejecución de la tarea")
        
        logger.info("=== TAREA TÉCNICA COMPLETADA ===")
        return True
        
    except Exception as e:
        logger.error(f"Error ejecutando tarea técnica: {e}")
        return False


def main():
    """Función principal que determina qué tareas ejecutar"""
    # Parsear argumentos de línea de comandos
    args = parse_arguments()
    
    logger = setup_logger(__name__)
    logger.info("=== INICIANDO PROCESAMIENTO DE NO CONFORMIDADES ===")
    
    if args.dry_run:
        logger.info("MODO DRY-RUN ACTIVADO: No se enviarán emails ni se registrarán ejecuciones")
    
    # Determinar qué tareas ejecutar basado en argumentos
    ejecutar_calidad = False
    ejecutar_tecnica = False
    
    if args.force_all:
        logger.info("FORZANDO EJECUCIÓN DE TODAS LAS TAREAS")
        ejecutar_calidad = True
        ejecutar_tecnica = True
    elif args.force_calidad:
        logger.info("FORZANDO EJECUCIÓN DE TAREA DE CALIDAD")
        ejecutar_calidad = True
    elif args.force_tecnica:
        logger.info("FORZANDO EJECUCIÓN DE TAREA TÉCNICA")
        ejecutar_tecnica = True
    else:
        # Ejecución normal: verificar horarios
        logger.info("Verificando horarios para ejecución normal...")
        
        try:
            # Usar context manager para verificar qué tareas se requieren
            with NoConformidadesManager() as nc_manager:
                # Verificar si se requiere ejecutar tarea de calidad usando función común
                ejecutar_calidad = should_execute_task(nc_manager.db_tareas, "NoConformidadesCalidad", "daily")
                logger.info(f"Requiere tarea de calidad: {ejecutar_calidad}")
                
                # Verificar si se requiere ejecutar tarea técnica usando función común
                ejecutar_tecnica = should_execute_task(nc_manager.db_tareas, "NoConformidadesTecnica", "daily")
                logger.info(f"Requiere tarea técnica: {ejecutar_tecnica}")
                
        except Exception as e:
            logger.error(f"Error verificando horarios: {e}")
            return False
    
    # Ejecutar tareas según sea necesario
    resultados = []
    
    if ejecutar_calidad:
        logger.info("Ejecutando tarea de calidad...")
        resultado_calidad = ejecutar_tarea_calidad(dry_run=args.dry_run)
        resultados.append(("Calidad", resultado_calidad))
    
    if ejecutar_tecnica:
        logger.info("Ejecutando tarea técnica...")
        resultado_tecnica = ejecutar_tarea_tecnica(dry_run=args.dry_run)
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


if __name__ == "__main__":
    import sys
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger = setup_logger(__name__)
        logger.error(f"Error crítico en ejecución: {e}")
        sys.exit(1)