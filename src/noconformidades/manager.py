"""
Manager para el sistema de gestión de No Conformidades.

Este módulo gestiona las no conformidades, incluyendo:
- Seguimiento de acciones correctivas
- Avisos automáticos a técnicos
- Informes para personal de calidad
- Control de fechas de vencimiento
"""

import logging
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple
import os
from pathlib import Path

try:
    from ..common.config import Config
    from ..common.database import AccessDatabase
    from ..common.task_manager import TaskManager
    from ..common.utils import (
        hide_password_in_connection_string, 
        get_quality_users, 
        get_technical_users, 
        get_admin_users, 
        get_user_email,
        get_admin_emails_string,
        get_quality_emails_string,
        send_notification_email
    )
except ImportError:
    # Fallback para cuando se ejecuta directamente
    from common.config import Config
    from common.database import AccessDatabase
    from common.task_manager import TaskManager
    from common.utils import (
        hide_password_in_connection_string, 
        get_quality_users, 
        get_technical_users, 
        get_admin_users, 
        get_user_email,
        get_admin_emails_string,
        get_quality_emails_string,
        send_notification_email
    )


class NoConformidadesManager:
    """Manager para gestión de No Conformidades."""
    
    def __init__(self, config: Config = None, logger: logging.Logger = None):
        """Inicializa el manager de No Conformidades."""
        self.config = config or Config()
        self.logger = logger or logging.getLogger(__name__)
        
        # IDs de aplicación
        self.id_aplicacion = 8
        self.dias_necesarios_tecnicos = 1
        
        # Conexiones de base de datos
        self._cn_tareas = None
        self._cn_nc = None
        
        # Task manager
        self.task_manager = TaskManager(config, logger)
        
        # Colecciones de usuarios
        self.col_usuarios_calidad = {}
        self.col_usuarios_administradores = {}
        self.col_usuarios_calidad_excluir = {}
        
        # CSS para correos
        self.css = ""
        
    def __enter__(self):
        """Context manager entry."""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close_connections()
        
    def close_connections(self):
        """Cierra las conexiones de base de datos."""
        if self._cn_tareas:
            try:
                self._cn_tareas.disconnect()
            except Exception as e:
                self.logger.warning(f"Error cerrando conexión de tareas: {e}")
            finally:
                self._cn_tareas = None
                
        if self._cn_nc:
            try:
                self._cn_nc.disconnect()
            except Exception as e:
                self.logger.warning(f"Error cerrando conexión de NC: {e}")
            finally:
                self._cn_nc = None
        
        try:
            if self.task_manager:
                self.task_manager.close_connection()
        except Exception as e:
            self.logger.error(f"Error cerrando TaskManager: {e}")
    
    def _get_nc_connection(self):
        """Obtiene la conexión a la base de datos de No Conformidades."""
        if not self._cn_nc:
            connection_string = self.config.get_db_noconformidades_connection_string()
            
            self.logger.info(f"Conectando a base de datos de NC: {hide_password_in_connection_string(connection_string)}")
            self._cn_nc = AccessDatabase(connection_string)
            self._cn_nc.connect()
            
        return self._cn_nc._connection
    
    def es_dia_entre_semana(self) -> bool:
        """Verifica si es un día entre semana (lunes a viernes)."""
        return datetime.now().weekday() < 5  # 0=lunes, 6=domingo
    
    def requiere_tarea_tecnica(self) -> bool:
        """Verifica si se requiere ejecutar la tarea técnica."""
        return self.task_manager.requires_execution('NCTecnica', self.dias_necesarios_tecnicos)
    
    def requiere_tarea_calidad(self) -> bool:
        """Verifica si se requiere ejecutar la tarea de calidad."""
        return self.task_manager.requires_execution('NCCalidad', 1)
    
    def get_css(self) -> str:
        """Obtiene el CSS para los correos."""
        if self.css:
            return self.css
            
        try:
            css_path = self.config.css_file_path
            self.logger.info(f"Intentando cargar CSS desde: {css_path}")
            
            if os.path.exists(css_path):
                with open(css_path, 'r', encoding='utf-8') as f:
                    self.css = f.read()
                self.logger.info("CSS cargado desde archivo externo")
            else:
                self.logger.warning(f"Archivo CSS no encontrado: {css_path}")
                self.css = self._get_default_css()
                self.logger.info("Usando CSS por defecto")
                
        except Exception as e:
            self.logger.error(f"Error cargando CSS: {e}")
            self.css = self._get_default_css()
            self.logger.info("Usando CSS por defecto debido a error")
            
        return self.css
    
    def _get_default_css(self) -> str:
        """Retorna CSS por defecto con estilo moderno y colores suaves."""
        return """
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: #ffffff; 
            margin: 0; 
            padding: 20px; 
            color: #4a5568;
            line-height: 1.6;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            border: 1px solid #e2e8f0;
            overflow: hidden;
        }
        h1, h2, h3 { 
            color: #2d3748; 
            margin-bottom: 15px;
            font-weight: 600;
        }
        h2 {
            background: linear-gradient(135deg, #90cdf4 0%, #63b3ed 100%);
            color: white;
            padding: 20px;
            margin: 0 0 20px 0;
            text-align: center;
            font-size: 1.8rem;
        }
        table { 
            border-collapse: separate; 
            border-spacing: 0;
            width: 100%; 
            margin: 20px 0;
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
        }
        th, td { 
            padding: 15px 18px; 
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
        }
        th { 
            background: linear-gradient(135deg, #718096 0%, #4a5568 100%); 
            color: white; 
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-size: 0.9rem;
        }
        tr:hover td {
            background-color: #f8fafc;
        }
        tr:last-child td {
            border-bottom: none;
        }
        .Cabecera { 
            background: linear-gradient(135deg, #68d391 0%, #48bb78 100%); 
            color: white; 
            font-weight: 600; 
        }
        .ColespanArriba { 
            background: linear-gradient(135deg, #90cdf4 0%, #63b3ed 100%); 
            color: white; 
            font-weight: 700; 
            text-align: center;
            padding: 20px;
            font-size: 1.1rem;
        }
        .campo {
            font-weight: 600;
            color: #4a5568;
            background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
            padding: 12px 16px;
            border-radius: 8px;
            border-left: 4px solid #a0aec0;
        }
        .valor {
            color: #2d3748;
            padding: 12px 16px;
            background: #fafafa;
            border-radius: 8px;
            border-left: 4px solid #68d391;
        }
        .highlight { 
            background: linear-gradient(135deg, #fefcbf 0%, #faf089 100%);
            padding: 12px 16px;
            border-radius: 8px;
            border-left: 4px solid #f6ad55;
            margin: 10px 0;
        }
        .warning { 
            background: linear-gradient(135deg, #fed7d7 0%, #feb2b2 100%);
            color: #c53030; 
            padding: 12px 16px;
            border-radius: 8px;
            border-left: 4px solid #fc8181;
            margin: 10px 0;
        }
        .error { 
            background: linear-gradient(135deg, #fed7d7 0%, #feb2b2 100%);
            color: #c53030; 
            padding: 12px 16px;
            border-radius: 8px;
            border: 2px solid #fc8181;
            margin: 10px 0;
            font-weight: 600;
        }
        .success { 
            background: linear-gradient(135deg, #f0fff4 0%, #c6f6d5 100%);
            color: #2f855a; 
            padding: 12px 16px;
            border-radius: 8px;
            border-left: 4px solid #68d391;
            margin: 10px 0;
        }
        .centrado { 
            text-align: center; 
        }
        p {
            margin-bottom: 15px;
            color: #4a5568;
        }
        """
    
    def get_col_usuarios_calidad(self) -> List[Dict[str, str]]:
        """Obtiene usuarios de calidad usando la función común."""
        try:
            return get_quality_users(self.config.app_id_noconformidades, self.config, self.logger)
        except Exception as e:
            self.logger.error(f"Error obteniendo usuarios de calidad: {e}")
            return []
    
    def get_col_usuarios_administradores(self) -> List[Dict[str, str]]:
        """Obtiene usuarios administradores usando la función común."""
        try:
            return get_admin_users(self.config, self.logger)
        except Exception as e:
            self.logger.error(f"Error obteniendo usuarios administradores: {e}")
            return []
    
    def get_cadena_correo_administradores(self) -> str:
        """Obtiene cadena de correos de administradores."""
        try:
            return get_admin_emails_string(self.config)
        except Exception as e:
            self.logger.error(f"Error obteniendo cadena de correos administradores: {e}")
            return ""
    
    def get_cadena_correo_calidad(self) -> str:
        """Obtiene cadena de correos de calidad."""
        try:
            return get_quality_emails_string(self.config)
        except Exception as e:
            self.logger.error(f"Error obteniendo cadena de correos calidad: {e}")
            return ""
    
    def lanzar(self, forzar_ejecucion: bool = False) -> bool:
        """
        Función principal que ejecuta las tareas de No Conformidades.
        
        Args:
            forzar_ejecucion (bool): Si es True, ejecuta independientemente del día de la semana
        
        Returns:
            bool: True si se ejecutó correctamente, False en caso contrario
        """
        try:
            # Verificar si es día entre semana (a menos que se fuerce la ejecución)
            if not forzar_ejecucion and not self.es_dia_entre_semana():
                self.logger.info("No es día entre semana, saltando ejecución")
                return True
            
            if forzar_ejecucion:
                self.logger.info("Ejecución forzada - saltando verificación de día de la semana")
            
            # Verificar qué tareas se requieren
            self.logger.debug("Verificando si se requiere tarea técnica...")
            requiere_tecnica = self.requiere_tarea_tecnica()
            self.logger.debug(f"Tarea técnica requerida: {requiere_tecnica}")
            
            self.logger.debug("Verificando si se requiere tarea de calidad...")
            requiere_calidad = self.requiere_tarea_calidad()
            self.logger.debug(f"Tarea de calidad requerida: {requiere_calidad}")
            
            if not requiere_tecnica and not requiere_calidad:
                self.logger.info("No se requieren tareas de NC")
                return True
            
            # Inicializar recursos comunes si se requiere alguna tarea
            if requiere_tecnica or requiere_calidad:
                self.logger.debug("Obteniendo CSS...")
                self.css = self.get_css()
                self.logger.debug("CSS obtenido correctamente")
                # Los usuarios se obtienen dinámicamente cuando se necesiten
            
            # Ejecutar tareas según se requiera
            if requiere_tecnica:
                self.logger.info("Ejecutando tarea técnica de NC")
                self.logger.debug("Iniciando realizar_tarea_tecnicos...")
                self.realizar_tarea_tecnicos()
                self.logger.debug("realizar_tarea_tecnicos completado")
            
            if requiere_calidad:
                self.logger.info("Ejecutando tarea de calidad de NC")
                self.logger.debug("Iniciando realizar_tarea_calidad...")
                self.realizar_tarea_calidad()
                self.logger.debug("realizar_tarea_calidad completado")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error en lanzar NC: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return False
        finally:
            self.close_connections()
    
    def realizar_tarea_tecnicos(self):
        """
        Realiza la tarea de envío de avisos a técnicos sobre acciones correctivas
        que están próximas a caducar o ya han caducado
        """
        try:
            self.logger.info("Iniciando tarea de técnicos")
            
            # Obtener colección de usuarios con acciones próximas a caducar
            col_usuarios_arapc = self._get_col_usuarios_arapc()
            
            if not col_usuarios_arapc:
                self.logger.info("No hay acciones próximas a caducar para técnicos")
                return
            
            # Procesar cada técnico
            for usuario_data in col_usuarios_arapc:
                usuario = usuario_data['usuario']
                correo = self._get_correo(usuario)
                
                if not correo:
                    self.logger.warning(f"No se encontró correo para usuario: {usuario}")
                    continue
                
                # Obtener datos específicos para este técnico
                col_arapc = self._get_col_arapc(usuario)
                
                if not col_arapc:
                    continue
                
                # Generar HTML de la tabla
                html_tabla = self._html_tabla_arapc(col_arapc)
                
                # Obtener CSS
                css_content = self.get_css()
                
                # Construir el correo
                asunto = "Aviso de Acciones Correctivas próximas a caducar"
                
                cuerpo_html = f"""
                <html>
                <head>
                    <style>{css_content}</style>
                </head>
                <body>
                    <h2>Acciones Correctivas próximas a caducar</h2>
                    <p>Estimado/a {usuario},</p>
                    <p>Le informamos que tiene acciones correctivas que están próximas a caducar o ya han caducado:</p>
                    {html_tabla}
                    <p>Por favor, revise y actualice el estado de estas acciones.</p>
                    <p>Saludos cordiales,<br>Sistema de Gestión de Calidad</p>
                </body>
                </html>
                """
                
                # Enviar correo usando función centralizada
                success = send_notification_email(
                    subject=asunto,
                    body=cuerpo_html,
                    recipients=correo,
                    config=self.config,
                    application="NoConformidades_Tecnicos"
                )
                
                if success:
                    self.logger.info(f"Correo enviado a técnico: {usuario} ({correo})")
                else:
                    self.logger.error(f"Error enviando correo a técnico: {usuario} ({correo})")
            
            # Registrar ejecución de la tarea
            self._registrar_correo_tarea_tecnica()
            
        except Exception as e:
            self.logger.error(f"Error en realizar_tarea_tecnicos: {str(e)}")
            raise

    def realizar_tarea_calidad(self):
        """
        Realiza la tarea de envío de informes de calidad sobre no conformidades
        """
        try:
            self.logger.info("Iniciando tarea de calidad")
            
            # Obtener datos para el informe
            col_nc_caducar = self._get_col_nc_apto_caducar_o_caducadas()
            col_nc_resueltas_pte_ce = self._get_col_nc_resueltas_pte_ce()
            col_nc_registradas = self._get_col_nc_registradas()
            
            # Generar HTML para cada sección
            html_caducar = self._html_tabla_nc_apto_caducar_o_caducadas(col_nc_caducar)
            html_resueltas = self._html_tabla_nc_resueltas_pte_ce(col_nc_resueltas_pte_ce)
            html_registradas = self._html_tabla_nc_registradas(col_nc_registradas)
            
            # Obtener indicadores de calidad
            html_indicadores = self._html_indicadores_calidad()
            
            # Obtener CSS
            css_content = self.get_css()
            
            # Construir el correo
            asunto = "Informe de No Conformidades - Gestión de Calidad"
            
            cuerpo_html = f"""
            <html>
            <head>
                <style>{css_content}</style>
            </head>
            <body>
                <h1>Informe de No Conformidades</h1>
                
                <h2>Indicadores de Calidad</h2>
                {html_indicadores}
                
                <h2>No Conformidades próximas a caducar o caducadas</h2>
                {html_caducar}
                
                <h2>No Conformidades resueltas pendientes de Control de Eficacia</h2>
                {html_resueltas}
                
                <h2>No Conformidades registradas sin acciones asociadas</h2>
                {html_registradas}
                
                <p>Saludos cordiales,<br>Sistema de Gestión de Calidad</p>
            </body>
            </html>
            """
            
            # Obtener destinatarios de calidad
            cadena_correo_calidad = self.get_cadena_correo_calidad()
            
            if cadena_correo_calidad:
                # Enviar correo usando función centralizada
                success = send_notification_email(
                    subject=asunto,
                    body=cuerpo_html,
                    recipients=cadena_correo_calidad,
                    config=self.config,
                    application="NoConformidades_Calidad"
                )
                
                if success:
                    self.logger.info(f"Informe de calidad enviado a: {cadena_correo_calidad}")
                else:
                    self.logger.error(f"Error enviando informe de calidad a: {cadena_correo_calidad}")
            else:
                self.logger.warning("No se encontraron destinatarios para el informe de calidad")
            
            # Registrar ejecución de la tarea
            self._registrar_correo_tarea_calidad()
            
        except Exception as e:
            self.logger.error(f"Error en realizar_tarea_calidad: {str(e)}")
            raise
    
    def _registrar_tarea_tecnica(self):
        """Registra la ejecución de la tarea técnica."""
        self.task_manager.register_task_completion('NCTecnica')
    
    def _registrar_correo_tarea_tecnica(self):
        """Registra el envío de correo de la tarea técnica."""
        self._registrar_tarea_tecnica()

    def _registrar_correo_tarea_calidad(self):
        """Registra el envío de correo de la tarea de calidad."""
        self.task_manager.register_task_completion('NCCalidad')

    def _get_col_usuarios_arapc(self):
        """Obtiene la colección de usuarios con acciones correctivas próximas a caducar."""
        try:
            conn = self._get_nc_connection()
            cursor = conn.cursor()
            
            sql = """
                SELECT DISTINCT nc.RESPONSABLETELEFONICA as usuario
                FROM (TbNoConformidades nc 
                INNER JOIN (TbNCAccionCorrectivas ac 
                INNER JOIN TbNCAccionesRealizadas ar ON ac.IDAccionCorrectiva = ar.IDAccionCorrectiva) 
                ON nc.IDNoConformidad = ac.IDNoConformidad) 
                LEFT JOIN TbNCARAvisos av ON ar.IDAccionRealizada = av.IDAR
                WHERE ar.FechaFinReal IS NULL 
                AND nc.RESPONSABLETELEFONICA IS NOT NULL
                AND nc.RESPONSABLETELEFONICA <> ''
                AND (DateDiff('d', Now(), ar.FechaFinPrevista) <= 7 OR ar.FechaFinPrevista < Now())
            """
            
            cursor.execute(sql)
            row = cursor.fetchone()
            
            return row[0] if row else 0
            
        except Exception as e:
            self.logger.error(f"Error contando AC vencidas: {e}")
            return 0
            row = cursor.fetchone()
            
            return row[0] if row else 0
            
        except Exception as e:
            self.logger.error(f"Error contando acciones correctivas vencidas: {e}")
            return 0
            rows = cursor.fetchall()
            
            return [{'usuario': row[0]} for row in rows]
            
        except Exception as e:
            self.logger.error(f"Error obteniendo usuarios ARAPC: {e}")
            return []

    def _get_correo(self, usuario):
        """Obtiene el correo electrónico de un usuario."""
        return get_user_email(usuario, self.id_aplicacion, self.config, self.logger)

    def _get_col_arapc(self, usuario):
        """Obtiene las acciones correctivas próximas a caducar para un usuario específico."""
        try:
            conn = self._get_nc_connection()
            cursor = conn.cursor()
            
            sql = """
                SELECT nc.IDNoConformidad, nc.Descripcion as DescripcionNC,
                       ac.IDAccionCorrectiva, ac.AccionCorrectiva as DescripcionAC,
                       ar.FechaFinPrevista, ar.AccionRealizada as Estado,
                       DateDiff('d', Now(), ar.FechaFinPrevista) as DiasRestantes
                FROM (TbNoConformidades nc 
                INNER JOIN (TbNCAccionCorrectivas ac 
                INNER JOIN TbNCAccionesRealizadas ar ON ac.IDAccionCorrectiva = ar.IDAccionCorrectiva) 
                ON nc.IDNoConformidad = ac.IDNoConformidad) 
                LEFT JOIN TbNCARAvisos av ON ar.IDAccionRealizada = av.IDAR
                WHERE nc.RESPONSABLETELEFONICA = ?
                AND ar.FechaFinReal IS NULL
                AND (DateDiff('d', Now(), ar.FechaFinPrevista) <= 7 OR ar.FechaFinPrevista < Now())
                ORDER BY ar.FechaFinPrevista
            """
            
            cursor.execute(sql, (usuario,))
            rows = cursor.fetchall()
            
            return [{
                'IDNoConformidad': row[0],
                'DescripcionNC': row[1],
                'IDAccionCorrectiva': row[2],
                'DescripcionAC': row[3],
                'FechaPrevista': row[4],
                'Estado': row[5],
                'DiasRestantes': row[6]
            } for row in rows]
            
        except Exception as e:
            self.logger.error(f"Error obteniendo ARAPC para {usuario}: {e}")
            return []

    def _html_tabla_arapc(self, col_arapc):
        """Genera HTML para la tabla de acciones correctivas próximas a caducar."""
        if not col_arapc:
            return "<p>No hay acciones correctivas próximas a caducar.</p>"
        
        html = """
        <table class="tabla-datos">
            <thead>
                <tr>
                    <th>ID NC</th>
                    <th>Descripción NC</th>
                    <th>ID AC</th>
                    <th>Descripción AC</th>
                    <th>Fecha Prevista</th>
                    <th>Estado</th>
                    <th>Días Restantes</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for item in col_arapc:
            dias_restantes = item['DiasRestantes']
            clase_fila = "fila-vencida" if dias_restantes < 0 else "fila-proxima" if dias_restantes <= 3 else ""
            
            html += f"""
                <tr class="{clase_fila}">
                    <td>{item['IDNoConformidad']}</td>
                    <td>{item['DescripcionNC']}</td>
                    <td>{item['IDAccionCorrectiva']}</td>
                    <td>{item['DescripcionAC']}</td>
                    <td>{item['FechaPrevista'].strftime('%d/%m/%Y') if item['FechaPrevista'] else ''}</td>
                    <td>{item['Estado']}</td>
                    <td>{dias_restantes}</td>
                </tr>
            """
        
        html += """
            </tbody>
        </table>
        """
        
        return html

    def _get_col_nc_apto_caducar_o_caducadas(self):
        """Obtiene no conformidades próximas a caducar o caducadas."""
        try:
            conn = self._get_nc_connection()
            cursor = conn.cursor()
            
            sql = """
                SELECT nc.IDNoConformidad, nc.Descripcion, nc.FechaDeteccion,
                       nc.ResponsableCalidad, nc.Estado,
                       DateDiff('d', Now(), nc.FechaPrevistaCierre) as DiasRestantes
                FROM TbNoConformidades nc
                WHERE nc.Estado <> 'Cerrada'
                AND (DateDiff('d', Now(), nc.FechaPrevistaCierre) <= 7 OR nc.FechaPrevistaCierre < Now())
                ORDER BY nc.FechaPrevistaCierre
            """
            
            cursor.execute(sql)
            rows = cursor.fetchall()
            
            return [{
                'IDNoConformidad': row[0],
                'Descripcion': row[1],
                'FechaDeteccion': row[2],
                'ResponsableCalidad': row[3],
                'Estado': row[4],
                'DiasRestantes': row[5]
            } for row in rows]
            
        except Exception as e:
            self.logger.error(f"Error obteniendo NC próximas a caducar: {e}")
            return []

    def _get_col_nc_resueltas_pte_ce(self):
        """Obtiene no conformidades resueltas pendientes de control de eficacia."""
        try:
            conn = self._get_nc_connection()
            cursor = conn.cursor()
            
            sql = """
                SELECT nc.IDNoConformidad, nc.Descripcion, nc.FechaDeteccion,
                       nc.ResponsableCalidad, nc.FechaResolucion
                FROM TbNoConformidades nc
                WHERE nc.Estado = 'Resuelta'
                AND nc.ControlEficacia IS NULL
                ORDER BY nc.FechaResolucion
            """
            
            cursor.execute(sql)
            rows = cursor.fetchall()
            
            return [{
                'IDNoConformidad': row[0],
                'Descripcion': row[1],
                'FechaDeteccion': row[2],
                'ResponsableCalidad': row[3],
                'FechaResolucion': row[4]
            } for row in rows]
            
        except Exception as e:
            self.logger.error(f"Error obteniendo NC resueltas pendientes CE: {e}")
            return []

    def _get_col_nc_registradas(self):
        """Obtiene no conformidades registradas sin acciones asociadas."""
        try:
            conn = self._get_nc_connection()
            cursor = conn.cursor()
            
            sql = """
                SELECT nc.IDNoConformidad, nc.Descripcion, nc.FechaDeteccion,
                       nc.ResponsableCalidad, nc.Estado
                FROM TbNoConformidades nc
                LEFT JOIN TbNCAccionCorrectivas ac ON nc.IDNoConformidad = ac.IDNoConformidad
                WHERE ac.IDAccionCorrectiva IS NULL
                AND nc.Estado <> 'Cerrada'
                ORDER BY nc.FechaDeteccion DESC
            """
            
            cursor.execute(sql)
            rows = cursor.fetchall()
            
            return [{
                'IDNoConformidad': row[0],
                'Descripcion': row[1],
                'FechaDeteccion': row[2],
                'ResponsableCalidad': row[3],
                'Estado': row[4]
            } for row in rows]
            
        except Exception as e:
            self.logger.error(f"Error obteniendo NC registradas: {e}")
            return []

    def _html_tabla_nc_apto_caducar_o_caducadas(self, col_nc):
        """Genera HTML para la tabla de NC próximas a caducar."""
        if not col_nc:
            return "<p>No hay no conformidades próximas a caducar.</p>"
        
        html = """
        <table class="tabla-datos">
            <thead>
                <tr>
                    <th>ID NC</th>
                    <th>Descripción</th>
                    <th>Fecha Detección</th>
                    <th>Responsable Calidad</th>
                    <th>Estado</th>
                    <th>Días Restantes</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for item in col_nc:
            dias_restantes = item['DiasRestantes']
            clase_fila = "fila-vencida" if dias_restantes < 0 else "fila-proxima" if dias_restantes <= 3 else ""
            
            html += f"""
                <tr class="{clase_fila}">
                    <td>{item['IDNoConformidad']}</td>
                    <td>{item['Descripcion']}</td>
                    <td>{item['FechaDeteccion'].strftime('%d/%m/%Y') if item['FechaDeteccion'] else ''}</td>
                    <td>{item['ResponsableCalidad']}</td>
                    <td>{item['Estado']}</td>
                    <td>{dias_restantes}</td>
                </tr>
            """
        
        html += """
            </tbody>
        </table>
        """
        
        return html

    def _html_tabla_nc_resueltas_pte_ce(self, col_nc):
        """Genera HTML para la tabla de NC resueltas pendientes de control de eficacia."""
        if not col_nc:
            return "<p>No hay no conformidades resueltas pendientes de control de eficacia.</p>"
        
        html = """
        <table class="tabla-datos">
            <thead>
                <tr>
                    <th>ID NC</th>
                    <th>Descripción</th>
                    <th>Fecha Detección</th>
                    <th>Responsable Calidad</th>
                    <th>Fecha Resolución</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for item in col_nc:
            html += f"""
                <tr>
                    <td>{item['IDNoConformidad']}</td>
                    <td>{item['Descripcion']}</td>
                    <td>{item['FechaDeteccion'].strftime('%d/%m/%Y') if item['FechaDeteccion'] else ''}</td>
                    <td>{item['ResponsableCalidad']}</td>
                    <td>{item['FechaResolucion'].strftime('%d/%m/%Y') if item['FechaResolucion'] else ''}</td>
                </tr>
            """
        
        html += """
            </tbody>
        </table>
        """
        
        return html

    def _html_tabla_nc_registradas(self, col_nc):
        """Genera HTML para la tabla de NC registradas sin acciones."""
        if not col_nc:
            return "<p>No hay no conformidades registradas sin acciones asociadas.</p>"
        
        html = """
        <table class="tabla-datos">
            <thead>
                <tr>
                    <th>ID NC</th>
                    <th>Descripción</th>
                    <th>Fecha Detección</th>
                    <th>Responsable Calidad</th>
                    <th>Estado</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for item in col_nc:
            html += f"""
                <tr>
                    <td>{item['IDNoConformidad']}</td>
                    <td>{item['Descripcion']}</td>
                    <td>{item['FechaDeteccion'].strftime('%d/%m/%Y') if item['FechaDeteccion'] else ''}</td>
                    <td>{item['ResponsableCalidad']}</td>
                    <td>{item['Estado']}</td>
                </tr>
            """
        
        html += """
            </tbody>
        </table>
        """
        
        return html

    def _html_indicadores_calidad(self):
        """Genera HTML para los indicadores de calidad."""
        try:
            # Obtener estadísticas
            total_nc_abiertas = self._get_count_nc_abiertas()
            total_nc_cerradas_mes = self._get_count_nc_cerradas_mes()
            total_ac_vencidas = self._get_count_ac_vencidas()
            
            html = f"""
            <table class="tabla-indicadores">
                <thead>
                    <tr>
                        <th>Indicador</th>
                        <th>Valor</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>No Conformidades Abiertas</td>
                        <td>{total_nc_abiertas}</td>
                    </tr>
                    <tr>
                        <td>No Conformidades Cerradas (Este Mes)</td>
                        <td>{total_nc_cerradas_mes}</td>
                    </tr>
                    <tr>
                        <td>Acciones Correctivas Vencidas</td>
                        <td>{total_ac_vencidas}</td>
                    </tr>
                </tbody>
            </table>
            """
            
            return html
            
        except Exception as e:
            self.logger.error(f"Error generando indicadores de calidad: {e}")
            return "<p>Error generando indicadores de calidad.</p>"

    def _get_count_nc_abiertas(self):
        """Obtiene el número de no conformidades abiertas."""
        try:
            conn = self._get_nc_connection()
            cursor = conn.cursor()
            
            sql = "SELECT COUNT(*) FROM TbNoConformidades WHERE Estado <> 'Cerrada'"
            cursor.execute(sql)
            row = cursor.fetchone()
            
            return row[0] if row else 0
            
        except Exception as e:
            self.logger.error(f"Error contando NC abiertas: {e}")
            return 0

    def _get_count_nc_cerradas_mes(self):
        """Obtiene el número de no conformidades cerradas este mes."""
        try:
            conn = self._get_nc_connection()
            cursor = conn.cursor()
            
            sql = """
                SELECT COUNT(*) 
                FROM TbNoConformidades 
                WHERE Estado = 'Cerrada' 
                AND Month(FechaCierre) = Month(Now()) 
                AND Year(FechaCierre) = Year(Now())
            """
            cursor.execute(sql)
            row = cursor.fetchone()
            
            return row[0] if row else 0
            
        except Exception as e:
            self.logger.error(f"Error contando NC cerradas este mes: {e}")
            return 0

    def _get_count_ac_vencidas(self):
        """Obtiene el número de acciones correctivas vencidas."""
        try:
            conn = self._get_nc_connection()
            cursor = conn.cursor()
            
            sql = """
                SELECT COUNT(*) 
                FROM TbNCAccionCorrectivas ac
                INNER JOIN TbNCAccionesRealizadas ar ON ac.IDAccionCorrectiva = ar.IDAccionCorrectiva
                WHERE ar.FechaFinReal IS NULL 
                AND ar.FechaFinPrevista < Now()
            """
            cursor.execute(sql)
            row = cursor.fetchone()
            
            return row[0] if row else 0
            
        except Exception as e:
            self.logger.error(f"Error contando AC vencidas: {e}")
            return 0
            row = cursor.fetchone()
            
            return row[0] if row else 0
            
        except Exception as e:
            self.logger.error(f"Error contando acciones correctivas vencidas: {e}")
            return 0
            row = cursor.fetchone()
            
            return row[0] if row else 0
            
        except Exception as e:
            self.logger.error(f"Error contando AC vencidas: {e}")
            return 0

    def _html_tabla_nc_apto_caducar_o_caducadas(self, col_nc):
        """Genera HTML para la tabla de NC próximas a caducar."""
        if not col_nc:
            return "<p>No hay no conformidades próximas a caducar.</p>"
        
        html = """
        <table class="tabla-datos">
            <thead>
                <tr>
                    <th>ID NC</th>
                    <th>Descripción</th>
                    <th>Fecha Detección</th>
                    <th>Responsable Calidad</th>
                    <th>Estado</th>
                    <th>Días Restantes</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for item in col_nc:
            dias_restantes = item['DiasRestantes']
            clase_fila = "fila-vencida" if dias_restantes < 0 else "fila-proxima" if dias_restantes <= 3 else ""
            
            html += f"""
                <tr class="{clase_fila}">
                    <td>{item['IDNoConformidad']}</td>
                    <td>{item['Descripcion']}</td>
                    <td>{item['FechaDeteccion'].strftime('%d/%m/%Y') if item['FechaDeteccion'] else ''}</td>
                    <td>{item['ResponsableCalidad']}</td>
                    <td>{item['Estado']}</td>
                    <td>{dias_restantes}</td>
                </tr>
            """
        
        html += """
            </tbody>
        </table>
        """
        
        return html

    def _html_tabla_nc_resueltas_pte_ce(self, col_nc):
        """Genera HTML para la tabla de NC resueltas pendientes de control de eficacia."""
        if not col_nc:
            return "<p>No hay no conformidades resueltas pendientes de control de eficacia.</p>"
        
        html = """
        <table class="tabla-datos">
            <thead>
                <tr>
                    <th>ID NC</th>
                    <th>Descripción</th>
                    <th>Fecha Detección</th>
                    <th>Responsable Calidad</th>
                    <th>Fecha Resolución</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for item in col_nc:
            html += f"""
                <tr>
                    <td>{item['IDNoConformidad']}</td>
                    <td>{item['Descripcion']}</td>
                    <td>{item['FechaDeteccion'].strftime('%d/%m/%Y') if item['FechaDeteccion'] else ''}</td>
                    <td>{item['ResponsableCalidad']}</td>
                    <td>{item['FechaResolucion'].strftime('%d/%m/%Y') if item['FechaResolucion'] else ''}</td>
                </tr>
            """
        
        html += """
            </tbody>
        </table>
        """
        
        return html

    def _html_tabla_nc_registradas(self, col_nc):
        """Genera HTML para la tabla de NC registradas sin acciones."""
        if not col_nc:
            return "<p>No hay no conformidades registradas sin acciones asociadas.</p>"
        
        html = """
        <table class="tabla-datos">
            <thead>
                <tr>
                    <th>ID NC</th>
                    <th>Descripción</th>
                    <th>Fecha Detección</th>
                    <th>Responsable Calidad</th>
                    <th>Estado</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for item in col_nc:
            html += f"""
                <tr>
                    <td>{item['IDNoConformidad']}</td>
                    <td>{item['Descripcion']}</td>
                    <td>{item['FechaDeteccion'].strftime('%d/%m/%Y') if item['FechaDeteccion'] else ''}</td>
                    <td>{item['ResponsableCalidad']}</td>
                    <td>{item['Estado']}</td>
                </tr>
            """
        
        html += """
            </tbody>
        </table>
        """
        
        return html

    def _html_indicadores_calidad(self):
        """Genera HTML para los indicadores de calidad."""
        try:
            # Obtener estadísticas
            total_nc_abiertas = self._get_count_nc_abiertas()
            total_nc_cerradas_mes = self._get_count_nc_cerradas_mes()
            total_ac_vencidas = self._get_count_ac_vencidas()
            
            html = f"""
            <table class="tabla-indicadores">
                <thead>
                    <tr>
                        <th>Indicador</th>
                        <th>Valor</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>No Conformidades Abiertas</td>
                        <td>{total_nc_abiertas}</td>
                    </tr>
                    <tr>
                        <td>No Conformidades Cerradas (Este Mes)</td>
                        <td>{total_nc_cerradas_mes}</td>
                    </tr>
                    <tr>
                        <td>Acciones Correctivas Vencidas</td>
                        <td>{total_ac_vencidas}</td>
                    </tr>
                </tbody>
            </table>
            """
            
            return html
            
        except Exception as e:
            self.logger.error(f"Error generando indicadores de calidad: {e}")
            return "<p>Error generando indicadores de calidad.</p>"

    def _get_count_nc_abiertas(self):
        """Obtiene el número de no conformidades abiertas."""
        try:
            conn = self._get_nc_connection()
            cursor = conn.cursor()
            
            sql = "SELECT COUNT(*) FROM TbNoConformidades WHERE Estado <> 'Cerrada'"
            cursor.execute(sql)
            row = cursor.fetchone()
            
            return row[0] if row else 0
            
        except Exception as e:
            self.logger.error(f"Error contando NC abiertas: {e}")
            return 0

    def _get_count_nc_cerradas_mes(self):
        """Obtiene el número de no conformidades cerradas este mes."""
        try:
            conn = self._get_nc_connection()
            cursor = conn.cursor()
            
            sql = """
                SELECT COUNT(*) 
                FROM TbNoConformidades 
                WHERE Estado = 'Cerrada' 
                AND Month(FechaCierre) = Month(Now()) 
                AND Year(FechaCierre) = Year(Now())
            """
            cursor.execute(sql)
            row = cursor.fetchone()
            
            return row[0] if row else 0
            
        except Exception as e:
            self.logger.error(f"Error contando NC cerradas este mes: {e}")
            return 0

    def _get_count_ac_vencidas(self):
        """Obtiene el número de acciones correctivas vencidas."""
        try:
            conn = self._get_nc_connection()
            cursor = conn.cursor()
            
            sql = """
                SELECT COUNT(*) 
                FROM TbNCAccionCorrectivas ac
                INNER JOIN TbNCAccionesRealizadas ar ON ac.IDAccionCorrectiva = ar.IDAccionCorrectiva
                WHERE ar.FechaFinReal IS NULL 
                AND ar.FechaFinPrevista < Now()
            """
            cursor.execute(sql)
            row = cursor.fetchone()
            
            return row[0] if row else 0
            
        except Exception as e:
            self.logger.error(f"Error contando AC vencidas: {e}")
            return 0

    def _html_tabla_nc_apto_caducar_o_caducadas(self, col_nc):
        """Genera HTML para la tabla de NC próximas a caducar."""
        if not col_nc:
            return "<p>No hay no conformidades próximas a caducar.</p>"
        
        html = """
        <table class="tabla-datos">
            <thead>
                <tr>
                    <th>ID NC</th>
                    <th>Descripción</th>
                    <th>Fecha Detección</th>
                    <th>Responsable Calidad</th>
                    <th>Estado</th>
                    <th>Días Restantes</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for item in col_nc:
            dias_restantes = item['DiasRestantes']
            clase_fila = "fila-vencida" if dias_restantes < 0 else "fila-proxima" if dias_restantes <= 3 else ""
            
            html += f"""
                <tr class="{clase_fila}">
                    <td>{item['IDNoConformidad']}</td>
                    <td>{item['Descripcion']}</td>
                    <td>{item['FechaDeteccion'].strftime('%d/%m/%Y') if item['FechaDeteccion'] else ''}</td>
                    <td>{item['ResponsableCalidad']}</td>
                    <td>{item['Estado']}</td>
                    <td>{dias_restantes}</td>
                </tr>
            """
        
        html += """
            </tbody>
        </table>
        """
        
        return html

    def _html_tabla_nc_resueltas_pte_ce(self, col_nc):
        """Genera HTML para la tabla de NC resueltas pendientes de control de eficacia."""
        if not col_nc:
            return "<p>No hay no conformidades resueltas pendientes de control de eficacia.</p>"
        
        html = """
        <table class="tabla-datos">
            <thead>
                <tr>
                    <th>ID NC</th>
                    <th>Descripción</th>
                    <th>Fecha Detección</th>
                    <th>Responsable Calidad</th>
                    <th>Fecha Resolución</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for item in col_nc:
            html += f"""
                <tr>
                    <td>{item['IDNoConformidad']}</td>
                    <td>{item['Descripcion']}</td>
                    <td>{item['FechaDeteccion'].strftime('%d/%m/%Y') if item['FechaDeteccion'] else ''}</td>
                    <td>{item['ResponsableCalidad']}</td>
                    <td>{item['FechaResolucion'].strftime('%d/%m/%Y') if item['FechaResolucion'] else ''}</td>
                </tr>
            """
        
        html += """
            </tbody>
        </table>
        """
        
        return html

    def _html_tabla_nc_registradas(self, col_nc):
        """Genera HTML para la tabla de NC registradas sin acciones."""
        if not col_nc:
            return "<p>No hay no conformidades registradas sin acciones asociadas.</p>"
        
        html = """
        <table class="tabla-datos">
            <thead>
                <tr>
                    <th>ID NC</th>
                    <th>Descripción</th>
                    <th>Fecha Detección</th>
                    <th>Responsable Calidad</th>
                    <th>Estado</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for item in col_nc:
            html += f"""
                <tr>
                    <td>{item['IDNoConformidad']}</td>
                    <td>{item['Descripcion']}</td>
                    <td>{item['FechaDeteccion'].strftime('%d/%m/%Y') if item['FechaDeteccion'] else ''}</td>
                    <td>{item['ResponsableCalidad']}</td>
                    <td>{item['Estado']}</td>
                </tr>
            """
        
        html += """
            </tbody>
        </table>
        """
        
        return html

    def _html_indicadores_calidad(self):
        """Genera HTML para los indicadores de calidad."""
        try:
            # Obtener estadísticas
            total_nc_abiertas = self._get_count_nc_abiertas()
            total_nc_cerradas_mes = self._get_count_nc_cerradas_mes()
            total_ac_vencidas = self._get_count_ac_vencidas()
            
            html = f"""
            <table class="tabla-indicadores">
                <thead>
                    <tr>
                        <th>Indicador</th>
                        <th>Valor</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>No Conformidades Abiertas</td>
                        <td>{total_nc_abiertas}</td>
                    </tr>
                    <tr>
                        <td>No Conformidades Cerradas (Este Mes)</td>
                        <td>{total_nc_cerradas_mes}</td>
                    </tr>
                    <tr>
                        <td>Acciones Correctivas Vencidas</td>
                        <td>{total_ac_vencidas}</td>
                    </tr>
                </tbody>
            </table>
            """
            
            return html
            
        except Exception as e:
            self.logger.error(f"Error generando indicadores de calidad: {e}")
            return "<p>Error generando indicadores de calidad.</p>"

    def _get_count_nc_abiertas(self):
        """Obtiene el número de no conformidades abiertas."""
        try:
            conn = self._get_nc_connection()
            cursor = conn.cursor()
            
            sql = "SELECT COUNT(*) FROM TbNoConformidades WHERE Estado <> 'Cerrada'"
            cursor.execute(sql)
            row = cursor.fetchone()
            
            return row[0] if row else 0
            
        except Exception as e:
            self.logger.error(f"Error contando NC abiertas: {e}")
            return 0

    def _get_count_nc_cerradas_mes(self):
        """Obtiene el número de no conformidades cerradas este mes."""
        try:
            conn = self._get_nc_connection()
            cursor = conn.cursor()
            
            sql = """
                SELECT COUNT(*) 
                FROM TbNoConformidades 
                WHERE Estado = 'Cerrada' 
                AND Month(FechaCierre) = Month(Now()) 
                AND Year(FechaCierre) = Year(Now())
            """
            cursor.execute(sql)
            row = cursor.fetchone()
            
            return row[0] if row else 0
            
        except Exception as e:
            self.logger.error(f"Error contando NC cerradas este mes: {e}")
            return 0

    def _get_count_ac_vencidas(self):
        """Obtiene el número de acciones correctivas vencidas."""
        try:
            conn = self._get_nc_connection()
            cursor = conn.cursor()
            
            sql = """
                SELECT COUNT(*) 
                FROM TbNCAccionCorrectivas ac
                INNER JOIN TbNCAccionesRealizadas ar ON ac.IDAccionCorrectiva = ar.IDAccionCorrectiva
                WHERE ar.FechaFinReal IS NULL 
                AND ar.FechaFinPrevista < Now()
            """
            cursor.execute(sql)
            row = cursor.fetchone()
            
            return row[0] if row else 0
            
        except Exception as e:
            self.logger.error(f"Error contando AC vencidas: {e}")
            return 0

    def _html_tabla_nc_apto_caducar_o_caducadas(self, col_nc):
        """Genera HTML para la tabla de NC próximas a caducar."""
        if not col_nc:
            return "<p>No hay no conformidades próximas a caducar.</p>"
        
        html = """
        <table class="tabla-datos">
            <thead>
                <tr>
                    <th>ID NC</th>
                    <th>Descripción</th>
                    <th>Fecha Detección</th>
                    <th>Responsable Calidad</th>
                    <th>Estado</th>
                    <th>Días Restantes</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for item in col_nc:
            dias_restantes = item['DiasRestantes']
            clase_fila = "fila-vencida" if dias_restantes < 0 else "fila-proxima" if dias_restantes <= 3 else ""
            
            html += f"""
                <tr class="{clase_fila}">
                    <td>{item['IDNoConformidad']}</td>
                    <td>{item['Descripcion']}</td>
                    <td>{item['FechaDeteccion'].strftime('%d/%m/%Y') if item['FechaDeteccion'] else ''}</td>
                    <td>{item['ResponsableCalidad']}</td>
                    <td>{item['Estado']}</td>
                    <td>{dias_restantes}</td>
                </tr>
            """
        
        html += """
            </tbody>
        </table>
        """
        
        return html

    def _html_tabla_nc_resueltas_pte_ce(self, col_nc):
        """Genera HTML para la tabla de NC resueltas pendientes de control de eficacia."""
        if not col_nc:
            return "<p>No hay no conformidades resueltas pendientes de control de eficacia.</p>"
        
        html = """
        <table class="tabla-datos">
            <thead>
                <tr>
                    <th>ID NC</th>
                    <th>Descripción</th>
                    <th>Fecha Detección</th>
                    <th>Responsable Calidad</th>
                    <th>Fecha Resolución</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for item in col_nc:
            html += f"""
                <tr>
                    <td>{item['IDNoConformidad']}</td>
                    <td>{item['Descripcion']}</td>
                    <td>{item['FechaDeteccion'].strftime('%d/%m/%Y') if item['FechaDeteccion'] else ''}</td>
                    <td>{item['ResponsableCalidad']}</td>
                    <td>{item['FechaResolucion'].strftime('%d/%m/%Y') if item['FechaResolucion'] else ''}</td>
                </tr>
            """
        
        html += """
            </tbody>
        </table>
        """
        
        return html

    def _html_tabla_nc_registradas(self, col_nc):
        """Genera HTML para la tabla de NC registradas sin acciones."""
        if not col_nc:
            return "<p>No hay no conformidades registradas sin acciones asociadas.</p>"
        
        html = """
        <table class="tabla-datos">
            <thead>
                <tr>
                    <th>ID NC</th>
                    <th>Descripción</th>
                    <th>Fecha Detección</th>
                    <th>Responsable Calidad</th>
                    <th>Estado</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for item in col_nc:
            html += f"""
                <tr>
                    <td>{item['IDNoConformidad']}</td>
                    <td>{item['Descripcion']}</td>
                    <td>{item['FechaDeteccion'].strftime('%d/%m/%Y') if item['FechaDeteccion'] else ''}</td>
                    <td>{item['ResponsableCalidad']}</td>
                    <td>{item['Estado']}</td>
                </tr>
            """
        
        html += """
            </tbody>
        </table>
        """
        
        return html

    def _html_indicadores_calidad(self):
        """Genera HTML para los indicadores de calidad."""
        try:
            # Obtener estadísticas
            total_nc_abiertas = self._get_count_nc_abiertas()
            total_nc_cerradas_mes = self._get_count_nc_cerradas_mes()
            total_ac_vencidas = self._get_count_ac_vencidas()
            
            html = f"""
            <table class="tabla-indicadores">
                <thead>
                    <tr>
                        <th>Indicador</th>
                        <th>Valor</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>No Conformidades Abiertas</td>
                        <td>{total_nc_abiertas}</td>
                    </tr>
                    <tr>
                        <td>No Conformidades Cerradas (Este Mes)</td>
                        <td>{total_nc_cerradas_mes}</td>
                    </tr>
                    <tr>
                        <td>Acciones Correctivas Vencidas</td>
                        <td>{total_ac_vencidas}</td>
                    </tr>
                </tbody>
            </table>
            """
            
            return html
            
        except Exception as e:
            self.logger.error(f"Error generando indicadores de calidad: {e}")
            return "<p>Error generando indicadores de calidad.</p>"

    def _get_count_nc_abiertas(self):
        """Obtiene el número de no conformidades abiertas."""
        try:
            conn = self._get_nc_connection()
            cursor = conn.cursor()
            
            sql = "SELECT COUNT(*) FROM TbNoConformidades WHERE Estado <> 'Cerrada'"
            cursor.execute(sql)
            row = cursor.fetchone()
            
            return row[0] if row else 0
            
        except Exception as e:
            self.logger.error(f"Error contando NC abiertas: {e}")
            return 0

    def _get_count_nc_cerradas_mes(self):
        """Obtiene el número de no conformidades cerradas este mes."""
        try:
            conn = self._get_nc_connection()
            cursor = conn.cursor()
            
            sql = """
                SELECT COUNT(*) 
                FROM TbNoConformidades 
                WHERE Estado = 'Cerrada' 
                AND Month(FechaCierre) = Month(Now()) 
                AND Year(FechaCierre) = Year(Now())
            """
            cursor.execute(sql)
            row = cursor.fetchone()
            
            return row[0] if row else 0
            
        except Exception as e:
            self.logger.error(f"Error contando NC cerradas este mes: {e}")
            return 0

    def _get_count_ac_vencidas(self):
        """Obtiene el número de acciones correctivas vencidas."""
        try:
            conn = self._get_nc_connection()
            cursor = conn.cursor()
            
            sql = """
                SELECT COUNT(*) 
                FROM TbNCAccionCorrectivas ac
                INNER JOIN TbNCAccionesRealizadas ar ON ac.IDAccionCorrectiva = ar.IDAccionCorrectiva
                WHERE ar.FechaFinReal IS NULL 
                AND ar.FechaFinPrevista < Now()
            """
            cursor.execute(sql)
            row = cursor.fetchone()
            
            return row[0] if row else 0
            
        except Exception as e:
            self.logger.error(f"Error contando AC vencidas: {e}")
            return 0

    def _html_tabla_nc_apto_caducar_o_caducadas(self, col_nc):
        """Genera HTML para la tabla de NC próximas a caducar."""
        if not col_nc:
            return "<p>No hay no conformidades próximas a caducar.</p>"
        
        html = """
        <table class="tabla-datos">
            <thead>
                <tr>
                    <th>ID NC</th>
                    <th>Descripción</th>
                    <th>Fecha Detección</th>
                    <th>Responsable Calidad</th>
                    <th>Estado</th>
                    <th>Días Restantes</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for item in col_nc:
            dias_restantes = item['DiasRestantes']
            clase_fila = "fila-vencida" if dias_restantes < 0 else "fila-proxima" if dias_restantes <= 3 else ""
            
            html += f"""
                <tr class="{clase_fila}">
                    <td>{item['IDNoConformidad']}</td>
                    <td>{item['Descripcion']}</td>
                    <td>{item['FechaDeteccion'].strftime('%d/%m/%Y') if item['FechaDeteccion'] else ''}</td>
                    <td>{item['ResponsableCalidad']}</td>
                    <td>{item['Estado']}</td>
                    <td>{dias_restantes}</td>
                </tr>
            """
        
        html += """
            </tbody>
        </table>
        """
        
        return html

    def _html_tabla_nc_resueltas_pte_ce(self, col_nc):
        """Genera HTML para la tabla de NC resueltas pendientes de control de eficacia."""
        if not col_nc:
            return "<p>No hay no conformidades resueltas pendientes de control de eficacia.</p>"
        
        html = """
        <table class="tabla-datos">
            <thead>
                <tr>
                    <th>ID NC</th>
                    <th>Descripción</th>
                    <th>Fecha Detección</th>
                    <th>Responsable Calidad</th>
                    <th>Fecha Resolución</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for item in col_nc:
            html += f"""
                <tr>
                    <td>{item['IDNoConformidad']}</td>
                    <td>{item['Descripcion']}</td>
                    <td>{item['FechaDeteccion'].strftime('%d/%m/%Y') if item['FechaDeteccion'] else ''}</td>
                    <td>{item['ResponsableCalidad']}</td>
                    <td>{item['FechaResolucion'].strftime('%d/%m/%Y') if item['FechaResolucion'] else ''}</td>
                </tr>
            """
        
        html += """
            </tbody>
        </table>
        """
        
        return html

    def _html_tabla_nc_registradas(self, col_nc):
        """Genera HTML para la tabla de NC registradas sin acciones."""
        if not col_nc:
            return "<p>No hay no conformidades registradas sin acciones asociadas.</p>"
        
        html = """
        <table class="tabla-datos">
            <thead>
                <tr>
                    <th>ID NC</th>
                    <th>Descripción</th>
                    <th>Fecha Detección</th>
                    <th>Responsable Calidad</th>
                    <th>Estado</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for item in col_nc:
            html += f"""
                <tr>
                    <td>{item['IDNoConformidad']}</td>
                    <td>{item['Descripcion']}</td>
                    <td>{item['FechaDeteccion'].strftime('%d/%m/%Y') if item['FechaDeteccion'] else ''}</td>
                    <td>{item['ResponsableCalidad']}</td>
                    <td>{item['Estado']}</td>
                </tr>
            """
        
        html += """
            </tbody>
        </table>
        """
        
        return html

    def _html_indicadores_calidad(self):
        """Genera HTML para los indicadores de calidad."""
        try:
            # Obtener estadísticas
            total_nc_abiertas = self._get_count_nc_abiertas()
            total_nc_cerradas_mes = self._get_count_nc_cerradas_mes()
            total_ac_vencidas = self._get_count_ac_vencidas()
            
            html = f"""
            <table class="tabla-indicadores">
                <thead>
                    <tr>
                        <th>Indicador</th>
                        <th>Valor</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>No Conformidades Abiertas</td>
                        <td>{total_nc_abiertas}</td>
                    </tr>
                    <tr>
                        <td>No Conformidades Cerradas (Este Mes)</td>
                        <td>{total_nc_cerradas_mes}</td>
                    </tr>
                    <tr>
                        <td>Acciones Correctivas Vencidas</td>
                        <td>{total_ac_vencidas}</td>
                    </tr>
                </tbody>
            </table>
            """
            
            return html
            
        except Exception as e:
            self.logger.error(f"Error generando indicadores de calidad: {e}")
            return "<p>Error generando indicadores de calidad.</p>"

    def _get_count_nc_abiertas(self):
        """Obtiene el número de no conformidades abiertas."""
        try:
            conn = self._get_nc_connection()
            cursor = conn.cursor()
            
            sql = "SELECT COUNT(*) FROM TbNoConformidades WHERE Estado <> 'Cerrada'"
            cursor.execute(sql)
            row = cursor.fetchone()
            
            return row[0] if row else 0
            
        except Exception as e:
            self.logger.error(f"Error contando NC abiertas: {e}")
            return 0

    def _get_count_nc_cerradas_mes(self):
        """Obtiene el número de no conformidades cerradas este mes."""
        try:
            conn = self._get_nc_connection()
            cursor = conn.cursor()
            
            sql = """
                SELECT COUNT(*) 
                FROM TbNoConformidades 
                WHERE Estado = 'Cerrada' 
                AND Month(FechaCierre) = Month(Now()) 
                AND Year(FechaCierre) = Year(Now())
            """
            cursor.execute(sql)
            row = cursor.fetchone()
            
            return row[0] if row else 0
            
        except Exception as e:
            self.logger.error(f"Error contando NC cerradas este mes: {e}")
            return 0

    def _get_count_ac_vencidas(self):
        """Obtiene el número de acciones correctivas vencidas."""
        try:
            conn = self._get_nc_connection()
            cursor = conn.cursor()
            
            sql = """
                SELECT COUNT(*) 
                FROM TbNCAccionCorrectivas ac
                INNER JOIN TbNCAccionesRealizadas ar ON ac.IDAccionCorrectiva = ar.IDAccionCorrectiva
                WHERE ar.FechaFinReal IS NULL 
                AND ar.FechaFinPrevista < Now()
            """
            cursor.execute(sql)
            row = cursor.fetchone()
            
            return row[0] if row else 0
            
        except Exception as e:
            self.logger.error(f"Error contando AC vencidas: {e}")
            return 0
