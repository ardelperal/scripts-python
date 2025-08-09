"""
Módulo No Conformidades - Gestión de no conformidades y ARAPs
Nueva versión usando la arquitectura de tareas base
"""
import logging
import os
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

# Definir tupla de errores de base de datos específicos (pyodbc) si disponible
try:  # pragma: no cover - import defensivo
    import pyodbc  # type: ignore
    DBErrors = (pyodbc.Error,)
except Exception:  # pyodbc no disponible en algunos entornos (tests, CI)
    DBErrors = tuple()

# Agregar el directorio src al path para imports
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)
if src_dir not in os.sys.path:
    os.sys.path.insert(0, src_dir)

from common.base_task import TareaDiaria
from common.config import config, Config
from common.database import AccessDatabase
from common.utils import (
    load_css_content,
    register_email_in_database, get_admin_emails_string, get_quality_emails_string,
    get_technical_emails_string
)
from common.html_report_generator import HTMLReportGenerator
from common.user_adapter import get_users_with_fallback
from .types import ARTecnicaRecord, ARCalidadProximaRecord
from .report_registrar import enviar_notificacion_calidad, enviar_notificacion_tecnico_individual

logger = logging.getLogger(__name__)

# --- Constantes para tipos de aviso AR Técnicas ---
AVISO_CADUCADAS = "IDCorreo0"
AVISO_7_DIAS = "IDCorreo7"
AVISO_15_DIAS = "IDCorreo15"


