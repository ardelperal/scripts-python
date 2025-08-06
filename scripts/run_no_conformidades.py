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
    get_technical_emails_string, register_task_completion, register_email_in_database
)
from src.no_conformidades.no_conformidades_manager import NoConformidadesManager
from src.no_conformidades.report_registrar import ReportRegistrar
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
    """Ejecuta la tarea de calidad generando un informe consolidado."""
    logger = setup_logger(__name__)
    logger.info("=== INICIANDO TAREA DE CALIDAD ===")
    if dry_run:
        logger.info("MODO DRY-RUN: No se enviarán emails reales")

    email_manager = ReportRegistrar()

    try:
        with NoConformidadesManager() as nc_manager:
            logger.info("Obteniendo datos para el reporte de calidad...")
            # 1. ARs próximas a vencer (calidad)
            ars_proximas_vencer = nc_manager.get_ars_proximas_vencer_calidad()
            # 2. NCs resueltas pendientes de control de eficacia
            ncs_pendientes_eficacia = nc_manager.get_ncs_pendientes_eficacia()
            # 3. NCs registradas sin acciones correctivas
            ncs_sin_acciones = nc_manager.get_ncs_sin_acciones()
            # 4. ARs para replanificar
            ars_para_replanificar = nc_manager.get_ars_para_replanificar()

            logger.info(f"ARs próximas a vencer (calidad): {len(ars_proximas_vencer)}")
            logger.info(f"NCs pendientes de eficacia: {len(ncs_pendientes_eficacia)}")
            logger.info(f"NCs sin acciones: {len(ncs_sin_acciones)}")
            logger.info(f"ARs para replanificar: {len(ars_para_replanificar)}")

            if ars_proximas_vencer or ncs_pendientes_eficacia or ncs_sin_acciones or ars_para_replanificar:
                correos_calidad = get_quality_emails_string(app_id="8", config=nc_manager.config, logger=logger, db_connection=nc_manager.db_tareas)

                if correos_calidad:
                    logger.info("Generando reporte de calidad...")
                    asunto = "Informe Tareas No Conformidades (No Conformidades)"
                    cuerpo = email_manager._generar_reporte_calidad_html(
                        ncs_eficacia=ncs_pendientes_eficacia,
                        ncs_caducar=ars_proximas_vencer,
                        ncs_sin_acciones=ncs_sin_acciones,
                        destinatarios_calidad=correos_calidad,
                        destinatarios_admin=""
                    )

                    if dry_run:
                        logger.info(f"DRY-RUN: Se enviaría reporte a {correos_calidad}")
                        resultado = True
                    else:
                        # Para el reporte de calidad NO se envían técnicos en BCC
                        resultado = register_email_in_database(
                            db_connection=nc_manager.db_tareas,
                            application="NoConformidades",
                            subject=asunto,
                            body=cuerpo,
                            recipients=correos_calidad,
                            admin_emails=""  # Sin BCC para el reporte de calidad
                        )
                    
                    if resultado:
                        logger.info("Reporte de calidad registrado correctamente.")
                    else:
                        logger.error("Error al registrar el reporte de calidad.")
                else:
                    logger.warning("No se encontraron destinatarios de calidad. No se enviará el reporte.")
            else:
                logger.info("No hay datos para generar el reporte de calidad.")

            if not dry_run:
                register_task_completion(nc_manager.db_tareas, "NoConformidadesCalidad")
            else:
                logger.info("DRY-RUN: Se habría registrado la ejecución de la tarea.")

        logger.info("=== TAREA DE CALIDAD COMPLETADA ===")
        return True
        
    except Exception as e:
        logger.error(f"Error ejecutando tarea de calidad: {e}")
        return False


