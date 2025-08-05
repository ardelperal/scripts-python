"""
Script principal para ejecutar las tareas de No Conformidades
Equivalente al NoConformidades.vbs original

Uso:
    python run_no_conformidades.py                    # Ejecución normal (verifica horarios)
    python run_no_conformidades.py --force-calidad    # Fuerza ejecución de tarea de calidad
    python run_no_conformidades.py --force-tecnica    # Fuerza ejecución de tarea técnica
    python run_no_conformidades.py --force-calidad --force-tecnica  # Fuerza ambas tareas
    python run_no_conformidades.py --force-all        # Fuerza ejecución de todas las tareas
    python run_no_conformidades.py --dry-run          # Simula ejecución sin enviar emails
"""

import sys
import os
import argparse
from datetime import datetime
from pathlib import Path

# Agregar el directorio raíz del proyecto al path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.common.logger import setup_logger
from src.common.utils import (
    should_execute_task, should_execute_quality_task, get_admin_emails_string, get_quality_emails_string, 
    register_task_completion, register_email_in_database
)
from src.no_conformidades.no_conformidades_manager import NoConformidadesManager
from src.no_conformidades.email_notifications import EmailNotificationManager
from src.common.user_adapter import get_users_with_fallback


def parse_arguments():
    """Parsea los argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(
        description="Script para ejecutar tareas de No Conformidades",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  %(prog)s                                    # Ejecución normal (verifica horarios)
  %(prog)s --force-calidad                    # Fuerza ejecución de tarea de calidad
  %(prog)s --force-tecnica                    # Fuerza ejecución de tarea técnica  
  %(prog)s --force-calidad --force-tecnica    # Fuerza ejecución de ambas tareas
  %(prog)s --force-all                        # Fuerza ejecución de todas las tareas
  %(prog)s --dry-run                          # Simula ejecución sin enviar emails
        """
    )
    
    # Opciones de forzado (ahora pueden combinarse)
    parser.add_argument(
        '--force-calidad', 
        action='store_true',
        help='Fuerza la ejecución de la tarea de calidad independientemente del horario'
    )
    parser.add_argument(
        '--force-tecnica', 
        action='store_true',
        help='Fuerza la ejecución de la tarea técnica independientemente del horario'
    )
    parser.add_argument(
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
            
            ncs_eficacia = nc_manager.get_nc_pendientes_eficacia()
            ncs_caducar = nc_manager.get_nc_proximas_caducar()
            ncs_sin_acciones = nc_manager.get_nc_registradas_sin_acciones()
            
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
                correos_calidad = get_quality_emails_string("1", nc_manager.config, logger)  # App ID 1 para NC
                correos_admin = get_admin_emails_string(nc_manager.db_tareas)  # Solo necesita db_connection
                
                logger.info(f"Destinatarios calidad: {correos_calidad}")
                logger.info(f"Destinatarios admin: {correos_admin}")
                
                # Registrar reporte de calidad en base de datos
                if correos_calidad or correos_admin:
                    # Generar el contenido del email
                    asunto = f"Reporte de No Conformidades - Calidad ({total_items} pendientes)"
                    cuerpo = email_manager._generar_reporte_calidad_html(
                        ncs_eficacia=ncs_eficacia,
                        ncs_caducar=ncs_caducar,
                        ncs_sin_acciones=ncs_sin_acciones,
                        destinatarios_calidad=correos_calidad,
                        destinatarios_admin=correos_admin
                    )
                    
                    destinatarios = correos_calidad if correos_calidad else ""
                    admin_emails = correos_admin if correos_admin else ""
                    
                    if dry_run:
                        logger.info("DRY-RUN: Se habría registrado reporte de calidad en base de datos")
                        resultado_email = True
                    else:
                        resultado_email = register_email_in_database(
                            db_connection=nc_manager.db_tareas,
                            application="NoConformidades",
                            subject=asunto,
                            body=cuerpo,
                            recipients=destinatarios,
                            admin_emails=admin_emails
                        )
                    
                    if resultado_email:
                        logger.info("Reporte de calidad registrado correctamente en base de datos")
                    else:
                        logger.error("Error registrando reporte de calidad en base de datos")
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
    """Ejecuta la tarea técnica (equivalente a RealizarTareaTecnicos)"""
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
            
            arapcs = nc_manager.get_arapcs_proximas_vencer()
            
            # Log de resultados
            logger.info(f"ARAPs próximas a vencer: {len(arapcs)}")
            
            if len(arapcs) == 0:
                logger.info("No hay ARAPs próximas a vencer")
            else:
                # Obtener destinatarios usando función común
                correos_admin = get_admin_emails_string(nc_manager.db_tareas)  # Solo necesita db_connection
                
                logger.info(f"Destinatarios admin: {correos_admin}")
                
                # Registrar reporte técnico general en base de datos
                if correos_admin:
                    # Generar el contenido del email
                    asunto = f"Reporte Técnico - ARAPs próximas a vencer ({len(arapcs)} elementos)"
                    cuerpo = email_manager._generar_reporte_tecnico_html(
                        arapcs=arapcs,
                        destinatarios_tecnicos="",
                        destinatarios_admin=correos_admin
                    )
                    
                    if dry_run:
                        logger.info("DRY-RUN: Se habría registrado reporte técnico general en base de datos")
                        resultado_email = True
                    else:
                        resultado_email = register_email_in_database(
                            db_connection=nc_manager.db_tareas,
                            application="NoConformidades",
                            subject=asunto,
                            body=cuerpo,
                            recipients="",
                            admin_emails=correos_admin
                        )
                    
                    if resultado_email:
                        logger.info("Reporte técnico general registrado correctamente en base de datos")
                    else:
                        logger.error("Error registrando reporte técnico general en base de datos")
                
                # Registrar notificaciones individuales en base de datos
                logger.info("Registrando notificaciones individuales en base de datos...")
                
                # Obtener usuarios técnicos usando función común
                usuarios_tecnicos = get_users_with_fallback(
                    user_type='technical',
                    app_id="1",  # App ID 1 para NC
                    config=nc_manager.config,
                    logger=logger
                )
                
                exitosos = 0
                total = 0
                
                # Registrar una notificación individual por cada ARAP
                for arap in arapcs:
                    # Buscar el responsable de esta ARAP
                    responsable_email = None
                    for usuario in usuarios_tecnicos:
                        if usuario.get('UsuarioRed') == arap.get('Responsable'):
                            responsable_email = usuario.get('CorreoUsuario')
                            break
                    
                    if responsable_email:
                        asunto = f"ARAP próxima a vencer - {arap.get('NumeroNC', 'N/A')}"
                        cuerpo = email_manager._generar_notificacion_individual_html(arap, responsable_email)
                        
                        if dry_run:
                            logger.info(f"DRY-RUN: Se habría registrado notificación individual para {responsable_email}")
                            resultado = True
                        else:
                            resultado = register_email_in_database(
                                db_connection=nc_manager.db_tareas,
                                application="NoConformidades",
                                subject=asunto,
                                body=cuerpo,
                                recipients=responsable_email,
                                admin_emails=""
                            )
                        
                        if resultado:
                            exitosos += 1
                        total += 1
                    else:
                        logger.warning(f"No se encontró email para responsable: {arap.get('Responsable', 'N/A')}")
                        total += 1
                
                logger.info(f"Notificaciones individuales registradas: {exitosos}/{total}")
            
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
    else:
        # Verificar opciones individuales de forzado
        if args.force_calidad:
            logger.info("FORZANDO EJECUCIÓN DE TAREA DE CALIDAD")
            ejecutar_calidad = True
        
        if args.force_tecnica:
            logger.info("FORZANDO EJECUCIÓN DE TAREA TÉCNICA")
            ejecutar_tecnica = True
        
        # Si no se forzó ninguna tarea, verificar horarios normales
        if not args.force_calidad and not args.force_tecnica:
            logger.info("Verificando horarios para ejecución normal...")
            
            try:
                # Usar context manager para verificar qué tareas se requieren
                with NoConformidadesManager() as nc_manager:
                    # Verificar si se requiere ejecutar tarea de calidad usando lógica de días laborables
                    # Tareas de calidad: semanales, preferentemente los lunes (configurables via .env)
                    dia_preferido_calidad = int(os.getenv('NC_CALIDAD_DIA_PREFERIDO', '0'))  # 0 = lunes
                    archivo_festivos = os.getenv('MASTER_FESTIVOS_FILE', 'herramientas/Festivos.txt')
                    ejecutar_calidad = should_execute_quality_task(
                        nc_manager.db_tareas, 
                        "NoConformidadesCalidad", 
                        dia_preferido_calidad, 
                        archivo_festivos, 
                        logger
                    )
                    logger.info(f"Requiere tarea de calidad (día preferido: {['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo'][dia_preferido_calidad]}): {ejecutar_calidad}")
                    
                    # Verificar si se requiere ejecutar tarea técnica usando función común
                    # Tareas técnicas: diarias (configurables via .env)
                    frecuencia_tecnica = int(os.getenv('NC_FRECUENCIA_TECNICA_DIAS', '1'))
                    ejecutar_tecnica = should_execute_task(nc_manager.db_tareas, "NoConformidadesTecnica", frecuencia_tecnica, logger)
                    logger.info(f"Requiere tarea técnica (cada {frecuencia_tecnica} días): {ejecutar_tecnica}")
                    
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