class NoConformidadesManager(TareaDiaria):
    """Manager de No Conformidades usando la nueva arquitectura"""
    
    def __init__(self):
        # Inicializar con los parámetros requeridos por TareaDiaria
        super().__init__(
            name="NoConformidades",
            script_filename="run_no_conformidades.py",
            task_names=["NCTecnico", "NCCalidad"],
            frequency_days=int(os.getenv('NC_FRECUENCIA_DIAS', '1'))
        )

        # Configuración específica
        self.dias_alerta_arapc = int(os.getenv('NC_DIAS_ALERTA_ARAPC', '15'))
        self.dias_alerta_nc = int(os.getenv('NC_DIAS_ALERTA_NC', '16'))

        # Conexiones a bases de datos
        self.db_nc = None

        # Cache para usuarios
        self._admin_users = None
        self._admin_emails = None
        self._quality_users = None
        self._quality_emails = None
        self._technical_users = None

        # CSS y generador HTML
        self.css_content = self._load_css_content()
        self.html_generator = HTMLReportGenerator()
    
    def _load_css_content(self) -> str:
        """Carga el contenido CSS según la configuración"""
        try:
            return config.get_nc_css_content()
        except Exception as e:
            self.logger.error("Error cargando CSS: {}".format(e))
            return "/* CSS no disponible */"
    
    def _get_nc_connection(self) -> AccessDatabase:
        """Obtiene la conexión a la base de datos de No Conformidades"""
        if self.db_nc is None:
            connection_string = config.get_db_no_conformidades_connection_string()
            self.db_nc = AccessDatabase(connection_string)
        return self.db_nc
    
    def _get_tareas_connection(self) -> AccessDatabase:
        """Obtiene la conexión a la base de datos de Tareas"""
        # Usar la conexión ya inicializada en BaseTask
        return self.db_tareas
    
    def ejecutar_consulta(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """
        Ejecuta una consulta SQL en la base de datos de No Conformidades
        
        Args:
            query: Consulta SQL a ejecutar
            params: Parámetros opcionales para la consulta
            
        Returns:
            Lista de diccionarios con los resultados de la consulta
        """
        try:
            db_nc = self._get_nc_connection()
            result = db_nc.execute_query(query, params)
            self.logger.debug(f"Consulta ejecutada exitosamente: {len(result)} registros")
            return result
        except Exception as e:
            self.logger.error(f"Error ejecutando consulta: {e}")
            self.logger.debug(f"Query: {query}")
            return []
    
    def ejecutar_insercion(self, query: str, params: Optional[tuple] = None) -> bool:
        """
        Ejecuta una consulta de inserción/actualización en la base de datos de No Conformidades
        
        Args:
            query: Consulta SQL de inserción/actualización
            params: Parámetros opcionales para la consulta
            
        Returns:
            True si la operación fue exitosa, False en caso contrario
        """
        try:
            db_nc = self._get_nc_connection()
            rows_affected = db_nc.execute_non_query(query, params)
            self.logger.debug(f"Inserción/actualización ejecutada: {rows_affected} filas afectadas")
            return rows_affected > 0
        except Exception as e:
            self.logger.error(f"Error ejecutando inserción/actualización: {e}")
            self.logger.debug(f"Query: {query}")
            return False

    def close_connections(self):
        """Cierra conexiones abiertas del manager."""
        super().close_connections()
        if self.db_nc:
            try:
                self.db_nc.disconnect()
            except Exception as e:  # Mantener genérica aquí; cierre no crítico
                self.logger.warning("Error cerrando conexión NC: {}".format(e))
            finally:
                self.db_nc = None

    def _format_date_for_access(self, fecha) -> str:
        """Formatea una fecha para uso en consultas SQL de Access"""
        if isinstance(fecha, str):
            for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y'):
                try:
                    fecha = datetime.strptime(fecha, fmt).date()
                    break
                except ValueError:
                    continue
            if isinstance(fecha, str):  # No se pudo convertir
                # Devolver fecha mínima por compatibilidad histórica (#01/01/1900#)
                self.logger.error("Formato de fecha no reconocido: {}".format(fecha))
                return "#01/01/1900#"
        if isinstance(fecha, datetime):
            fecha = fecha.date()
        if isinstance(fecha, date):
            return fecha.strftime('#%m/%d/%Y#')  # Formato literal para Access
        return str(fecha)
    def get_ars_proximas_vencer_calidad(self) -> List[ARCalidadProximaRecord]:
        """Obtiene las ARs próximas a vencer o vencidas para el equipo de calidad."""
        try:
            db_nc = self._get_nc_connection()
            query = """
                SELECT DISTINCT DateDiff('d',Now(),[FPREVCIERRE]) AS DiasParaCierre, 
                    TbNoConformidades.CodigoNoConformidad, TbNoConformidades.Nemotecnico, 
                    TbNoConformidades.DESCRIPCION, TbNoConformidades.RESPONSABLECALIDAD, 
                    TbNoConformidades.FECHAAPERTURA, TbNoConformidades.FPREVCIERRE
                FROM TbNoConformidades 
                INNER JOIN (TbNCAccionCorrectivas 
                  INNER JOIN TbNCAccionesRealizadas 
                  ON TbNCAccionCorrectivas.IDAccionCorrectiva = TbNCAccionesRealizadas.IDAccionCorrectiva) 
                ON TbNoConformidades.IDNoConformidad = TbNCAccionCorrectivas.IDNoConformidad 
                WHERE TbNCAccionesRealizadas.FechaFinReal IS NULL AND 
                      DateDiff('d',Now(),[FPREVCIERRE]) < 16;
            """
            result = db_nc.execute_query(query)
            self.logger.info(f"Encontradas {len(result)} ARs próximas a vencer (Calidad).")
            return result
        except DBErrors as db_err:
            self.logger.error(f"DBError obteniendo ARs próximas a vencer (Calidad): {db_err}", exc_info=True)
            return []
        except Exception as e:
            self.logger.exception(f"Error inesperado obteniendo ARs próximas a vencer (Calidad): {e}")
            return []
    

    def _get_dias_class(self, dias: int) -> str:
        """Retorna la clase CSS según los días restantes"""
        if dias <= 0:
            return "negativo"
        elif dias <= 7:
            return "critico"
        else:
            return "normal"

    def _format_date_display(self, fecha) -> str:
        """Formatea una fecha para mostrar en las tablas"""
        if fecha is None:
            return ""
        
        if isinstance(fecha, str):
            try:
                # Intentar varios formatos de fecha
                for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']:
                    try:
                        fecha_obj = datetime.strptime(fecha, fmt)
                        return fecha_obj.strftime('%d/%m/%Y')
                    except ValueError:
                        continue
                return fecha  # Si no se puede parsear, devolver como está
            except:
                return fecha
        elif isinstance(fecha, (date, datetime)):
            return fecha.strftime('%d/%m/%Y')
        else:
            return str(fecha)

    def get_ncs_pendientes_eficacia(self) -> List[Dict[str, Any]]:
        """Obtiene NCs resueltas pendientes de control de eficacia."""
        try:
            db_nc = self._get_nc_connection()
            query = """
                SELECT DISTINCT TbNoConformidades.CodigoNoConformidad, TbNoConformidades.Nemotecnico, 
                    TbNoConformidades.DESCRIPCION, TbNoConformidades.RESPONSABLECALIDAD,  
                    TbNoConformidades.FECHACIERRE, TbNoConformidades.FechaPrevistaControlEficacia,
                    DateDiff('d',Now(),[FechaPrevistaControlEficacia]) AS Dias
                FROM TbNoConformidades
                INNER JOIN (TbNCAccionCorrectivas 
                  INNER JOIN TbNCAccionesRealizadas 
                  ON TbNCAccionCorrectivas.IDAccionCorrectiva = TbNCAccionesRealizadas.IDAccionCorrectiva)
                ON TbNoConformidades.IDNoConformidad = TbNCAccionCorrectivas.IDNoConformidad
                WHERE DateDiff('d',Now(),[FechaPrevistaControlEficacia]) < 30
                  AND TbNCAccionesRealizadas.FechaFinReal IS NOT NULL
                  AND TbNoConformidades.RequiereControlEficacia = 'Sí'
                  AND TbNoConformidades.FechaControlEficacia IS NULL;
            """
            result = db_nc.execute_query(query)
            self.logger.info(f"Encontradas {len(result)} NCs pendientes de eficacia.")
            return result
        except Exception as e:
            self.logger.error(f"Error obteniendo NCs pendientes de eficacia: {e}")
            return []
    
    def get_ncs_sin_acciones(self) -> List[Dict[str, Any]]:
        """Obtiene No Conformidades sin acciones correctivas registradas."""
        try:
            db_nc = self._get_nc_connection()
            query = """
                SELECT DISTINCT TbNoConformidades.CodigoNoConformidad, TbNoConformidades.Nemotecnico,
                    TbNoConformidades.DESCRIPCION, TbNoConformidades.RESPONSABLECALIDAD, 
                    TbNoConformidades.FECHAAPERTURA, TbNoConformidades.FPREVCIERRE
                FROM TbNoConformidades
                LEFT JOIN TbNCAccionCorrectivas 
                  ON TbNoConformidades.IDNoConformidad = TbNCAccionCorrectivas.IDNoConformidad
                WHERE TbNCAccionCorrectivas.IDNoConformidad IS NULL;
            """
            result = db_nc.execute_query(query)
            self.logger.info(f"Encontradas {len(result)} NCs sin acciones.")
            return result
        except Exception as e:
            self.logger.error(f"Error obteniendo NCs sin acciones: {e}")
            return []

    def get_ars_para_replanificar(self) -> List[Dict[str, Any]]:
        """Obtiene ARs que requieren replanificación.

        Criterio: Acciones (AR) cuya FechaFinPrevista está a menos de 16 días (o pasada)
        y aún no poseen FechaFinReal (no cerradas). Se usa para alertar a Calidad sobre
        posibles retrasos o necesidad de ajuste de planificación.

        Returns:
            Lista de dicts con campos: CodigoNoConformidad, Nemotecnico, Accion, Tarea,
            Tecnico, RESPONSABLECALIDAD, FechaFinPrevista, Dias.
        """
        try:
            db_nc = self._get_nc_connection()
            query = """
                SELECT TbNoConformidades.CodigoNoConformidad, TbNoConformidades.Nemotecnico, 
                    TbNCAccionCorrectivas.AccionCorrectiva AS Accion, TbNCAccionesRealizadas.AccionRealizada AS Tarea,
                    TbUsuariosAplicaciones.Nombre AS Tecnico, TbNoConformidades.RESPONSABLECALIDAD, 
                    TbNCAccionesRealizadas.FechaFinPrevista,
                    DateDiff('d',Now(),[TbNCAccionesRealizadas].[FechaFinPrevista]) AS Dias
                FROM (TbNoConformidades 
                  INNER JOIN (TbNCAccionCorrectivas 
                    INNER JOIN TbNCAccionesRealizadas 
                    ON TbNCAccionCorrectivas.IDAccionCorrectiva = TbNCAccionesRealizadas.IDAccionCorrectiva)
                  ON TbNoConformidades.IDNoConformidad = TbNCAccionCorrectivas.IDNoConformidad)
                LEFT JOIN TbUsuariosAplicaciones 
                  ON TbNCAccionesRealizadas.Responsable = TbUsuariosAplicaciones.UsuarioRed
                WHERE DateDiff('d',Now(),[TbNCAccionesRealizadas].[FechaFinPrevista]) < 16 
                  AND TbNCAccionesRealizadas.FechaFinReal IS NULL;
            """
            result = db_nc.execute_query(query)
            self.logger.info(f"Encontradas {len(result)} ARs para replanificar.")
            return result
        except Exception as e:
            self.logger.error(f"Error obteniendo ARs para replanificar: {e}")
            return []
            
        except Exception as e:
            self.logger.error("Error obteniendo ARAPs próximas a vencer: {}".format(e))
    
    def get_correo_calidad_por_nc(self, codigo_nc: str) -> Optional[str]:
        """
        Obtiene el correo del responsable de calidad para una No Conformidad específica.
        """
        try:
            db_nc = self._get_nc_connection()

            query = """
                SELECT TbUsuariosAplicaciones.CorreoUsuario 
                FROM TbNoConformidades LEFT JOIN TbUsuariosAplicaciones ON TbNoConformidades.RESPONSABLECALIDAD = TbUsuariosAplicaciones.Nombre 
                WHERE (((TbNoConformidades.CodigoNoConformidad)=?));
            """
            
            result = db_nc.execute_query(query, (codigo_nc,))
            
            if result and result[0].get('CorreoUsuario'):
                return result[0]['CorreoUsuario']
            else:
                self.logger.warning(f"No se encontró correo de calidad para la NC {codigo_nc}")
                return None
            
        except Exception as e:
            self.logger.error(f"Error obteniendo correo de calidad para NC {codigo_nc}: {e}")
            return None

    def get_correo_calidad_por_arap(self, codigo_nc: str) -> Optional[str]:
        """Obtiene el correo del responsable de calidad a partir de un código de No Conformidad."""
        if not codigo_nc:
            return None
        
        # Simplemente reutiliza la función existente, ya que ahora tenemos el CodigoNC
        return self.get_correo_calidad_por_nc(codigo_nc)
    

    def get_tecnicos_con_nc_activas(self) -> List[str]:
        """Obtiene una lista de técnicos con NC activas y ARs pendientes."""
        try:
            db_nc = self._get_nc_connection()
            query = """
                SELECT DISTINCT TbNoConformidades.RESPONSABLETELEFONICA
                FROM (TbNoConformidades
                  INNER JOIN TbNCAccionCorrectivas ON TbNoConformidades.IDNoConformidad = TbNCAccionCorrectivas.IDNoConformidad)
                  INNER JOIN TbNCAccionesRealizadas ON TbNCAccionCorrectivas.IDAccionCorrectiva = TbNCAccionesRealizadas.IDAccionCorrectiva
                WHERE TbNCAccionesRealizadas.FechaFinReal IS NULL 
                  AND TbNoConformidades.Borrado = False 
                  AND DateDiff('d', Now(), [FechaFinPrevista]) <= 15;
            """
            result = db_nc.execute_query(query)
            tecnicos = [row['RESPONSABLETELEFONICA'] for row in result if row['RESPONSABLETELEFONICA']]
            self.logger.info(f"Encontrados {len(tecnicos)} técnicos con NCs activas.")
            return tecnicos
        except DBErrors as db_err:
            self.logger.error(f"DBError obteniendo técnicos con NCs activas: {db_err}", exc_info=True)
            return []
        except Exception as e:
            self.logger.exception(f"Error inesperado obteniendo técnicos con NCs activas: {e}")
            return []

    def get_ars_tecnico_por_vencer(self, tecnico: str, dias_min: int, dias_max: int, tipo_aviso: str) -> List[ARTecnicaRecord]:
        """Obtiene las ARs de un técnico que están por vencer en un rango de días.

        Refactorizada para reutilizar la función genérica _get_ars_tecnico.
        """
        return self._get_ars_tecnico(
            tecnico=tecnico,
            dias_min=dias_min,
            dias_max=dias_max,
            campo_aviso=tipo_aviso,
            vencidas=False,
            log_context=f"{dias_min}-{dias_max}"
        )

    def get_ars_tecnico_vencidas(self, tecnico: str, tipo_correo: str = AVISO_CADUCADAS) -> List[ARTecnicaRecord]:
        """Obtiene las ARs vencidas de un técnico (fecha fin prevista <= 0 días)."""
        return self._get_ars_tecnico(
            tecnico=tecnico,
            dias_min=None,
            dias_max=None,
            campo_aviso=tipo_correo,
            vencidas=True,
            log_context="vencidas"
        )

    # -------------------------------------------------------------
    #  MÉTODO GENÉRICO UNIFICADO PARA OBTENER ARs POR TÉCNICO
    # -------------------------------------------------------------
    def _get_ars_tecnico(
        self,
        tecnico: str,
        dias_min: Optional[int],
        dias_max: Optional[int],
        campo_aviso: str,
        vencidas: bool = False,
        log_context: str = ""
    ) -> List[ARTecnicaRecord]:
        """Obtiene ARs para un técnico según rango de días o si están vencidas.

        Args:
            tecnico: Identificador del responsable telefónica.
            dias_min: Límite inferior del rango (inclusive salvo caso especial 1-7).
            dias_max: Límite superior del rango (inclusive).
            campo_aviso: Campo de la tabla TbNCARAvisos a comprobar (IDCorreo0/7/15).
            vencidas: Si True ignora rango y usa condición <= 0.
            log_context: Texto adicional para logging (e.g. "8-15", "1-7", "vencidas").
        
        Returns:
            Lista de registros (dict) con información de AR para construcción posterior
            de reportes y/o registro de avisos.
        """
        try:
            db_nc = self._get_nc_connection()

            campo_correo_map = {
                "IDCorreo0": "TbNCARAvisos.IDCorreo0",
                "IDCorreo7": "TbNCARAvisos.IDCorreo7",
                "IDCorreo15": "TbNCARAvisos.IDCorreo15",
            }
            campo_correo = campo_correo_map.get(campo_aviso, "TbNCARAvisos.IDCorreo0")

            if vencidas:
                condicion_dias = "DateDiff('d',Now(),[FechaFinPrevista]) <= 0"
            else:
                if dias_min == 1:
                    condicion_dias = f"DateDiff('d',Now(),[FechaFinPrevista]) > 0 AND DateDiff('d',Now(),[FechaFinPrevista]) <= {dias_max}"
                else:
                    condicion_dias = f"DateDiff('d',Now(),[FechaFinPrevista]) BETWEEN {dias_min} AND {dias_max}"

            query = f"""
                SELECT DISTINCT TbNoConformidades.CodigoNoConformidad, TbNCAccionesRealizadas.IDAccionRealizada,
                    TbNCAccionCorrectivas.AccionCorrectiva, TbNCAccionesRealizadas.AccionRealizada,
                    TbNCAccionesRealizadas.FechaInicio, TbNCAccionesRealizadas.FechaFinPrevista,
                    TbUsuariosAplicaciones.Nombre, DateDiff('d',Now(),[FechaFinPrevista]) AS DiasParaCaducar,
                    TbUsuariosAplicaciones.CorreoUsuario AS CorreoCalidad, TbExpedientes.Nemotecnico
                FROM ((TbNoConformidades 
                  LEFT JOIN TbUsuariosAplicaciones ON TbNoConformidades.RESPONSABLECALIDAD = TbUsuariosAplicaciones.UsuarioRed)
                  INNER JOIN (TbNCAccionCorrectivas 
                    INNER JOIN (TbNCAccionesRealizadas 
                      LEFT JOIN TbNCARAvisos ON TbNCAccionesRealizadas.IDAccionRealizada = TbNCARAvisos.IDAR)
                    ON TbNCAccionCorrectivas.IDAccionCorrectiva = TbNCAccionesRealizadas.IDAccionCorrectiva)
                  ON TbNoConformidades.IDNoConformidad = TbNCAccionCorrectivas.IDNoConformidad)
                LEFT JOIN TbExpedientes ON TbNoConformidades.IDExpediente = TbExpedientes.IDExpediente
                WHERE TbNCAccionesRealizadas.FechaFinReal IS NULL
                  AND {condicion_dias}
                  AND {campo_correo} IS NULL
                  AND TbNoConformidades.RESPONSABLETELEFONICA = ?
            """
            result = db_nc.execute_query(query, (tecnico,))
            self.logger.info(
                f"Encontradas {len(result)} ARs para técnico {tecnico} ({log_context or 'rango'})"
            )
            return result
        except DBErrors as db_err:
            self.logger.error(f"DBError obteniendo ARs para técnico {tecnico} ({log_context}): {db_err}", exc_info=True)
            return []
        except Exception as e:
            self.logger.exception(f"Error inesperado obteniendo ARs para técnico {tecnico} ({log_context}): {e}")
            return []

    def registrar_aviso_ar(self, id_ar: int, id_correo: int, tipo_aviso: str):
        """Registra (insert/update) un aviso para una AR en TbNCARAvisos.

        Si existe fila para el IDAR se actualiza el campo del tipo de aviso; en caso
        contrario se inserta una nueva fila calculando el próximo ID secuencial.
        """
        try:
            db_nc = self._get_nc_connection()
            # Verificar si ya existe un registro para este IDAR
            check_query = "SELECT IDAR FROM TbNCARAvisos WHERE IDAR = ?"
            exists = db_nc.execute_query(check_query, (id_ar,))
            
            if exists:
                # Si existe, actualizar el campo correspondiente
                update_query = f"UPDATE TbNCARAvisos SET {tipo_aviso} = ?, Fecha = Date() WHERE IDAR = ?"
                db_nc.execute_non_query(update_query, (id_correo, id_ar))
                self.logger.info(f"Actualizado aviso {tipo_aviso} para AR {id_ar} con ID de correo {id_correo}.")
            else:
                # Si no existe, insertar un nuevo registro
                # Primero obtener el próximo ID (máximo + 1)
                max_id_query = "SELECT Max(TbNCARAvisos.ID) AS Maximo FROM TbNCARAvisos"
                max_result = db_nc.execute_query(max_id_query)
                next_id = 1  # Valor por defecto si no hay registros
                if max_result and max_result[0].get('Maximo') is not None:
                    next_id = max_result[0]['Maximo'] + 1
                
                insert_query = f"INSERT INTO TbNCARAvisos (ID, IDAR, {tipo_aviso}, Fecha) VALUES (?, ?, ?, Date())"
                db_nc.execute_non_query(insert_query, (next_id, id_ar, id_correo))
                self.logger.info(f"Insertado aviso {tipo_aviso} para AR {id_ar} con ID de correo {id_correo} y ID {next_id}.")

        except Exception as e:
            self.logger.error(f"Error registrando aviso para AR {id_ar}: {e}")
    
    # get_nc_pendientes_eficacia legacy eliminado; usar get_ncs_pendientes_eficacia
    
    # get_araps_tecnicas_proximas_a_vencer / get_araps_tecnicas_vencidas legacy eliminados
    
    def get_technical_users(self) -> List[Dict[str, Any]]:
        """
        Obtiene los usuarios técnicos usando las funciones comunes
        """
        try:
            return get_users_with_fallback(
                user_type='technical',
                db_connection=self._get_nc_connection(),
                config=config,
                logger=self.logger,
                app_id=self.id_aplicacion_nc
            )
        except Exception as e:
            self.logger.error("Error obteniendo usuarios técnicos: {}".format(e))
            return []
    
    def get_quality_users(self) -> List[Dict[str, Any]]:
        """
        Obtiene los usuarios de calidad usando las funciones comunes
        """
        try:
            return get_users_with_fallback(
                user_type='quality',
                db_connection=self._get_nc_connection(),
                config=config,
                logger=self.logger,
                app_id=self.id_aplicacion_nc
            )
        except Exception as e:
            self.logger.error("Error obteniendo usuarios de calidad: {}".format(e))
            return []
    
    def get_admin_users(self) -> List[Dict[str, Any]]:
        """
        Obtiene los usuarios administradores usando las funciones comunes
        """
        try:
            return get_users_with_fallback(
                user_type='admin',
                db_connection=self._get_nc_connection(),
                config=config,
                logger=self.logger,
                app_id=self.id_aplicacion_nc
            )
        except Exception as e:
            self.logger.error("Error obteniendo usuarios administradores: {}".format(e))
            return []
    

    # generate_quality_report_html / generate_technician_report_html eliminados (se genera directamente donde se necesitan)
    
    # Métodos legacy de generación de tablas/HTML eliminados tras unificación en HTMLReportGenerator.
    
    def should_execute_technical_task(self) -> bool:
        """
        Determina si debe ejecutarse la tarea técnica (diaria)
        """
        try:
            from src.common.utils import should_execute_task
            return should_execute_task(self.db_tareas, "NoConformidadesTecnica", 1, self.logger)
            
        except Exception as e:
            self.logger.error("Error verificando si ejecutar tarea técnica: {}".format(e))
            return False

    def should_execute_quality_task(self) -> bool:
        """
        Determina si debe ejecutarse la tarea de calidad (semanal, primer día laborable)
        """
        try:
            from src.common.utils import should_execute_weekly_task
            return should_execute_weekly_task(self.db_tareas, "NoConformidadesCalidad", logger=self.logger)
            
        except Exception as e:
            self.logger.error("Error verificando si ejecutar tarea de calidad: {}".format(e))
            return False

    def run(self) -> bool:
        """
        Método principal para ejecutar la tarea de No Conformidades
        
        Returns:
            True si se ejecutó correctamente
        """
        try:
            self.logger.info("Ejecutando tarea de No Conformidades")
            
            # Verificar si debe ejecutarse
            if not self.debe_ejecutarse():
                self.logger.info("La tarea de No Conformidades no debe ejecutarse hoy")
                return True
            
            # Ejecutar la lógica específica
            success = self.ejecutar_logica_especifica()
            
            if success:
                # Marcar como completada
                self.marcar_como_completada()
                self.logger.info("Tarea de No Conformidades completada exitosamente")
            
            return success
            
        except Exception as e:
            self.logger.error("Error ejecutando tarea de No Conformidades: {}".format(e))
            return False

    def ejecutar_logica_especifica(self) -> bool:
        """
        Ejecuta la lógica específica de la tarea de No Conformidades
        
        Returns:
            True si se ejecutó correctamente
        """
        try:
            self.logger.info("Ejecutando lógica específica de No Conformidades")
            
            # 1. Generar correo para Miembros de Calidad
            self._generar_correo_calidad()
            
            # 2. Generar correos para Técnicos
            self._generar_correos_tecnicos()
            
            self.logger.info("Lógica específica de No Conformidades ejecutada correctamente")
            return True
            
        except Exception as e:
            self.logger.error("Error en lógica específica de No Conformidades: {}".format(e))
            return False



    def _generar_correo_calidad(self):
        """Reúne datos de Calidad y delega el registro/envío de correo al registrador.

        Mantiene un guardado de debug opcional del HTML resultante para inspección.
        """
        try:
            self.logger.info("Compilando datos para correo de Miembros de Calidad")
            datos_calidad = {
                "ars_proximas_vencer": self.get_ars_proximas_vencer_calidad(),
                "ncs_pendientes_eficacia": self.get_ncs_pendientes_eficacia(),
                "ncs_sin_acciones": self.get_ncs_sin_acciones(),
                "ars_para_replanificar": self.get_ars_para_replanificar(),
            }

            if not any(datos_calidad.values()):
                self.logger.info("Sin datos para correo de Calidad – se omite registro", 
                               extra={'tags': {'report_type': 'calidad', 'outcome': 'skipped'}})
                return

            # Generar HTML únicamente para debug local (fuente de verdad está en registrar)
            html_preview = self.html_generator.generar_reporte_calidad_moderno(
                datos_calidad["ars_proximas_vencer"],
                datos_calidad["ncs_pendientes_eficacia"],
                datos_calidad["ncs_sin_acciones"],
                datos_calidad["ars_para_replanificar"],
            )
            if html_preview.strip():
                self._guardar_html_debug(html_preview, "correo_calidad.html")

            # Delegar a registrador
            ok = enviar_notificacion_calidad(datos_calidad)
            if ok:
                self.logger.info("Notificación de Calidad registrada", 
                               extra={'tags': {'report_type': 'calidad', 'outcome': 'success'}})
            else:
                self.logger.info("Fallo registrando notificación de Calidad", 
                               extra={'tags': {'report_type': 'calidad', 'outcome': 'failure'}})
        except Exception as e:
            self.logger.error(f"Error reuniendo/enviando datos de Calidad: {e}", 
                            extra={'tags': {'report_type': 'calidad', 'outcome': 'error'}}, 
                            exc_info=True)

    def _generar_correos_tecnicos(self):
        """Compila datos por técnico y delega registro/envío al registrador.

        Sustituye la versión previa que sólo generaba HTML de depuración. Ahora
        mantiene guardado opcional del HTML (debug) y usa report_registrar para
        registrar correos e insertar avisos en TbNCARAvisos.
        """
        try:
            self.logger.info("Compilando datos para técnicos")
            tecnicos = self._get_tecnicos_con_nc_activas()
            for tecnico in tecnicos:
                self._generar_correo_tecnico_individual(tecnico)
        except Exception as e:
            self.logger.error(f"Error compilando datos para técnicos: {e}")

    def _get_tecnicos_con_nc_activas(self) -> List[str]:
        """
        Obtiene la lista de técnicos que tienen al menos una NC activa con AR pendiente
        """
        try:
            db_nc = self._get_nc_connection()
            query = """
                SELECT DISTINCT TbNoConformidades.RESPONSABLETELEFONICA
                FROM (TbNoConformidades
                  INNER JOIN TbNCAccionCorrectivas ON TbNoConformidades.IDNoConformidad = TbNCAccionCorrectivas.IDNoConformidad)
                  INNER JOIN TbNCAccionesRealizadas ON TbNCAccionCorrectivas.IDAccionCorrectiva = TbNCAccionesRealizadas.IDAccionCorrectiva
                WHERE TbNCAccionesRealizadas.FechaFinReal IS NULL 
                  AND TbNoConformidades.Borrado = False 
                  AND DateDiff('d', Now(), [FechaFinPrevista]) <= 15
            """
            result = db_nc.execute_query(query)
            tecnicos = [row['RESPONSABLETELEFONICA'] for row in result if row['RESPONSABLETELEFONICA']]
            self.logger.info(f"Encontrados {len(tecnicos)} técnicos con NCs activas")
            return tecnicos
        except Exception as e:
            self.logger.error(f"Error obteniendo técnicos con NCs activas: {e}")
            return []

    def _generar_correo_tecnico_individual(self, tecnico: str):
        """Reúne ARs del técnico y delega el registro al registrador.

        Conserva el guardado de HTML para debug local.
        """
        try:
            ars_15_dias = self.get_ars_tecnico_por_vencer(tecnico, 8, 15, AVISO_15_DIAS)
            ars_7_dias = self.get_ars_tecnico_por_vencer(tecnico, 1, 7, AVISO_7_DIAS)
            ars_vencidas = self.get_ars_tecnico_vencidas(tecnico, AVISO_CADUCADAS)
            if not (ars_15_dias or ars_7_dias or ars_vencidas):
                self.logger.info(f"Sin ARs para técnico {tecnico}", 
                               extra={'tags': {'report_type': 'tecnico', 'tecnico': tecnico, 'outcome': 'skipped'}})
                return

            # Debug HTML
            try:
                cuerpo_html = self.html_generator.generar_reporte_tecnico_moderno(
                    ars_15_dias, ars_7_dias, ars_vencidas
                )
                if cuerpo_html.strip():
                    self._guardar_html_debug(cuerpo_html, f"correo_tecnico_{tecnico}.html")
            except Exception as gen_err:  # pragma: no cover - debug no crítico
                self.logger.debug(f"Error generando HTML debug técnico {tecnico}: {gen_err}")

            datos_tecnico = {
                "ars_15_dias": ars_15_dias,
                "ars_7_dias": ars_7_dias,
                "ars_vencidas": ars_vencidas,
            }
            ok = enviar_notificacion_tecnico_individual(tecnico, datos_tecnico)
            if ok:
                self.logger.info(f"Notificación técnica registrada para {tecnico}", 
                               extra={'tags': {'report_type': 'tecnico', 'tecnico': tecnico, 'outcome': 'success'}})
            else:
                self.logger.info(f"Fallo registrando notificación técnica para {tecnico}", 
                               extra={'tags': {'report_type': 'tecnico', 'tecnico': tecnico, 'outcome': 'failure'}})
        except Exception as e:
            self.logger.error(f"Error procesando notificación para técnico {tecnico}: {e}", 
                            extra={'tags': {'report_type': 'tecnico', 'tecnico': tecnico, 'outcome': 'error'}}, 
                            exc_info=True)

    # (Los métodos específicos _get_ars_tecnico_15_dias / 7_dias / vencidas fueron
    #  eliminados en favor de _get_ars_tecnico para reducir duplicación.)

    def _guardar_html_debug(self, html_content: str, filename: str):  # pragma: no cover (sólo uso manual)
        """Guarda el HTML generado en un archivo para debug"""
        try:
            import os
            debug_dir = os.path.join(os.path.dirname(__file__), "debug_html")
            if not os.path.exists(debug_dir):
                os.makedirs(debug_dir)

            filepath = os.path.join(debug_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)

            self.logger.info(f"HTML guardado en: {filepath}")
        except Exception as e:  # pragma: no cover - errores de debug no críticos
            self.logger.error(f"Error guardando HTML debug: {e}")


def main():  # pragma: no cover (entry point manual)
    """
    Función principal para ejecutar el manager directamente con argumentos
    """
    import sys
    import argparse
    
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Configurar argumentos
    parser = argparse.ArgumentParser(description='Manager de No Conformidades')
    parser.add_argument('--force-calidad', action='store_true', 
                       help='Forzar generación del correo de calidad')
    parser.add_argument('--force-tecnicos', action='store_true',
                       help='Forzar generación de correos de técnicos')
    parser.add_argument('--debug', action='store_true',
                       help='Activar modo debug')
    
    args = parser.parse_args()
    
    # Configurar nivel de logging si debug está activado
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    manager = None
    try:
        logger.info("=== INICIANDO MANAGER NO CONFORMIDADES ===")
        
        # Crear el manager
        manager = NoConformidadesManager()
        
        if args.force_calidad:
            logger.info("Ejecutando generación forzada del correo de calidad...")
            manager._generar_correo_calidad()
            
        if args.force_tecnicos:
            logger.info("Ejecutando generación forzada de correos de técnicos...")
            manager._generar_correos_tecnicos()
            
        if not args.force_calidad and not args.force_tecnicos:
            logger.info("Ejecutando lógica completa...")
            success = manager.ejecutar_logica_especifica()
            if not success:
                logger.error("Error en la ejecución de la lógica específica")
                return 1
        
        logger.info("=== MANAGER NO CONFORMIDADES COMPLETADO EXITOSAMENTE ===")
        return 0
        
    except Exception as e:
        logger.error(f"Error crítico en el manager: {e}")
        return 1
    finally:
        # Cerrar conexiones
        if manager:
            try:
                manager.close_connections()
                logger.info("Conexiones cerradas correctamente")
            except Exception as e:
                logger.warning(f"Error cerrando conexiones: {e}")


if __name__ == "__main__":
    import sys
    exit_code = main()
    sys.exit(exit_code)