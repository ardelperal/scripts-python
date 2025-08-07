"""
Módulo BRASS - Gestión de equipos de medida y calibraciones
Nueva versión usando la arquitectura de tareas base
"""
import logging
import os
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from pathlib import Path

# Agregar el directorio src al path para imports
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)
if src_dir not in os.path.sys.path:
    os.sys.path.insert(0, src_dir)

from common.base_task import TareaDiaria
from common.config import config
from common.database import AccessDatabase
from common.utils import (
    load_css_content,
    generate_html_header,
    generate_html_footer,
    safe_str,
    register_email_in_database
)
from common.user_adapter import get_users_with_fallback

logger = logging.getLogger(__name__)


class BrassManager(TareaDiaria):
    """Gestor BRASS usando la nueva arquitectura de tareas"""
    
    def __init__(self):
        # Inicializar la clase base con el nombre de la tarea y frecuencia
        super().__init__(
            name="BRASS",
            script_filename="run_brass.py",
            task_names=["BRASSDiario"],  # Nombre de la tarea en la BD (como en el script original)
            frequency_days=int(os.getenv('BRASS_FRECUENCIA_DIAS', '1'))
        )
        
        # Conexión específica a la base de datos BRASS
        self.db_brass = None
        
        # Cache para usuarios administradores
        self._admin_users = None
        self._admin_emails = None
        
        # Cargar contenido CSS
        self.css_content = load_css_content(config.css_file_path)
    
    def _get_brass_connection(self):
        """Obtiene la conexión a la base de datos BRASS"""
        if self.db_brass is None:
            self.db_brass = AccessDatabase(config.get_db_brass_connection_string())
        return self.db_brass
    
    def close_connections(self):
        """Cierra todas las conexiones"""
        super().close_connections()
        if self.db_brass is not None:
            try:
                self.db_brass.disconnect()
                self.db_brass = None
            except Exception as e:
                self.logger.warning(f"Error cerrando conexión BRASS: {e}")
    
    def get_equipment_out_of_calibration(self) -> List[Dict[str, Any]]:
        """
        Obtiene la lista de equipos de medida que están fuera de calibración
        
        Returns:
            Lista de equipos fuera de calibración
        """
        try:
            db_brass = self._get_brass_connection()
            
            # Primero obtener todos los equipos activos
            query_equipos = """
                SELECT IDEquipoMedida, NOMBRE, NS, PN, MARCA, MODELO
                FROM TbEquiposMedida 
                WHERE FechaFinServicio IS NULL
            """
            
            equipos = db_brass.execute_query(query_equipos)
            equipos_sin_calibracion = []
            
            for equipo in equipos:
                if not self._is_calibration_valid(equipo['IDEquipoMedida']):
                    equipos_sin_calibracion.append(equipo)
            
            self.logger.info(f"Encontrados {len(equipos_sin_calibracion)} equipos fuera de calibración")
            return equipos_sin_calibracion
            
        except Exception as e:
            self.logger.error(f"Error obteniendo equipos fuera de calibración: {e}")
            return []
    
    def _is_calibration_valid(self, equipment_id: int) -> bool:
        """
        Verifica si la calibración de un equipo está vigente
        
        Args:
            equipment_id: ID del equipo de medida
            
        Returns:
            True si la calibración está vigente
        """
        try:
            db_brass = self._get_brass_connection()
            
            query = """
                SELECT FechaFinCalibracion 
                FROM TbEquiposMedidaCalibraciones 
                WHERE IDEquipoMedida = ? 
                ORDER BY IDCalibracion DESC
            """
            
            result = db_brass.execute_query(query, (equipment_id,))
            
            if not result:
                return False
            
            fecha_fin = result[0]['FechaFinCalibracion']
            if not fecha_fin:
                return False
            
            # Convertir a date si es necesario
            if isinstance(fecha_fin, datetime):
                fecha_fin = fecha_fin.date()
            
            return date.today() < fecha_fin
            
        except Exception as e:
            self.logger.error(f"Error verificando calibración del equipo {equipment_id}: {e}")
            return False
    
    def generate_html_report(self, equipment_list: List[Dict[str, Any]]) -> str:
        """
        Genera el reporte HTML de equipos fuera de calibración
        
        Args:
            equipment_list: Lista de equipos fuera de calibración
            
        Returns:
            HTML del reporte
        """
        if not equipment_list:
            return ""
        
        title = "INFORME DE AVISOS DE EQUIPOS DE MEDIDA FUERA DE CALIBRACIÓN"
        html_content = generate_html_header(title, self.css_content)
        
        html_content += f"<h1>{title}</h1>\n"
        html_content += "<br><br>\n"
        
        # Tabla de equipos
        html_content += "<table>\n"
        html_content += "<tr>\n"
        html_content += '<td colspan="5" class="ColespanArriba">EQUIPOS DE MEDIDA FUERA DE CALIBRACIÓN</td>\n'
        html_content += "</tr>\n"
        
        # Encabezados
        html_content += "<tr>\n"
        html_content += '<td class="centrado"><strong>NOMBRE</strong></td>\n'
        html_content += '<td class="centrado"><strong>NS</strong></td>\n'
        html_content += '<td class="centrado"><strong>PN</strong></td>\n'
        html_content += '<td class="centrado"><strong>MARCA</strong></td>\n'
        html_content += '<td class="centrado"><strong>MODELO</strong></td>\n'
        html_content += "</tr>\n"
        
        # Filas de datos
        for equipo in equipment_list:
            html_content += "<tr>\n"
            html_content += f"<td>{safe_str(equipo.get('NOMBRE'))}</td>\n"
            html_content += f"<td>{safe_str(equipo.get('NS'))}</td>\n"
            html_content += f"<td>{safe_str(equipo.get('PN'))}</td>\n"
            html_content += f"<td>{safe_str(equipo.get('MARCA'))}</td>\n"
            html_content += f"<td>{safe_str(equipo.get('MODELO'))}</td>\n"
            html_content += "</tr>\n"
        
        html_content += "</table>\n"
        html_content += generate_html_footer()
        
        return html_content
    
    def get_admin_users(self) -> List[Dict[str, str]]:
        """
        Obtiene la lista de usuarios administradores usando la función común
        
        Returns:
            Lista de usuarios administradores
        """
        if self._admin_users is not None:
            return self._admin_users
        
        try:
            self._admin_users = get_users_with_fallback(
                user_type='admin',
                db_connection=self.db_tareas,
                config=config,
                logger=self.logger
            )
            return self._admin_users
            
        except Exception as e:
            self.logger.error(f"Error obteniendo usuarios administradores: {e}")
            return []
    
    def get_admin_emails_string(self) -> str:
        """
        Obtiene la cadena de correos de administradores separados por ;
        
        Returns:
            String con correos separados por ;
        """
        if self._admin_emails is not None:
            return self._admin_emails
        
        admin_users = self.get_admin_users()
        emails = [user['CorreoUsuario'] for user in admin_users if user['CorreoUsuario']]
        self._admin_emails = ';'.join(emails)
        return self._admin_emails
    
    def ejecutar_logica_especifica(self) -> bool:
        """
        Implementa la lógica específica de la tarea BRASS
        
        Returns:
            True si se ejecutó correctamente
        """
        try:
            self.logger.info("Ejecutando lógica específica de BRASS")
            
            # Obtener equipos fuera de calibración
            equipment_list = self.get_equipment_out_of_calibration()
            
            # Si no hay equipos fuera de calibración, la tarea se considera exitosa
            if not equipment_list:
                self.logger.info("No hay equipos fuera de calibración")
                return True
            
            # Generar reporte HTML
            html_report = self.generate_html_report(equipment_list)
            
            # Registrar correo usando la función común
            subject = "Informe Equipos de Medida fuera de calibración (BRASS)"
            success = register_email_in_database(
                self.db_tareas,
                "BRASS",
                subject,
                html_report,
                config.default_recipient,
                self.get_admin_emails_string()
            )
            
            if success:
                self.logger.info("Correo registrado correctamente")
                return True
            else:
                self.logger.error("Error registrando correo")
                return False
                
        except Exception as e:
            self.logger.error(f"Error en lógica específica de BRASS: {e}")
            return False
    
    def run(self) -> bool:
        """
        Método principal para ejecutar la tarea BRASS
        
        Returns:
            True si se ejecutó correctamente
        """
        try:
            # Verificar si debe ejecutarse
            if not self.debe_ejecutarse():
                self.logger.info("La tarea BRASS no debe ejecutarse hoy")
                return True
            
            # Ejecutar la lógica específica
            success = self.ejecutar_logica_especifica()
            
            if success:
                # Marcar como completada
                self.marcar_como_completada()
                self.logger.info("Tarea BRASS completada exitosamente")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error ejecutando tarea BRASS: {e}")
            return False