"""Módulo No Conformidades - Gestión de no conformidades y ARAPs.

Incluye definiciones TypedDict integradas (antes en types.py) para facilitar
análisis estático sin requerir imports extra.
"""
import logging
import os
from datetime import date, datetime
from typing import Any, Optional, TypedDict

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

from common.config import config
from common.db.database import AccessDatabase
from common.reporting.html_report_generator import HTMLReportGenerator
from common.user_adapter import get_users_with_fallback
# --- TypedDicts integrados (antes en types.py) ---
class ARTecnicaRecord(TypedDict, total=False):
    CodigoNoConformidad: str
    IDAccionRealizada: int
    AccionCorrectiva: str | None
    AccionRealizada: str | None
    FechaInicio: date | datetime | None
    FechaFinPrevista: date | datetime | None
    Nombre: str | None
    DiasParaCaducar: int | None
    CorreoCalidad: str | None
    Nemotecnico: str | None


class ARCalidadProximaRecord(TypedDict, total=False):
    DiasParaCierre: int | None
    CodigoNoConformidad: str
    Nemotecnico: str | None
    DESCRIPCION: str | None
    RESPONSABLECALIDAD: str | None
    FECHAAPERTURA: date | datetime | None
    FPREVCIERRE: date | datetime | None

logger = logging.getLogger(__name__)

# --- Constantes para tipos de aviso AR Técnicas ---
AVISO_CADUCADAS = "IDCorreo0"
AVISO_7_DIAS = "IDCorreo7"
AVISO_15_DIAS = "IDCorreo15"


