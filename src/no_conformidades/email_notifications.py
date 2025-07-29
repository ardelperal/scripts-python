"""
Módulo de notificaciones por email para No Conformidades
Maneja el envío de notificaciones y reportes por correo electrónico
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime

from ..common.base_email_manager import BaseEmailNotificationManager
from .no_conformidades_manager import NoConformidad, ARAPC, Usuario


class EmailNotificationManager(BaseEmailNotificationManager):
    """Gestor de notificaciones por email para No Conformidades"""
    
    def __init__(self):
        super().__init__("No Conformidades")
    
    def enviar_notificacion_calidad(self, 
                                  ncs_eficacia: List[NoConformidad],
                                  ncs_caducar: List[NoConformidad],
                                  ncs_sin_acciones: List[NoConformidad],
                                  destinatarios_calidad: str,
                                  destinatarios_admin: str) -> bool:
        """Envía notificación de calidad con el reporte de NCs"""
        try:
            # Generar el reporte HTML usando la funcionalidad común
            html_content = self.generate_module_report(
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
            
            # Usar la funcionalidad común para enviar el reporte
            return self.send_html_report(
                to_addresses=destinatarios,
                subject=asunto,
                html_content=html_content
            )
                
        except Exception as e:
            self.logger.error(f"Error enviando notificación de calidad: {e}")
            return False
    
    def enviar_notificacion_tecnica(self, 
                                  arapcs: List[ARAPC],
                                  destinatarios_tecnicos: str,
                                  destinatarios_admin: str) -> bool:
        """Envía notificación técnica con ARAPs próximas a vencer"""
        try:
            # Generar el reporte HTML usando la funcionalidad común
            html_content = self.generate_module_report(
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
            
            # Usar la funcionalidad común para enviar el reporte
            return self.send_html_report(
                to_addresses=destinatarios,
                subject=asunto,
                html_content=html_content
            )
                
        except Exception as e:
            self.logger.error(f"Error enviando notificación técnica: {e}")
            return False
    
    def enviar_notificacion_individual_arapc(self, 
                                           arapc: ARAPC, 
                                           usuario_responsable: Usuario) -> bool:
        """Envía notificación individual a responsable de ARAPC usando funciones comunes"""
        try:
            if not usuario_responsable.correo:
                self.logger.warning(f"Usuario {usuario_responsable.nombre} no tiene correo configurado")
                return False
            
            # Calcular días restantes
            dias_restantes = (arapc.fecha_fin_prevista - datetime.now()).days if arapc.fecha_fin_prevista else 0
            
            # Preparar el contenido del email usando funciones comunes
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
            
            # Usar el generador HTML común para crear el contenido
            html_content = self.html_generator.generar_header_html("Notificación de Acción Correctiva/Preventiva")
            
            # Agregar contenido específico
            tipo_alerta = "alert" if dias_restantes < 0 else "warning" if dias_restantes <= 3 else "info"
            html_content += f"""
                <div class="content">
                    <p>Estimado/a {usuario_responsable.nombre},</p>
                    
                    <div class="{tipo_alerta}">
                        <strong>Su acción correctiva/preventiva {estado.upper()}</strong>
                    </div>
                    
                    <div class="section-title">Detalles de la Acción</div>
                    <table class="table">
                        <tr><td><strong>ID Acción:</strong></td><td>{arapc.id_accion}</td></tr>
                        <tr><td><strong>No Conformidad:</strong></td><td>{arapc.codigo_nc}</td></tr>
                        <tr><td><strong>Descripción:</strong></td><td>{arapc.descripcion}</td></tr>
                        <tr><td><strong>Fecha Fin Prevista:</strong></td><td>{fecha_fin}</td></tr>
                        <tr><td><strong>Estado:</strong></td><td>{estado}</td></tr>
                    </table>
                    
                    <p>Por favor, tome las acciones necesarias para completar esta tarea.</p>
                    
                    <p>Saludos cordiales,<br>
                    Sistema de Gestión de No Conformidades</p>
                </div>
            """
            
            html_content += self.html_generator.generar_footer_html()
            
            # Usar la funcionalidad común para enviar el email
            return self.send_html_report(
                to_addresses=[usuario_responsable.correo],
                subject=asunto,
                html_content=html_content
            )
                
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
    
    # Implementación de métodos abstractos de la clase base
    def get_admin_emails(self) -> List[str]:
        """Obtiene la lista de emails de administradores para No Conformidades"""
        try:
            from ..common.utils import get_admin_users
            from .no_conformidades_manager import NoConformidadesManager
            
            # Crear instancia temporal del manager para obtener conexión a BD
            manager = NoConformidadesManager()
            manager.conectar_bases_datos()
            
            try:
                # Usar la funcionalidad común para obtener usuarios administradores
                admin_users = get_admin_users(manager.db_tareas)
                emails = [user['CorreoUsuario'] for user in admin_users if user.get('CorreoUsuario')]
                
                self.logger.info(f"Obtenidos {len(emails)} emails de administradores")
                return emails
                
            finally:
                manager.desconectar_bases_datos()
                
        except Exception as e:
            self.logger.error(f"Error obteniendo emails de administradores: {e}")
            return []

    def generate_module_report(self, **kwargs) -> str:
        """Genera un reporte HTML específico para No Conformidades usando funciones comunes"""
        try:
            # Extraer datos de los argumentos
            ncs_eficacia = kwargs.get('ncs_eficacia', [])
            arapcs = kwargs.get('arapcs', [])
            ncs_caducar = kwargs.get('ncs_caducar', [])
            ncs_sin_acciones = kwargs.get('ncs_sin_acciones', [])
            titulo = kwargs.get('titulo', 'Reporte de No Conformidades')
            
            # Usar el generador HTML común para crear el reporte completo
            return self.html_generator.generar_reporte_completo(
                ncs_eficacia=ncs_eficacia,
                arapcs=arapcs,
                ncs_caducar=ncs_caducar,
                ncs_sin_acciones=ncs_sin_acciones,
                titulo=titulo
            )
            
        except Exception as e:
            self.logger.error(f"Error generando reporte del módulo: {e}")
            return f"<html><body><h1>Error generando reporte</h1><p>{e}</p></body></html>"