def ejecutar_tarea_tecnica(dry_run=False):
    """Ejecuta la tarea técnica enviando notificaciones individuales por técnico."""
    logger = setup_logger(__name__)
    logger.info("=== INICIANDO TAREA TÉCNICA ===")
    if dry_run:
        logger.info("MODO DRY-RUN: No se enviarán emails reales")

    email_manager = ReportRegistrar()
    exitosos = 0
    total_notificaciones = 0

    try:
        with NoConformidadesManager() as nc_manager:
            tecnicos = nc_manager.get_tecnicos_con_nc_activas()
            if not tecnicos:
                logger.info("No hay técnicos con NC activas para notificar.")
                if not dry_run:
                    register_task_completion(nc_manager.db_tareas, "NoConformidadesTecnica")
                return True

            for tecnico in tecnicos:
                # Obtener ARs para este técnico
                ars_por_vencer_8_15 = nc_manager.get_ars_tecnico_por_vencer(tecnico, 8, 15, "IDCorreo15")
                ars_por_vencer_1_7 = nc_manager.get_ars_tecnico_por_vencer(tecnico, 1, 7, "IDCorreo7")
                ars_vencidas = nc_manager.get_ars_tecnico_vencidas(tecnico, "IDCorreo0")

                if not ars_por_vencer_8_15 and not ars_por_vencer_1_7 and not ars_vencidas:
                    logger.info(f"El técnico {tecnico} no tiene ARs para notificar.")
                    continue

                # Obtener correos de responsables de calidad específicos
                # Solo para consultas 2.1.b (1-7 días) y 2.1.c (vencidas)
                correos_calidad_cc = set()
                
                # Obtener correos de calidad para ARs de 1-7 días
                for ar in ars_por_vencer_1_7:
                    if 'CodigoNoConformidad' in ar:
                        correo_calidad = nc_manager.get_correo_calidad_por_nc(ar['CodigoNoConformidad'])
                        if correo_calidad:
                            correos_calidad_cc.add(correo_calidad)
                
                # Obtener correos de calidad para ARs vencidas
                for ar in ars_vencidas:
                    if 'CodigoNoConformidad' in ar:
                        correo_calidad = nc_manager.get_correo_calidad_por_nc(ar['CodigoNoConformidad'])
                        if correo_calidad:
                            correos_calidad_cc.add(correo_calidad)

                # Convertir set a string separado por comas
                correos_cc = "; ".join(sorted(correos_calidad_cc)) if correos_calidad_cc else ""

                # Obtener el correo electrónico del técnico
                from src.common.utils import get_user_email
                correo_tecnico = get_user_email(tecnico, nc_manager.config, logger)
                
                if not correo_tecnico:
                    logger.error(f"ERROR: No se pudo obtener el correo del técnico {tecnico}. No se registrará la notificación.")
                    total_notificaciones += 1
                    continue

                total_notificaciones += 1
                logger.info(f"Generando notificación para {tecnico} ({correo_tecnico})...")
                if correos_cc:
                    logger.info(f"  - Con copia a responsables de calidad: {correos_cc}")
                
                asunto = "Tareas de Acciones Correctivas a punto de caducar o caducadas (No Conformidades)"
                cuerpo = email_manager.generate_technical_report_html(
                    ars_proximas_vencer_8_15=ars_por_vencer_8_15,
                    ars_proximas_vencer_1_7=ars_por_vencer_1_7,
                    ars_vencidas=ars_vencidas
                )

                if dry_run:
                    logger.info(f"DRY-RUN: Se enviaría notificación a {correo_tecnico}")
                    if correos_cc:
                        logger.info(f"DRY-RUN: Con copia a: {correos_cc}")
                    resultado = True
                else:
                    resultado = register_email_in_database(
                        db_connection=nc_manager.db_tareas,
                        application="NoConformidades",
                        subject=asunto,
                        body=cuerpo,
                        recipients=correo_tecnico,
                        admin_emails=correos_cc
                    )

                if resultado:
                    exitosos += 1
                    logger.info(f"Notificación para {tecnico} registrada correctamente.")
                    # Registrar avisos para las ARs notificadas
                    for ar in ars_por_vencer_8_15:
                        nc_manager.registrar_aviso_ar(ar['IDAccionRealizada'], 1, "IDCorreo15")
                    for ar in ars_por_vencer_1_7:
                        nc_manager.registrar_aviso_ar(ar['IDAccionRealizada'], 1, "IDCorreo7")
                    for ar in ars_vencidas:
                        nc_manager.registrar_aviso_ar(ar['IDAccionRealizada'], 1, "IDCorreo0")
                else:
                    logger.error(f"Error al registrar la notificación para {tecnico}.")

            logger.info(f"Notificaciones técnicas procesadas: {exitosos}/{total_notificaciones}")

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