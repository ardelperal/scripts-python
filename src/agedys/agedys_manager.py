#!/usr/bin/env python3
"""
Gestor AGEDYS Nuevo - Migración del sistema original a la nueva arquitectura
Adaptación del script original AGEDYS.VBS a Python con herencia de TareaDiaria
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Añadir el directorio src al path para importaciones
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from common.base_task import TareaDiaria
from common import config
from common.database import AccessDatabase
from src.common.utils import (
    generate_html_header, generate_html_footer, format_date, load_css_content,
    get_quality_emails_string, get_technical_emails_string, get_admin_emails_string,
    register_email_in_database
)


class AgedysManager(TareaDiaria):
    """Gestor AGEDYS que hereda de TareaDiaria"""
    
    def __init__(self):
        super().__init__(
            name="AGEDYS",
            script_filename="run_agedys.py",
            task_names=["Tareas"],  # Nombre de la tarea en la BD (como en el script original)
            frequency_days=int(os.getenv('AGEDYS_FRECUENCIA_DIAS', '1'))
        )
        
        # Configurar conexiones específicas de AGEDYS
        self.setup_agedys_connections()
        
        # Cargar CSS
        self.css_content = load_css_content(config.css_file_path)
        
        # ID de aplicación AGEDYS
        self.app_id = 3
    
    def setup_agedys_connections(self):
        """Configura las conexiones específicas de AGEDYS"""
        # Conexión a la base de datos de AGEDYS
        agedys_connection_string = config.get_db_agedys_connection_string()
        self.db_agedys = AccessDatabase(agedys_connection_string)
    
    def get_usuarios_facturas_pendientes_visado_tecnico(self) -> List[Dict[str, Any]]:
        """Obtiene usuarios con facturas pendientes de visado técnico"""
        self.logger.info("Obteniendo usuarios con facturas pendientes de visado técnico...")
        
        usuarios_dict = {}
        
        # Consulta 1: Peticionarios con visado pendiente (AGEDYSGenerico = 'Sí')
        query1 = """
            SELECT DISTINCT TbUsuariosAplicaciones.UsuarioRed, TbUsuariosAplicaciones.CorreoUsuario
            FROM ((TbProyectos INNER JOIN (TbNPedido INNER JOIN (TbFacturasDetalle
            INNER JOIN TbVisadoFacturas_Nueva ON TbFacturasDetalle.IDFactura = TbVisadoFacturas_Nueva.IDFactura)
            ON TbNPedido.NPEDIDO = TbFacturasDetalle.NPEDIDO) ON TbProyectos.CODPROYECTOS = TbNPedido.CODPPD)
            INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente)
            INNER JOIN TbUsuariosAplicaciones ON TbProyectos.PETICIONARIO = TbUsuariosAplicaciones.Nombre
            WHERE TbFacturasDetalle.FechaAceptacion IS NULL
            AND TbVisadoFacturas_Nueva.FRECHAZOTECNICO IS NULL
            AND TbVisadoFacturas_Nueva.FVISADOTECNICO IS NULL
            AND TbExpedientes1.AGEDYSGenerico = 'Sí'
            AND TbExpedientes1.AGEDYSAplica = 'Sí'
        """
        
        try:
            results = self.db_agedys.execute_query(query1)
            for row in results:
                usuario_red = row.get('UsuarioRed', '')
                correo = row.get('CorreoUsuario', '')
                if usuario_red and correo:
                    usuarios_dict[usuario_red] = correo
        except Exception as e:
            self.logger.error(f"Error en consulta 1 de facturas pendientes: {e}")
        
        # Consulta 2: Responsables sin visado (AGEDYSGenerico = 'Sí')
        query2 = """
            SELECT DISTINCT TbUsuariosAplicaciones.UsuarioRed, TbUsuariosAplicaciones.CorreoUsuario
            FROM ((((TbProyectos INNER JOIN (TbNPedido INNER JOIN TbFacturasDetalle
            ON TbNPedido.NPEDIDO = TbFacturasDetalle.NPEDIDO) ON TbProyectos.CODPROYECTOS = TbNPedido.CODPPD)
            INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente)
            LEFT JOIN TbVisadoFacturas_Nueva ON TbFacturasDetalle.IDFactura = TbVisadoFacturas_Nueva.IDFactura)
            INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente)
            INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id
            WHERE TbFacturasDetalle.FechaAceptacion IS NULL
            AND TbVisadoFacturas_Nueva.IDFactura IS NULL
            AND TbExpedientes1.AGEDYSGenerico = 'Sí'
            AND TbExpedientes1.AGEDYSAplica = 'Sí'
            AND TbExpedientesResponsables.CorreoSiempre <> 'No'
        """
        
        try:
            results = self.db_agedys.execute_query(query2)
            for row in results:
                usuario_red = row.get('UsuarioRed', '')
                correo = row.get('CorreoUsuario', '')
                if usuario_red and correo:
                    usuarios_dict[usuario_red] = correo
        except Exception as e:
            self.logger.error(f"Error en consulta 2 de facturas pendientes: {e}")
        
        # Consulta 3: Responsables con visado pendiente (AGEDYSGenerico = 'No')
        query3 = """
            SELECT DISTINCT TbUsuariosAplicaciones.UsuarioRed, TbUsuariosAplicaciones.CorreoUsuario
            FROM (((TbProyectos INNER JOIN (TbNPedido INNER JOIN (TbFacturasDetalle
            INNER JOIN TbVisadoFacturas_Nueva ON TbFacturasDetalle.IDFactura = TbVisadoFacturas_Nueva.IDFactura)
            ON TbNPedido.NPEDIDO = TbFacturasDetalle.NPEDIDO) ON TbProyectos.CODPROYECTOS = TbNPedido.CODPPD)
            INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente)
            INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente)
            INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id
            WHERE TbFacturasDetalle.FechaAceptacion IS NULL
            AND TbVisadoFacturas_Nueva.FRECHAZOTECNICO IS NULL
            AND TbVisadoFacturas_Nueva.FVISADOTECNICO IS NULL
            AND TbExpedientes1.AGEDYSGenerico = 'No'
            AND TbExpedientes1.AGEDYSAplica = 'Sí'
            AND TbExpedientesResponsables.CorreoSiempre <> 'No'
        """
        
        try:
            results = self.db_agedys.execute_query(query3)
            for row in results:
                usuario_red = row.get('UsuarioRed', '')
                correo = row.get('CorreoUsuario', '')
                if usuario_red and correo:
                    usuarios_dict[usuario_red] = correo
        except Exception as e:
            self.logger.error(f"Error en consulta 3 de facturas pendientes: {e}")
        
        # Consulta 4: Responsables sin visado (AGEDYSGenerico = 'No')
        query4 = """
            SELECT DISTINCT TbUsuariosAplicaciones.UsuarioRed, TbUsuariosAplicaciones.CorreoUsuario
            FROM ((((TbProyectos INNER JOIN (TbNPedido INNER JOIN TbFacturasDetalle
            ON TbNPedido.NPEDIDO = TbFacturasDetalle.NPEDIDO) ON TbProyectos.CODPROYECTOS = TbNPedido.CODPPD)
            INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente)
            LEFT JOIN TbVisadoFacturas_Nueva ON TbFacturasDetalle.IDFactura = TbVisadoFacturas_Nueva.IDFactura)
            INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente)
            INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id
            WHERE TbFacturasDetalle.FechaAceptacion IS NULL
            AND TbVisadoFacturas_Nueva.IDFactura IS NULL
            AND TbExpedientes1.AGEDYSGenerico = 'No'
            AND TbExpedientes1.AGEDYSAplica = 'Sí'
            AND TbExpedientesResponsables.CorreoSiempre <> 'No'
        """
        
        try:
            results = self.db_agedys.execute_query(query4)
            for row in results:
                usuario_red = row.get('UsuarioRed', '')
                correo = row.get('CorreoUsuario', '')
                if usuario_red and correo:
                    usuarios_dict[usuario_red] = correo
        except Exception as e:
            self.logger.error(f"Error en consulta 4 de facturas pendientes: {e}")
        
        # Convertir diccionario a lista
        usuarios_list = []
        for usuario_red, correo in usuarios_dict.items():
            usuarios_list.append({
                'UsuarioRed': usuario_red,
                'CorreoUsuario': correo
            })
        
        self.logger.info(f"Usuarios encontrados: {len(usuarios_list)}")
        return usuarios_list
    
    def get_admin_emails(self) -> str:
        """Obtiene los emails de administradores usando el módulo común"""
        try:
            from ..common.user_adapter import get_users_with_fallback
            
            # Usar el módulo común para obtener usuarios administradores
            admin_users = get_users_with_fallback(
                user_type='admin',
                config=self.config,
                logger=self.logger,
                db_connection=self.db_tareas  # Usar la conexión de tareas para usuarios
            )
            
            if admin_users:
                emails = [user.get('CorreoUsuario', '') for user in admin_users if user.get('CorreoUsuario')]
                return ';'.join(emails)
            else:
                # Fallback como en el script original
                return "andres.romandelperal@telefonica.com;Fernando.lazarodiaz@telefonica.com"
                
        except Exception as e:
            self.logger.error(f"Error obteniendo emails de administradores: {e}")
            return "andres.romandelperal@telefonica.com;Fernando.lazarodiaz@telefonica.com"
    
    def run(self) -> bool:
        """Ejecuta la lógica principal de AGEDYS"""
        try:
            if not self.debe_ejecutarse():
                self.logger.info("La tarea AGEDYS no debe ejecutarse hoy según la lógica de negocio")
                return True
            
            self.logger.info("Iniciando ejecución de AGEDYS...")
            
            # Obtener usuarios con facturas pendientes
            usuarios = self.get_usuarios_facturas_pendientes_visado_tecnico()
            
            if not usuarios:
                self.logger.info("No hay usuarios con facturas pendientes de visado técnico")
                self.marcar_como_completada()
                return True
            
            # Obtener emails de administradores
            admin_emails = self.get_admin_emails()
            
            # Generar y enviar correos (simplificado para la migración inicial)
            subject = "TAREAS PENDIENTES (AGEDYS)"
            body = self._generate_email_body(usuarios)
            
            # Registrar el correo en la base de datos
            register_email_in_database(
                self.db_tareas,
                "Tareas",
                subject,
                body,
                "",  # Sin destinatarios específicos por ahora
                admin_emails
            )
            
            self.logger.info("AGEDYS ejecutado exitosamente")
            self.marcar_como_completada()
            return True
            
        except Exception as e:
            self.logger.error(f"Error ejecutando AGEDYS: {e}")
            return False
    
    def _generate_email_body(self, usuarios: List[Dict[str, Any]]) -> str:
        """Genera el cuerpo del correo HTML"""
        html_parts = []
        
        # Cabecera HTML
        html_parts.append(generate_html_header("TAREAS PENDIENTES (AGEDYS)", self.css_content))
        
        # Contenido
        html_parts.append("<h2>Usuarios con facturas pendientes de visado técnico</h2>")
        html_parts.append("<table>")
        html_parts.append("<tr><th>Usuario</th><th>Email</th></tr>")
        
        for usuario in usuarios:
            html_parts.append(f"<tr><td>{usuario['UsuarioRed']}</td><td>{usuario['CorreoUsuario']}</td></tr>")
        
        html_parts.append("</table>")
        
        # Pie HTML
        html_parts.append(generate_html_footer())
        
        return "".join(html_parts)
    
    def close_connections(self):
        """Cierra las conexiones a las bases de datos"""
        try:
            if hasattr(self, 'db_agedys') and self.db_agedys:
                self.db_agedys.disconnect()
        except Exception as e:
            self.logger.warning(f"Error cerrando conexión AGEDYS: {e}")
        
        try:
            if hasattr(self, 'db_brass') and self.db_brass:
                self.db_brass.disconnect()
        except Exception as e:
            self.logger.warning(f"Error cerrando conexión BRASS: {e}")
        
        try:
            if hasattr(self, 'db_expedientes') and self.db_expedientes:
                self.db_expedientes.disconnect()
        except Exception as e:
            self.logger.warning(f"Error cerrando conexión Expedientes: {e}")
        
        # Llamar al método padre
        super().close_connections()