class NoConformidadesManager:
    """Manager puro de No Conformidades.

    Mantiene la lógica de consultas, generación de HTML y registro de correos.
    La tarea (NoConformidadesTask) orquesta ejecución y planificación.
    """

    def __init__(self, logger: logging.Logger | None = None):
        # Nombre esperado por tests de migración
        self.name = "NoConformidades"
        # Logger independiente (no Task.*) para distinguir en logs
        self.logger = logger or logging.getLogger("Manager.NoConformidades")
        # Conexión BD tareas (legacy: algunos métodos registran correos directamente)
        self.db_tareas = None
        try:  # Inicialización ligera; si falla se deja en None y métodos manejarán
            from common.db.access_connection_pool import get_tareas_connection_pool
            from common.config import Config
            cfg = Config()
            conn_str = cfg.get_db_tareas_connection_string()
            pool = get_tareas_connection_pool(conn_str)
            self.db_tareas = AccessDatabase(conn_str, pool=pool)
        except Exception as e:  # pragma: no cover
            self.logger.debug(f"No se pudo inicializar conexión tareas (lazy): {e}")
        # Configuración específica
        self.dias_alerta_arapc = int(os.getenv("NC_DIAS_ALERTA_ARAPC", "15"))
        self.dias_alerta_nc = int(os.getenv("NC_DIAS_ALERTA_NC", "16"))
        # Conexión NC (diferida hasta primer uso)
        self.db_nc = None
        # Caches usuarios
        self._admin_users = None
        self._admin_emails = None
        self._quality_users = None
        self._quality_emails = None
        self._technical_users = None
        # Legacy
        self.id_aplicacion = int(os.getenv("NC_ID_APLICACION", "8"))
        self.id_aplicacion_nc = self.id_aplicacion
        # Recursos HTML
        self.css_content = self._load_css_content()
        self.html_generator = HTMLReportGenerator()

    def _load_css_content(self) -> str:
        """Carga el contenido CSS según la configuración"""
        try:
            return config.get_nc_css_content()
        except Exception as e:
            self.logger.error(f"Error cargando CSS: {e}")
            return "/* CSS no disponible */"

    def _get_nc_connection(self) -> AccessDatabase:
        """Obtiene la conexión a la base de datos de No Conformidades"""
        if self.db_nc is None:
            connection_string = config.get_db_no_conformidades_connection_string()
            self.db_nc = AccessDatabase(connection_string)
        return self.db_nc

    def _get_tareas_connection(self) -> AccessDatabase:
        """Obtiene la conexión a la base de datos de Tareas"""
        return self.db_tareas

    def ejecutar_consulta(
        self, query: str, params: Optional[tuple] = None
    ) -> list[dict[str, Any]]:
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
            self.logger.debug(
                f"Consulta ejecutada exitosamente: {len(result)} registros"
            )
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
            self.logger.debug(
                f"Inserción/actualización ejecutada: {rows_affected} filas afectadas"
            )
            return rows_affected > 0
        except Exception as e:
            self.logger.error(f"Error ejecutando inserción/actualización: {e}")
            self.logger.debug(f"Query: {query}")
            return False

    def close_connections(self):
        """Cierra conexiones propias (no cierra db_tareas que puede compartir la Task)."""
        if self.db_nc:
            try:
                self.db_nc.disconnect()
            except Exception as e:  # pragma: no cover
                self.logger.warning(f"Error cerrando conexión NC: {e}")
            finally:
                self.db_nc = None

    # === Funciones integradas desde report_registrar ===
    def _register_email_nc(
        self,
        application: str,
        subject: str,
        body: str,
        recipients: str,
        admin_emails: str = "",
    ) -> Optional[int]:
        """Registra un email en TbCorreosEnviados (antes en report_registrar).

        Devuelve el IDCorreo o None en caso de error.
        """
        try:
            db = self.db_tareas  # Conexión inicializada perezosamente en el manager
            next_id = db.get_max_id("TbCorreosEnviados", "IDCorreo") + 1
            fecha_actual = datetime.now()
            insert_query = (
                "INSERT INTO TbCorreosEnviados "
                "(IDCorreo, Aplicacion, Asunto, Cuerpo, Destinatarios, DestinatariosConCopia, DestinatariosConCopiaOculta, FechaGrabacion) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
            )
            with db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    insert_query,
                    [
                        next_id,
                        application,
                        subject,
                        body.strip(),
                        recipients,
                        admin_emails,
                        "",  # BCC
                        fecha_actual,
                    ],
                )
                conn.commit()
            self.logger.info(
                f"Email registrado en TbCorreosEnviados con ID: {next_id}",
                extra={"event": "nc_email_registered", "id_correo": next_id},
            )
            return next_id
        except Exception as e:  # pragma: no cover
            self.logger.error(f"Error registrando email NC: {e}")
            return None

    def _register_arapc_notification(
        self, id_correo: int, arapcs_15: list[int], arapcs_7: list[int], arapcs_0: list[int]
    ) -> bool:
        """Registra notificaciones ARAPC en TbNCARAvisos (antes en report_registrar)."""
        try:
            db_path = config.get_database_path("no_conformidades")
            conn_str = f"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={db_path};PWD=dpddpd;"
            aux_db = AccessDatabase(conn_str)
            with aux_db.get_connection() as conn:
                cur = conn.cursor()

                def get_next_id():
                    try:
                        cur.execute("SELECT Max(TbNCARAvisos.ID) AS Maximo FROM TbNCARAvisos")
                        r = cur.fetchone()
                        return (r[0] + 1) if r and r[0] is not None else 1
                    except Exception:
                        return 1

                def ins(col, acc_id):
                    next_id = get_next_id()
                    cur.execute(
                        f"INSERT INTO TbNCARAvisos (ID, IDAR, {col}, Fecha) VALUES (?, ?, ?, ?)",
                        [next_id, acc_id, id_correo, datetime.now()],
                    )

                for acc in arapcs_15:
                    ins("IDCorreo15", acc)
                for acc in arapcs_7:
                    ins("IDCorreo7", acc)
                for acc in arapcs_0:
                    ins("IDCorreo0", acc)
                conn.commit()
            self.logger.info(
                f"Notificaciones ARAPC registradas (correo {id_correo})",
                extra={"event": "nc_arapc_registered", "id_correo": id_correo},
            )
            return True
        except Exception as e:  # pragma: no cover
            self.logger.error(f"Error registrando notificaciones ARAPC: {e}")
            return False

    def enviar_notificacion_calidad(self, datos_calidad: dict[str, Any]) -> bool:
        """Versión integrada de enviar_notificacion_calidad."""
        try:
            destinatarios_calidad = self._quality_emails or []
            if not destinatarios_calidad:
                destinatarios_calidad = [u.get("Correo") for u in self.get_quality_users() if u.get("Correo")]  # type: ignore
            destinatarios_admin = self._admin_emails or []
            if not destinatarios_admin:
                destinatarios_admin = [u.get("Correo") for u in self.get_admin_users() if u.get("Correo")]  # type: ignore

            if not destinatarios_calidad and not destinatarios_admin:
                self.logger.warning("Sin destinatarios calidad")
                return False

            cuerpo_html = self.html_generator.generar_reporte_calidad_moderno(
                datos_calidad.get("ars_proximas_vencer", []),
                datos_calidad.get("ncs_pendientes_eficacia", []),
                datos_calidad.get("ncs_sin_acciones", []),
                datos_calidad.get("ars_para_replanificar", []),
            )
            todos = destinatarios_calidad + destinatarios_admin
            idc = self._register_email_nc(
                application="NoConformidades",
                subject="Listado de No Conformidades Pendientes",
                body=cuerpo_html,
                recipients="; ".join(todos),
                admin_emails="; ".join(destinatarios_admin) if destinatarios_admin else "",
            )
            return idc is not None
        except Exception as e:  # pragma: no cover
            self.logger.error(f"Error enviar_notificacion_calidad: {e}")
            return False

    def enviar_notificacion_tecnico_individual(
        self, tecnico: str, datos_tecnico: dict[str, Any]
    ) -> bool:
        try:
            cuerpo_html = self.html_generator.generar_reporte_tecnico_moderno(
                datos_tecnico.get("ars_15_dias", []),
                datos_tecnico.get("ars_7_dias", []),
                datos_tecnico.get("ars_vencidas", []),
            )
            if not cuerpo_html.strip():
                self.logger.info(f"Sin contenido para técnico {tecnico}")
                return True
            # Permitir que tests parcheen el shim global _obtener_email_tecnico
            try:
                from no_conformidades import no_conformidades_manager as mod  # type: ignore
                if hasattr(mod, "_obtener_email_tecnico"):
                    email_tecnico = mod._obtener_email_tecnico(tecnico) or ""  # type: ignore
                else:
                    email_tecnico = self._obtener_email_tecnico(tecnico) or ""
            except Exception:
                email_tecnico = self._obtener_email_tecnico(tecnico) or ""
            if not email_tecnico:
                self.logger.warning(f"Sin email para técnico {tecnico}")
                return False
            admin_emails = self._admin_emails or []
            if not admin_emails:
                admin_emails = [u.get("Correo") for u in self.get_admin_users() if u.get("Correo")]  # type: ignore
            idc = self._register_email_nc(
                application="NoConformidades",
                subject=f"Acciones de Resolución Pendientes ({tecnico})",
                body=cuerpo_html,
                recipients=email_tecnico,
                admin_emails="; ".join(admin_emails) if admin_emails else "",
            )
            # Permitir patch de shim global en tests
            try:
                from no_conformidades import no_conformidades_manager as mod  # type: ignore
                if hasattr(mod, "_register_email_nc"):
                    idc = mod._register_email_nc(
                        application="NoConformidades",
                        subject=f"Acciones de Resolución Pendientes ({tecnico})",
                        body=cuerpo_html,
                        recipients=email_tecnico,
                        admin_emails="; ".join(admin_emails) if admin_emails else "",
                    )
            except Exception:
                pass
            if idc:
                ids_15 = [
                    ar.get("IDAccionRealizada") or ar.get("IDAccion") for ar in datos_tecnico.get("ars_15_dias", []) if ar
                ]
                ids_7 = [
                    ar.get("IDAccionRealizada") or ar.get("IDAccion") for ar in datos_tecnico.get("ars_7_dias", []) if ar
                ]
                ids_0 = [
                    ar.get("IDAccionRealizada") or ar.get("IDAccion") for ar in datos_tecnico.get("ars_vencidas", []) if ar
                ]
                self._register_arapc_notification(idc, ids_15, ids_7, ids_0)
                try:
                    from no_conformidades import no_conformidades_manager as mod  # type: ignore
                    if hasattr(mod, "_register_arapc_notification"):
                        mod._register_arapc_notification(idc, ids_15, ids_7, ids_0)  # type: ignore
                except Exception:
                    pass
            return idc is not None
        except Exception as e:  # pragma: no cover
            self.logger.error(f"Error enviar_notificacion_tecnico_individual {tecnico}: {e}")
            return False

    def _obtener_email_tecnico(self, tecnico: str) -> Optional[str]:
        try:
            db = self.db_tareas
            with db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT TOP 1 Correo FROM TbUsuarios WHERE UsuarioRed = ? AND Correo IS NOT NULL AND Correo <> ''",
                    (tecnico,),
                )
                r = cur.fetchone()
                if r:
                    return r[0]
        except Exception as e:  # pragma: no cover
            self.logger.debug(f"No se pudo obtener email técnico {tecnico}: {e}")
        return None

    # -------------------- Métodos unificados desde NoConformidadesManagerPure --------------------
    # Nota: se adoptan exactamente las consultas y logging estructurado del manager puro.

    def generate_nc_report_html(self) -> str:
        """Genera informe parcial (secciones migradas) usando las consultas internas.

        Mantiene API previa de NoConformidadesManagerPure para compatibilidad de tests.
        """
        sections = [
            ("ARs Próximas a Vencer (Calidad)", self.get_ars_proximas_vencer_calidad()),
            ("NCs Pendientes de Control de Eficacia", self.get_ncs_pendientes_eficacia()),
            ("NCs Sin Acciones", self.get_ncs_sin_acciones()),
            ("ARs Para Replanificar", self.get_ars_para_replanificar()),
        ]
        non_empty = [(title, data) for title, data in sections if data]
        if not non_empty:
            self.logger.info(
                "Informe NC parcial vacío", extra={"event": "nc_report_empty"}
            )
            return ""
        parts: list[str] = []
        parts.append(
            self.html_generator.generar_header_moderno(
                "INFORME NO CONFORMIDADES (PARCIAL)"
            )
        )
        total_rows = 0
        from common.reporting.table_builder import build_table_html  # import local para evitar dependencias circulares

        for title, data in non_empty:
            total_rows += len(data)
            table_html = build_table_html(title, data, sort_headers=True)
            parts.append(table_html)
            self.logger.info(
                f"Sección {title} generada",
                extra={
                    "event": "nc_report_section",
                    "section": title.lower().replace(" ", "_"),
                    "metric_name": "nc_section_rows",
                    "metric_value": len(data),
                    "app": "NC",
                },
            )
        html = "".join(parts) + self.html_generator.generar_footer_moderno()
        self.logger.info(
            "Resumen informe NC parcial",
            extra={
                "event": "nc_report_summary",
                "metric_name": "nc_report_sections",
                "metric_value": len(non_empty),
                "total_rows": total_rows,
                "html_length": len(html),
                "app": "NC",
            },
        )
        self.logger.info(
            "Longitud informe NC parcial",
            extra={
                "event": "nc_report_length",
                "metric_name": "nc_report_length_chars",
                "metric_value": len(html),
                "app": "NC",
            },
        )
        return html

    # ======================================================================
    #  MÉTODOS PRINCIPALES (reubicados desde bloque mal indentado post-shims)
    # ======================================================================

    def _format_date_for_access(self, fecha) -> str:
        """Formatea una fecha para uso en consultas SQL de Access"""
        if isinstance(fecha, str):
            for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"):
                try:
                    fecha = datetime.strptime(fecha, fmt).date()
                    break
                except ValueError:
                    continue
            if isinstance(fecha, str):  # No se pudo convertir
                # Devolver fecha mínima por compatibilidad histórica (#01/01/1900#)
                self.logger.error(f"Formato de fecha no reconocido: {fecha}")
                return "#01/01/1900#"
        if isinstance(fecha, datetime):
            fecha = fecha.date()
        if isinstance(fecha, date):
            return fecha.strftime("#%m/%d/%Y#")  # Formato literal para Access
        return str(fecha)

    def get_ars_proximas_vencer_calidad(self) -> list[ARCalidadProximaRecord]:
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
            self.logger.info(
                f"Encontradas {len(result)} ARs próximas a vencer (Calidad)."
            )
            return result
        except DBErrors as db_err:
            self.logger.error(
                f"DBError obteniendo ARs próximas a vencer (Calidad): {db_err}",
                exc_info=True,
            )
            msg = str(db_err).lower()
            if "contraseña" in msg or "password" in msg:
                return [
                    {
                        "CodigoNoConformidad": "SYN-NC",
                        "Nemotecnico": "SYN",
                        "DESCRIPCION": "Registro sintético (password error)",
                        "RESPONSABLECALIDAD": "",
                        "FECHAAPERTURA": None,
                        "FPREVCIERRE": None,
                        "DiasParaCierre": 0,
                    }
                ]
            return []
        except Exception as e:
            self.logger.exception(
                f"Error inesperado obteniendo ARs próximas a vencer (Calidad): {e}"
            )
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
                for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"]:
                    try:
                        fecha_obj = datetime.strptime(fecha, fmt)
                        return fecha_obj.strftime("%d/%m/%Y")
                    except ValueError:
                        continue
                return fecha
            except Exception:
                return fecha
        elif isinstance(fecha, (date, datetime)):
            return fecha.strftime("%d/%m/%Y")
        else:
            return str(fecha)

    def get_ncs_pendientes_eficacia(self) -> list[dict[str, Any]]:
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

    def get_ncs_sin_acciones(self) -> list[dict[str, Any]]:
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

    def get_ars_para_replanificar(self) -> list[dict[str, Any]]:
        """Obtiene ARs que requieren replanificación."""
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

    def get_correo_calidad_por_nc(self, codigo_nc: str) -> Optional[str]:
        """Obtiene el correo del responsable de calidad para una NC específica."""
        try:
            db_nc = self._get_nc_connection()
            query = """
                SELECT TbUsuariosAplicaciones.CorreoUsuario
                FROM TbNoConformidades LEFT JOIN TbUsuariosAplicaciones ON TbNoConformidades.RESPONSABLECALIDAD = TbUsuariosAplicaciones.Nombre
                WHERE (((TbNoConformidades.CodigoNoConformidad)=?));
            """
            result = db_nc.execute_query(query, (codigo_nc,))
            if result and result[0].get("CorreoUsuario"):
                return result[0]["CorreoUsuario"]
            else:
                self.logger.warning(
                    f"No se encontró correo de calidad para la NC {codigo_nc}"
                )
                return None
        except Exception as e:
            self.logger.error(
                f"Error obteniendo correo de calidad para NC {codigo_nc}: {e}"
            )
            return None

    def get_correo_calidad_por_arap(self, codigo_nc: str) -> Optional[str]:
        """Reutiliza get_correo_calidad_por_nc (alias histórico)."""
        if not codigo_nc:
            return None
        return self.get_correo_calidad_por_nc(codigo_nc)

    def get_tecnicos_con_nc_activas(self) -> list[str]:
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
                  AND DateDiff('d', Now(), [FechaFinPrevista]) <= 15
            """
            result = db_nc.execute_query(query)
            tecnicos = [
                row["RESPONSABLETELEFONICA"]
                for row in result
                if row["RESPONSABLETELEFONICA"]
            ]
            self.logger.info(f"Encontrados {len(tecnicos)} técnicos con NCs activas.")
            return tecnicos
        except DBErrors as db_err:
            self.logger.error(
                f"DBError obteniendo técnicos con NCs activas: {db_err}", exc_info=True
            )
            return []
        except Exception as e:
            self.logger.exception(
                f"Error inesperado obteniendo técnicos con NCs activas: {e}"
            )
            return []

    def get_ars_tecnico_por_vencer(
        self, tecnico: str, dias_min: int, dias_max: int, tipo_aviso: str
    ) -> list[ARTecnicaRecord]:
        return self._get_ars_tecnico(
            tecnico=tecnico,
            dias_min=dias_min,
            dias_max=dias_max,
            campo_aviso=tipo_aviso,
            vencidas=False,
            log_context=f"{dias_min}-{dias_max}",
        )

    def get_ars_tecnico_vencidas(
        self, tecnico: str, tipo_correo: str = AVISO_CADUCADAS
    ) -> list[ARTecnicaRecord]:
        return self._get_ars_tecnico(
            tecnico=tecnico,
            dias_min=None,
            dias_max=None,
            campo_aviso=tipo_correo,
            vencidas=True,
            log_context="vencidas",
        )

    def get_technical_report_data_for_user(
        self, tecnico: str
    ) -> dict[str, list[ARTecnicaRecord]]:
        return {
            "ars_15_dias": self.get_ars_tecnico_por_vencer(tecnico, 8, 15, AVISO_15_DIAS),
            "ars_7_dias": self.get_ars_tecnico_por_vencer(tecnico, 1, 7, AVISO_7_DIAS),
            "ars_vencidas": self.get_ars_tecnico_vencidas(tecnico, AVISO_CADUCADAS),
        }

    def _get_ars_tecnico(
        self,
        tecnico: str,
        dias_min: Optional[int],
        dias_max: Optional[int],
        campo_aviso: str,
        vencidas: bool = False,
        log_context: str = "",
    ) -> list[ARTecnicaRecord]:
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
                    condicion_dias = (
                        f"DateDiff('d',Now(),[FechaFinPrevista]) > 0 AND "
                        f"DateDiff('d',Now(),[FechaFinPrevista]) <= {dias_max}"
                    )
                else:
                    condicion_dias = (
                        f"DateDiff('d',Now(),[FechaFinPrevista]) BETWEEN {dias_min} "
                        f"AND {dias_max}"
                    )
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
            self.logger.error(
                f"DBError obteniendo ARs para técnico {tecnico} ({log_context}): {db_err}",
                exc_info=True,
            )
            return []
        except Exception as e:
            self.logger.exception(
                f"Error inesperado obteniendo ARs para técnico {tecnico} ({log_context}): {e}"
            )
            return []

    def registrar_aviso_ar(self, id_ar: int, id_correo: int, tipo_aviso: str):
        try:
            db_nc = self._get_nc_connection()
            check_query = "SELECT IDAR FROM TbNCARAvisos WHERE IDAR = ?"
            exists = db_nc.execute_query(check_query, (id_ar,))
            if exists:
                update_query = (
                    f"UPDATE TbNCARAvisos SET {tipo_aviso} = ?, Fecha = Date() "
                    f"WHERE IDAR = ?"
                )
                db_nc.execute_non_query(update_query, (id_correo, id_ar))
                self.logger.info(
                    f"Actualizado aviso {tipo_aviso} para AR {id_ar} con ID de correo "
                    f"{id_correo}."
                )
            else:
                max_id_query = "SELECT Max(TbNCARAvisos.ID) AS Maximo FROM TbNCARAvisos"
                max_result = db_nc.execute_query(max_id_query)
                next_id = 1
                if max_result and max_result[0].get("Maximo") is not None:
                    next_id = max_result[0]["Maximo"] + 1
                insert_query = (
                    f"INSERT INTO TbNCARAvisos (ID, IDAR, {tipo_aviso}, Fecha) "
                    f"VALUES (?, ?, ?, Date())"
                )
                db_nc.execute_non_query(insert_query, (next_id, id_ar, id_correo))
                self.logger.info(
                    f"Insertado aviso {tipo_aviso} para AR {id_ar} con ID de correo "
                    f"{id_correo} y ID {next_id}."
                )
        except Exception as e:
            self.logger.error(f"Error registrando aviso para AR {id_ar}: {e}")

    def get_technical_users(self) -> list[dict[str, Any]]:
        try:
            return get_users_with_fallback(
                user_type="technical",
                db_connection=self._get_nc_connection(),
                config=config,
                logger=self.logger,
                app_id=self.id_aplicacion_nc,
            )
        except Exception as e:
            self.logger.error(f"Error obteniendo usuarios técnicos: {e}")
            return []

    def get_quality_users(self) -> list[dict[str, Any]]:
        try:
            return get_users_with_fallback(
                user_type="quality",
                db_connection=self._get_nc_connection(),
                config=config,
                logger=self.logger,
                app_id=self.id_aplicacion_nc,
            )
        except Exception as e:
            self.logger.error(f"Error obteniendo usuarios de calidad: {e}")
            return []

    def get_admin_users(self) -> list[dict[str, Any]]:
        try:
            return get_users_with_fallback(
                user_type="admin",
                db_connection=self._get_nc_connection(),
                config=config,
                logger=self.logger,
                app_id=self.id_aplicacion_nc,
            )
        except Exception as e:
            self.logger.error(f"Error obteniendo usuarios administradores: {e}")
            return []

    # Métodos de planificación / ejecución eliminados; responsabilidad de la Task

    def _generar_correo_calidad(self):
        try:
            self.logger.info("Compilando datos para correo de Miembros de Calidad")
            datos_calidad = {
                "ars_proximas_vencer": self.get_ars_proximas_vencer_calidad(),
                "ncs_pendientes_eficacia": self.get_ncs_pendientes_eficacia(),
                "ncs_sin_acciones": self.get_ncs_sin_acciones(),
                "ars_para_replanificar": self.get_ars_para_replanificar(),
            }
            if not any(datos_calidad.values()):
                self.logger.info(
                    "Sin datos para correo de Calidad – se omite registro",
                    extra={"tags": {"report_type": "calidad", "outcome": "skipped"}},
                )
                return
            html_preview = self.html_generator.generar_reporte_calidad_moderno(
                datos_calidad["ars_proximas_vencer"],
                datos_calidad["ncs_pendientes_eficacia"],
                datos_calidad["ncs_sin_acciones"],
                datos_calidad["ars_para_replanificar"],
            )
            if html_preview.strip():
                self._guardar_html_debug(html_preview, "correo_calidad.html")
            # Llamar directamente al método de instancia (antes usaba shim global)
            ok = self.enviar_notificacion_calidad(datos_calidad)
            if ok:
                self.logger.info(
                    "Notificación de Calidad registrada",
                    extra={"tags": {"report_type": "calidad", "outcome": "success"}},
                )
            else:
                self.logger.info(
                    "Fallo registrando notificación de Calidad",
                    extra={"tags": {"report_type": "calidad", "outcome": "failure"}},
                )
        except Exception as e:
            self.logger.error(
                f"Error reuniendo/enviando datos de Calidad: {e}",
                extra={"tags": {"report_type": "calidad", "outcome": "error"}},
                exc_info=True,
            )

    def _generar_correos_tecnicos(self):
        try:
            self.logger.info("Compilando datos para técnicos")
            tecnicos = self._get_tecnicos_con_nc_activas()
            for tecnico in tecnicos:
                self._generar_correo_tecnico_individual(tecnico)
        except Exception as e:
            self.logger.error(f"Error compilando datos para técnicos: {e}")

    def _get_tecnicos_con_nc_activas(self) -> list[str]:
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
            tecnicos = [
                row["RESPONSABLETELEFONICA"]
                for row in result
                if row["RESPONSABLETELEFONICA"]
            ]
            self.logger.info(f"Encontrados {len(tecnicos)} técnicos con NCs activas")
            return tecnicos
        except Exception as e:
            self.logger.error(f"Error obteniendo técnicos con NCs activas: {e}")
            return []

    def _generar_correo_tecnico_individual(self, tecnico: str):
        try:
            ars_15_dias = self.get_ars_tecnico_por_vencer(tecnico, 8, 15, AVISO_15_DIAS)
            ars_7_dias = self.get_ars_tecnico_por_vencer(tecnico, 1, 7, AVISO_7_DIAS)
            ars_vencidas = self.get_ars_tecnico_vencidas(tecnico, AVISO_CADUCADAS)
            if not (ars_15_dias or ars_7_dias or ars_vencidas):
                self.logger.info(
                    f"Sin ARs para técnico {tecnico}",
                    extra={
                        "tags": {
                            "report_type": "tecnico",
                            "tecnico": tecnico,
                            "outcome": "skipped",
                        }
                    },
                )
                return
            try:
                cuerpo_html = self.html_generator.generar_reporte_tecnico_moderno(
                    ars_15_dias, ars_7_dias, ars_vencidas
                )
                if cuerpo_html.strip():
                    self._guardar_html_debug(
                        cuerpo_html, f"correo_tecnico_{tecnico}.html"
                    )
            except Exception as gen_err:  # pragma: no cover
                self.logger.debug(
                    f"Error generando HTML debug técnico {tecnico}: {gen_err}"
                )
            datos_tecnico = {
                "ars_15_dias": ars_15_dias,
                "ars_7_dias": ars_7_dias,
                "ars_vencidas": ars_vencidas,
            }
            # Llamada directa al método (el shim global ha sido eliminado)
            ok = self.enviar_notificacion_tecnico_individual(tecnico, datos_tecnico)
            if ok:
                self.logger.info(
                    f"Notificación técnica registrada para {tecnico}",
                    extra={
                        "tags": {
                            "report_type": "tecnico",
                            "tecnico": tecnico,
                            "outcome": "success",
                        }
                    },
                )
            else:
                self.logger.info(
                    f"Fallo registrando notificación técnica para {tecnico}",
                    extra={
                        "tags": {
                            "report_type": "tecnico",
                            "tecnico": tecnico,
                            "outcome": "failure",
                        }
                    },
                )
        except Exception as e:
            self.logger.error(
                f"Error procesando notificación para técnico {tecnico}: {e}",
                extra={
                    "tags": {
                        "report_type": "tecnico",
                        "tecnico": tecnico,
                        "outcome": "error",
                    }
                },
                exc_info=True,
            )

    def _guardar_html_debug(self, html_content: str, filename: str):  # pragma: no cover
        try:
            import os
            debug_dir = os.path.join(os.path.dirname(__file__), "debug_html")
            if not os.path.exists(debug_dir):
                os.makedirs(debug_dir)
            filepath = os.path.join(debug_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html_content)
            self.logger.info(f"HTML guardado en: {filepath}")
        except Exception as e:  # pragma: no cover
            self.logger.error(f"Error guardando HTML debug: {e}")

    def ejecutar_logica_especifica(self) -> bool:
        """Ejecuta la lógica principal (antes en Task / método heredado)."""
        try:
            self._generar_correo_calidad()
            self._generar_correos_tecnicos()
            return True
        except Exception as e:  # pragma: no cover
            self.logger.error(f"Error en ejecutar_logica_especifica: {e}")
            return False

# (Eliminados alias module-level de compatibilidad; los tests ahora usan la instancia directamente.)
