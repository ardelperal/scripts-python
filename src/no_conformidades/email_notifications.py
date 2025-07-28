"""
Módulo de notificaciones por email para No Conformidades
Maneja el envío de notificaciones y reportes por correo electrónico
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime

from ..common.email_sender import EmailSender
from ..common.logger import setup_logger
from .no_conformidades_manager import NoConformidad, ARAPC, Usuario
from .html_report_generator import HTMLReportGenerator


class EmailNotificationManager:
    """Gestor de notificaciones por email para No Conformidades"""
    
    def __init__(self):
        self.email_sender = EmailSender()
        self.html_generator = HTMLReportGenerator()
        self.logger = setup_logger(__name__)
    
    def enviar_notificacion_calidad(self, 
                                  ncs_eficacia: List[NoConformidad],
                                  ncs_caducar: List[NoConformidad],
                                  ncs_sin_acciones: List[NoConformidad],
                                  destinatarios_calidad: str,
                                  destinatarios_admin: str) -> bool:
        """Envía notificación de calidad con el reporte de NCs"""
        try:
            # Generar el reporte HTML
            html_content = self.html_generator.generar_reporte_completo(
                ncs_eficacia=ncs_eficacia,
                arapcs=[],  # No incluir ARAPs en reporte de calidad
                ncs_caducar=ncs_caducar,
                ncs_sin_acciones=ncs_sin_acciones,
                titulo="Reporte de Calidad - No Conformidades"
            )
            
            # Preparar el asunto
            fecha_actual = datetime.now().strftime("%d/%m/%Y")
            total_items = len(ncs_eficacia) + len(ncs_caducar) + len(ncs_sin_acciones)
            
            asunto = f"Reporte Calidad NC - {fecha_actual} ({total_items} elementos)"
            
            # Preparar destinatarios
            destinatarios = []
            if destinatarios_calidad:
                destinatarios.extend(destinatarios_calidad.split(';'))
            if destinatarios_admin:
                destinatarios.extend(destinatarios_admin.split(';'))
            
            # Limpiar destinatarios vacíos
            destinatarios = [d.strip() for d in destinatarios if d.strip()]
            
            if not destinatarios:
                self.logger.warning("No hay destinatarios para el reporte de calidad")
                return False
            
            # Enviar el email
            resultado = self.email_sender.send_email(
                to_addresses=destinatarios,
                subject=asunto,
                body=html_content,
                is_html=True
            )
            
            if resultado:
                self.logger.info(f"Reporte de calidad enviado a {len(destinatarios)} destinatarios")
                return True
            else:
                self.logger.error("Error enviando reporte de calidad")
                return False
                
        except Exception as e:
            self.logger.error(f"Error enviando notificación de calidad: {e}")
            return False
    
    def enviar_notificacion_tecnica(self, 
                                  arapcs: List[ARAPC],
                                  destinatarios_tecnicos: str,
                                  destinatarios_admin: str) -> bool:
        """Envía notificación técnica con ARAPs próximas a vencer"""
        try:
            # Generar el reporte HTML solo con ARAPs
            html_content = self.html_generator.generar_reporte_completo(
                ncs_eficacia=[],
                arapcs=arapcs,
                ncs_caducar=[],
                ncs_sin_acciones=[],
                titulo="Reporte Técnico - Acciones Correctivas/Preventivas"
            )
            
            # Preparar el asunto
            fecha_actual = datetime.now().strftime("%d/%m/%Y")
            total_arapcs = len(arapcs)
            arapcs_vencidas = sum(1 for arapc in arapcs 
                                if arapc.fecha_fin_prevista and 
                                (arapc.fecha_fin_prevista - datetime.now()).days < 0)
            
            if arapcs_vencidas > 0:
                asunto = f"🔴 URGENTE - ARAPs Vencidas - {fecha_actual} ({arapcs_vencidas}/{total_arapcs})"
            else:
                asunto = f"Reporte Técnico ARAPs - {fecha_actual} ({total_arapcs} elementos)"
            
            # Preparar destinatarios
            destinatarios = []
            if destinatarios_tecnicos:
                destinatarios.extend(destinatarios_tecnicos.split(';'))
            if destinatarios_admin:
                destinatarios.extend(destinatarios_admin.split(';'))
            
            # Limpiar destinatarios vacíos
            destinatarios = [d.strip() for d in destinatarios if d.strip()]
            
            if not destinatarios:
                self.logger.warning("No hay destinatarios para el reporte técnico")
                return False
            
            # Enviar el email
            resultado = self.email_sender.send_email(
                to_addresses=destinatarios,
                subject=asunto,
                body=html_content,
                is_html=True
            )
            
            if resultado:
                self.logger.info(f"Reporte técnico enviado a {len(destinatarios)} destinatarios")
                return True
            else:
                self.logger.error("Error enviando reporte técnico")
                return False
                
        except Exception as e:
            self.logger.error(f"Error enviando notificación técnica: {e}")
            return False
    
    def enviar_notificacion_individual_arapc(self, 
                                           arapc: ARAPC, 
                                           usuario_responsable: Usuario) -> bool:
        """Envía notificación individual a responsable de ARAPC"""
        try:
            if not usuario_responsable.correo:
                self.logger.warning(f"Usuario {usuario_responsable.nombre} no tiene correo configurado")
                return False
            
            # Calcular días restantes
            dias_restantes = (arapc.fecha_fin_prevista - datetime.now()).days if arapc.fecha_fin_prevista else 0
            
            # Preparar el contenido del email
            if dias_restantes < 0:
                estado = f"VENCIDA hace {abs(dias_restantes)} días"
                urgencia = "🔴 URGENTE - "
            elif dias_restantes <= 3:
                estado = f"vence en {dias_restantes} días"
                urgencia = "⚠️ IMPORTANTE - "
            else:
                estado = f"vence en {dias_restantes} días"
                urgencia = ""
            
            asunto = f"{urgencia}Acción Correctiva/Preventiva {estado} - NC {arapc.codigo_nc}"
            
            fecha_fin = arapc.fecha_fin_prevista.strftime("%d/%m/%Y") if arapc.fecha_fin_prevista else "No definida"
            
            body = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; }}
                    .header {{ background-color: #4472C4; color: white; padding: 15px; text-align: center; }}
                    .content {{ padding: 20px; }}
                    .alert {{ background-color: #FFE6E6; border-left: 4px solid #FF0000; padding: 15px; margin: 15px 0; }}
                    .warning {{ background-color: #FFF3CD; border-left: 4px solid #FFC107; padding: 15px; margin: 15px 0; }}
                    .info {{ background-color: #D1ECF1; border-left: 4px solid #17A2B8; padding: 15px; margin: 15px 0; }}
                    .details {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h2>Notificación de Acción Correctiva/Preventiva</h2>
                </div>
                <div class="content">
                    <p>Estimado/a {usuario_responsable.nombre},</p>
                    
                    {'<div class="alert">' if dias_restantes < 0 else '<div class="warning">' if dias_restantes <= 3 else '<div class="info">'}
                        <strong>Su acción correctiva/preventiva {estado.upper()}</strong>
                    </div>
                    
                    <div class="details">
                        <h3>Detalles de la Acción:</h3>
                        <p><strong>ID Acción:</strong> {arapc.id_accion}</p>
                        <p><strong>No Conformidad:</strong> {arapc.codigo_nc}</p>
                        <p><strong>Descripción:</strong> {arapc.descripcion}</p>
                        <p><strong>Fecha Fin Prevista:</strong> {fecha_fin}</p>
                        <p><strong>Estado:</strong> {estado}</p>
                    </div>
                    
                    <p>Por favor, tome las acciones necesarias para completar esta tarea.</p>
                    
                    <p>Saludos cordiales,<br>
                    Sistema de Gestión de No Conformidades</p>
                </div>
            </body>
            </html>
            """
            
            # Enviar el email
            resultado = self.email_sender.send_email(
                to_addresses=[usuario_responsable.correo],
                subject=asunto,
                body=body,
                is_html=True
            )
            
            if resultado:
                self.logger.info(f"Notificación individual enviada a {usuario_responsable.correo} para ARAPC {arapc.id_accion}")
                return True
            else:
                self.logger.error(f"Error enviando notificación individual a {usuario_responsable.correo}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error enviando notificación individual ARAPC: {e}")
            return False
    
    def enviar_notificaciones_individuales_arapcs(self, 
                                                arapcs: List[ARAPC],
                                                usuarios_tecnicos: List[Usuario]) -> Dict[str, bool]:
        """Envía notificaciones individuales a todos los responsables de ARAPs"""
        resultados = {}
        
        # Crear diccionario de usuarios por nombre/código
        usuarios_dict = {usuario.usuario_red.lower(): usuario for usuario in usuarios_tecnicos}
        usuarios_dict.update({usuario.nombre.lower(): usuario for usuario in usuarios_tecnicos})
        
        for arapc in arapcs:
            if not arapc.responsable:
                continue
            
            # Buscar el usuario responsable
            responsable_key = arapc.responsable.lower()
            usuario_responsable = usuarios_dict.get(responsable_key)
            
            if not usuario_responsable:
                self.logger.warning(f"No se encontró usuario para responsable: {arapc.responsable}")
                resultados[f"ARAPC_{arapc.id_accion}"] = False
                continue
            
            # Enviar notificación individual
            resultado = self.enviar_notificacion_individual_arapc(arapc, usuario_responsable)
            resultados[f"ARAPC_{arapc.id_accion}"] = resultado
        
        # Log resumen
        exitosos = sum(1 for r in resultados.values() if r)
        total = len(resultados)
        self.logger.info(f"Notificaciones individuales ARAPs: {exitosos}/{total} enviadas correctamente")
        
        return resultados
    
    def marcar_email_como_enviado(self, tipo_email: str, fecha: datetime = None) -> bool:
        """Marca un email como enviado en el sistema de control"""
        try:
            if fecha is None:
                fecha = datetime.now()
            
            # Aquí se podría implementar un sistema de control de emails enviados
            # Por ahora solo registramos en el log
            self.logger.info(f"Email marcado como enviado: {tipo_email} - {fecha}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error marcando email como enviado: {e}")
            return False