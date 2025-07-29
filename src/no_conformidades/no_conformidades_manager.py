"""
Gestor de No Conformidades - Conversión del legacy NoConformidades.vbs
Maneja la gestión de no conformidades, ARAPC, notificaciones y tareas relacionadas.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict

from common.database import get_database_instance
from common.config import Config
from common.utils import (
    should_execute_task, get_admin_emails_string, get_quality_emails_string,
    register_task_completion, send_email, setup_logging, hide_password_in_connection_string
)
from common.logger import setup_logger


@dataclass
class NoConformidad:
    """Representa una No Conformidad"""
    codigo: str
    nemotecnico: str
    descripcion: str
    responsable_calidad: str
    fecha_apertura: datetime
    fecha_prev_cierre: datetime
    dias_para_cierre: int = 0


@dataclass
class ARAPC:
    """Representa una Acción Correctiva/Preventiva"""
    id_accion: int
    codigo_nc: str
    descripcion: str
    responsable: str
    fecha_fin_prevista: datetime
    fecha_fin_real: Optional[datetime] = None
    dias_para_vencer: int = 0


@dataclass
class Usuario:
    """Representa un usuario del sistema"""
    usuario_red: str
    nombre: str
    correo: str


@dataclass
class UsuarioARAPCPorCaducar:
    """Representa un usuario con ARAPs por caducar"""
    responsable: str
    cantidad_arapcs: int


@dataclass
class NCProximaCaducar:
    """Representa una No Conformidad próxima a caducar por eficacia"""
    id_nc: int
    codigo_nc: str
    descripcion: str
    fecha_apertura: datetime
    id_accion: int
    descripcion_accion: str
    fecha_fin_accion: datetime
    responsable: str
    dias_transcurridos: int


class NoConformidadesManager:
    """Gestor principal de No Conformidades"""
    
    def __init__(self):
        self.config = Config()
        self.logger = setup_logger(__name__)
        
        # Bases de datos
        self.db_nc = None
        self.db_tareas = None
        
        # Configuración de días
        self.dias_alerta_arapc = 15
        self.dias_alerta_nc = 16
    
    def _formatear_fecha_access(self, fecha) -> str:
        """
        Formatea una fecha para uso en consultas SQL de Access
        Convierte fecha a formato #MM/dd/yyyy#
        """
        if isinstance(fecha, str):
            # Si ya es string, intentar parsearlo
            try:
                fecha = datetime.strptime(fecha, '%Y-%m-%d').date()
            except ValueError:
                try:
                    fecha = datetime.strptime(fecha, '%m/%d/%Y').date()
                except ValueError:
                    self.logger.error(f"Formato de fecha no reconocido: {fecha}")
                    return "#01/01/1900#"
        elif isinstance(fecha, datetime):
            fecha = fecha.date()
        elif hasattr(fecha, 'date'):
            fecha = fecha.date()
        
        # Formatear en formato Access #MM/dd/yyyy#
        return f"#{fecha.strftime('%m/%d/%Y')}#"
        
    def conectar_bases_datos(self):
        """Conecta a las bases de datos necesarias"""
        try:
            # Conexión a base de datos de No Conformidades
            nc_connection_string = self.config.get_db_no_conformidades_connection_string()
            self.logger.info(f"Conectando a BD No Conformidades: {hide_password_in_connection_string(nc_connection_string)}")
            self.db_nc = get_database_instance(nc_connection_string)
            
            # Conexión a base de datos de Tareas
            tareas_connection_string = self.config.get_db_tareas_connection_string()
            self.logger.info(f"Conectando a BD Tareas: {hide_password_in_connection_string(tareas_connection_string)}")
            self.db_tareas = get_database_instance(tareas_connection_string)
            
            self.logger.info("Conexiones a bases de datos establecidas correctamente")
            
        except Exception as e:
            self.logger.error(f"Error conectando a bases de datos: {e}")
            raise
    
    def desconectar_bases_datos(self):
        """Desconecta de las bases de datos"""
        try:
            if self.db_nc:
                self.db_nc.disconnect()
            if self.db_tareas:
                self.db_tareas.disconnect()
            self.logger.info("Conexiones a bases de datos cerradas")
        except Exception as e:
            self.logger.error(f"Error cerrando conexiones: {e}")
    
    def __enter__(self):
        """Context manager entry - conecta a las bases de datos"""
        self.conectar_bases_datos()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - desconecta de las bases de datos"""
        self.desconectar_bases_datos()
        if exc_type:
            self.logger.error(f"Error en context manager: {exc_val}")
    

    
    def obtener_nc_resueltas_pendientes_eficacia(self) -> List[NoConformidad]:
        """Obtiene NCs resueltas pendientes de control de eficacia"""
        try:
            # Calcular la fecha límite (30 días atrás desde hoy)
            from datetime import datetime, timedelta
            fecha_limite = datetime.now() - timedelta(days=30)
            fecha_limite_str = self._formatear_fecha_access(fecha_limite)
            
            sql = f"""
                SELECT DISTINCT nc.CodigoNoConformidad, nc.Nemotecnico, nc.DESCRIPCION,
                       nc.RESPONSABLECALIDAD, nc.FECHAAPERTURA, nc.FPREVCIERRE
                FROM TbNoConformidades nc
                INNER JOIN TbNCAccionCorrectivas ac ON nc.IDNoConformidad = ac.IDNoConformidad
                INNER JOIN TbNCAccionesRealizadas ar ON ac.IDAccionCorrectiva = ar.IDAccionCorrectiva
                WHERE ar.FechaFinReal IS NOT NULL 
                AND nc.ControlEficacia IS NULL
                AND ar.FechaFinReal <= {fecha_limite_str}
            """
            
            records = self.db_nc.execute_query(sql)
            ncs = []
            
            for record in records:
                nc = NoConformidad(
                    codigo=record[0] or "",
                    nemotecnico=record[1] or "",
                    descripcion=record[2] or "",
                    responsable_calidad=record[3] or "",
                    fecha_apertura=record[4] if record[4] else datetime.now(),
                    fecha_prev_cierre=record[5] if record[5] else datetime.now()
                )
                ncs.append(nc)
            
            self.logger.info(f"Encontradas {len(ncs)} NCs pendientes de control de eficacia")
            return ncs
            
        except Exception as e:
            self.logger.error(f"Error obteniendo NCs pendientes de eficacia: {e}")
            return []
    
    def obtener_arapc_proximas_vencer(self) -> List[ARAPC]:
        """
        Obtiene las ARAPs (Acciones Correctivas) próximas a vencer
        Equivalente a la función ObtenerARAPCProximasVencer del VBS original
        """
        try:
            # Obtener el valor de días de alerta desde la configuración
            import os
            from datetime import datetime, timedelta
            dias_alerta_arapc = int(os.getenv('DIAS_ALERTA_ARAPC', '7'))
            self.logger.info(f"Buscando ARAPs próximas a vencer en {dias_alerta_arapc} días")
            
            # Calcular fechas límite
            fecha_hoy = datetime.now().date()
            fecha_limite_superior = fecha_hoy + timedelta(days=dias_alerta_arapc)
            
            fecha_hoy_str = self._formatear_fecha_access(fecha_hoy)
            fecha_limite_superior_str = self._formatear_fecha_access(fecha_limite_superior)
            
            # Query SQL siguiendo la lógica del VBScript legacy - INNER JOIN con TbNCAccionesRealizadas
            sql_query = f"""
            SELECT 
                nc.IDNoConformidad,
                nc.CodigoNoConformidad,
                nc.DESCRIPCION,
                nc.FECHAAPERTURA,
                ac.IDAccionCorrectiva,
                ac.AccionCorrectiva,
                ar.FechaFinPrevista,
                ac.Responsable
            FROM TbNoConformidades nc
            INNER JOIN TbNCAccionCorrectivas ac ON nc.IDNoConformidad = ac.IDNoConformidad
            INNER JOIN TbNCAccionesRealizadas ar ON ac.IDAccionCorrectiva = ar.IDAccionCorrectiva
            WHERE ar.FechaFinReal IS NULL
                AND ar.FechaFinPrevista IS NOT NULL
                AND ar.FechaFinPrevista >= {fecha_hoy_str}
                AND ar.FechaFinPrevista <= {fecha_limite_superior_str}
            ORDER BY ar.FechaFinPrevista ASC
            """
            
            # Ejecutar la consulta
            resultados = self.db_nc.execute_query(sql_query)
            
            # Convertir resultados a objetos ARAPC y calcular días para vencer
            arapcs = []
            for row in resultados:
                fecha_fin = row[6]
                if fecha_fin:
                    if isinstance(fecha_fin, str):
                        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
                    elif hasattr(fecha_fin, 'date'):
                        fecha_fin = fecha_fin.date()
                    
                    dias_para_vencer = (fecha_fin - fecha_hoy).days
                else:
                    dias_para_vencer = 0
                
                arapc = ARAPC(
                    id_accion=row[4],
                    codigo_nc=row[1] or "",
                    descripcion=row[5] or "",
                    responsable=row[7] or "",
                    fecha_fin_prevista=row[6] if row[6] else datetime.now(),
                    dias_para_vencer=dias_para_vencer
                )
                arapcs.append(arapc)
            
            self.logger.info(f"ARAPs próximas a vencer encontradas: {len(arapcs)}")
            return arapcs
            
        except Exception as e:
            self.logger.error(f"Error obteniendo ARAPs próximas a vencer: {e}")
            return []
    
    def obtener_nc_proximas_caducar(self) -> List[NoConformidad]:
        """
        Obtiene las No Conformidades próximas a caducar por eficacia
        Equivalente a la función ObtenerNCProximasCaducar del VBS original
        """
        try:
            from datetime import datetime, timedelta
            self.logger.info("Buscando NCs próximas a caducar por eficacia")
            
            # Calcular fechas límite (entre 30 y 365 días desde la fecha final)
            fecha_hoy = datetime.now().date()
            fecha_limite_inferior = fecha_hoy - timedelta(days=365)  # Hace 365 días
            fecha_limite_superior = fecha_hoy - timedelta(days=30)   # Hace 30 días
            
            fecha_limite_inferior_str = self._formatear_fecha_access(fecha_limite_inferior)
            fecha_limite_superior_str = self._formatear_fecha_access(fecha_limite_superior)
            
            # Query SQL siguiendo la lógica del VBScript legacy - INNER JOIN con TbNCAccionesRealizadas
            sql_query = f"""
            SELECT 
                nc.IDNoConformidad,
                nc.CodigoNoConformidad,
                nc.DESCRIPCION,
                nc.FECHAAPERTURA,
                ac.IDAccionCorrectiva,
                ac.AccionCorrectiva AS DescripcionAccion,
                ar.FechaFinPrevista,
                ac.Responsable
            FROM TbNoConformidades nc
            INNER JOIN TbNCAccionCorrectivas ac ON nc.IDNoConformidad = ac.IDNoConformidad
            INNER JOIN TbNCAccionesRealizadas ar ON ac.IDAccionCorrectiva = ar.IDAccionCorrectiva
            WHERE ar.FechaFinReal IS NULL
                AND ar.FechaFinPrevista IS NOT NULL
                AND ar.FechaFinPrevista >= {fecha_limite_inferior_str}
                AND ar.FechaFinPrevista <= {fecha_limite_superior_str}
            ORDER BY ar.FechaFinPrevista ASC
            """
            
            # Ejecutar la consulta
            resultados = self.db_nc.execute_query(sql_query)
            
            # Convertir resultados a objetos NoConformidad y calcular días transcurridos
            ncs_proximas = []
            for row in resultados:
                fecha_fin = row[6]
                if fecha_fin:
                    if isinstance(fecha_fin, str):
                        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
                    elif hasattr(fecha_fin, 'date'):
                        fecha_fin = fecha_fin.date()
                    
                    dias_transcurridos = (fecha_hoy - fecha_fin).days
                else:
                    dias_transcurridos = 0
                
                nc = NoConformidad(
                    codigo=row[1] or "",
                    nemotecnico="",
                    descripcion=row[2] or "",
                    responsable_calidad=row[7] or "",
                    fecha_apertura=row[3] if row[3] else datetime.now(),
                    fecha_prev_cierre=row[6] if row[6] else datetime.now(),
                    dias_para_cierre=dias_transcurridos
                )
                ncs_proximas.append(nc)
            
            self.logger.info(f"NCs próximas a caducar encontradas: {len(ncs_proximas)}")
            return ncs_proximas
            
        except Exception as e:
            self.logger.error(f"Error obteniendo NCs próximas a caducar: {e}")
            return []
    
    def obtener_nc_registradas_sin_acciones(self) -> List[NoConformidad]:
        """
        Obtiene las No Conformidades registradas sin acciones correctivas
        Equivalente a la función ObtenerNCRegistradasSinAcciones del VBS original
        """
        try:
            from datetime import datetime, timedelta
            self.logger.info("Buscando NCs registradas sin acciones correctivas")
            
            # Calcular fecha límite basada en días de alerta
            fecha_hoy = datetime.now().date()
            fecha_limite = fecha_hoy + timedelta(days=self.dias_alerta_nc)
            fecha_limite_str = self._formatear_fecha_access(fecha_limite)
            
            # Query SQL sin DATEDIFF - usando nombres correctos de columnas
            sql_query = f"""
            SELECT 
                nc.IDNoConformidad,
                nc.CodigoNoConformidad,
                nc.Nemotecnico,
                nc.DESCRIPCION,
                nc.RESPONSABLECALIDAD,
                nc.FECHAAPERTURA,
                nc.FPREVCIERRE
            FROM TbNoConformidades nc
            LEFT JOIN TbNCAccionCorrectivas ac ON nc.IDNoConformidad = ac.IDNoConformidad
            WHERE ac.IDAccionCorrectiva IS NULL
                AND nc.FPREVCIERRE IS NOT NULL
                AND nc.FPREVCIERRE <= {fecha_limite_str}
            ORDER BY nc.FECHAAPERTURA ASC
            """
            
            # Ejecutar la consulta
            resultados = self.db_nc.execute_query(sql_query)
            
            # Convertir resultados a objetos NoConformidad y calcular días para cierre
            ncs_sin_acciones = []
            for row in resultados:
                fecha_prev_cierre = row[6]
                if fecha_prev_cierre:
                    if isinstance(fecha_prev_cierre, str):
                        fecha_prev_cierre = datetime.strptime(fecha_prev_cierre, '%Y-%m-%d').date()
                    elif hasattr(fecha_prev_cierre, 'date'):
                        fecha_prev_cierre = fecha_prev_cierre.date()
                    
                    dias_para_cierre = (fecha_prev_cierre - fecha_hoy).days
                else:
                    dias_para_cierre = 0
                
                nc = NoConformidad(
                    codigo=row[1] or "",
                    nemotecnico=row[2] or "",
                    descripcion=row[3] or "",
                    responsable_calidad=row[4] or "",
                    fecha_apertura=row[5] if row[5] else datetime.now(),
                    fecha_prev_cierre=row[6] if row[6] else datetime.now(),
                    dias_para_cierre=dias_para_cierre
                )
                ncs_sin_acciones.append(nc)
            
            self.logger.info(f"NCs registradas sin acciones encontradas: {len(ncs_sin_acciones)}")
            return ncs_sin_acciones
            
        except Exception as e:
            self.logger.error(f"Error obteniendo NCs registradas sin acciones: {e}")
            return []
    
    def obtener_usuarios_arapc_por_caducar(self) -> List[UsuarioARAPCPorCaducar]:
        """
        Obtiene los usuarios con ARAPs por caducar agrupados
        Equivalente a la función ObtenerUsuariosARAPCPorCaducar del VBS original
        """
        try:
            from datetime import datetime, timedelta
            import os
            self.logger.info("Obteniendo usuarios con ARAPs por caducar")
            
            # Obtener el valor de días de alerta desde la configuración
            dias_alerta_arapc = int(os.getenv('DIAS_ALERTA_ARAPC', '7'))
            
            # Calcular fechas límite
            fecha_hoy = datetime.now().date()
            fecha_limite_superior = fecha_hoy + timedelta(days=dias_alerta_arapc)
            
            fecha_hoy_str = self._formatear_fecha_access(fecha_hoy)
            fecha_limite_superior_str = self._formatear_fecha_access(fecha_limite_superior)
            
            # Query SQL siguiendo la lógica del VBScript legacy - INNER JOIN con TbNCAccionesRealizadas
            sql_query = f"""
            SELECT 
                nc.RESPONSABLETELEFONICA,
                COUNT(*) AS CantidadARAPs
            FROM TbNoConformidades nc
            INNER JOIN TbNCAccionCorrectivas ac ON nc.IDNoConformidad = ac.IDNoConformidad
            INNER JOIN TbNCAccionesRealizadas ar ON ac.IDAccionCorrectiva = ar.IDAccionCorrectiva
            WHERE ar.FechaFinReal IS NULL
                AND ar.FechaFinPrevista IS NOT NULL
                AND ar.FechaFinPrevista >= {fecha_hoy_str}
                AND ar.FechaFinPrevista <= {fecha_limite_superior_str}
                AND nc.RESPONSABLETELEFONICA IS NOT NULL
                AND nc.RESPONSABLETELEFONICA <> ''
            GROUP BY nc.RESPONSABLETELEFONICA
            ORDER BY CantidadARAPs DESC, nc.RESPONSABLETELEFONICA ASC
            """
            
            # Ejecutar la consulta
            resultados = self.db_nc.execute_query(sql_query)
            
            # Convertir resultados a objetos UsuarioARAPCPorCaducar
            usuarios_arapc = []
            for row in resultados:
                usuario = UsuarioARAPCPorCaducar(
                    responsable=row[0] or "",
                    cantidad_arapcs=row[1] if row[1] is not None else 0
                )
                usuarios_arapc.append(usuario)
            
            self.logger.info(f"Usuarios con ARAPs por caducar encontrados: {len(usuarios_arapc)}")
            return usuarios_arapc
            
        except Exception as e:
            self.logger.error(f"Error obteniendo usuarios con ARAPs por caducar: {e}")
            return []
    
    def obtener_arapc_usuario_por_tipo(self, usuario: str, tipo_alerta: str) -> List[Dict]:
        """
        Obtiene las ARAPs de un usuario específico por tipo de alerta
        Equivalente a la función ObtenerARAPCUsuarioPorTipo del VBS original
        """
        try:
            from datetime import datetime, timedelta
            self.logger.info(f"Obteniendo ARAPs para usuario {usuario} con tipo de alerta {tipo_alerta}")
            
            # Calcular fechas límite según el tipo de alerta
            fecha_hoy = datetime.now().date()
            
            # Query SQL siguiendo la lógica del VBScript legacy - INNER JOIN con TbNCAccionesRealizadas
            sql_query = f"""
            SELECT 
                nc.IDNoConformidad,
                nc.CodigoNoConformidad,
                nc.DESCRIPCION,
                ac.IDAccionCorrectiva,
                ac.AccionCorrectiva,
                ar.FechaFinPrevista,
                ac.Responsable
            FROM TbNoConformidades nc
            INNER JOIN TbNCAccionCorrectivas ac ON nc.IDNoConformidad = ac.IDNoConformidad
            INNER JOIN TbNCAccionesRealizadas ar ON ac.IDAccionCorrectiva = ar.IDAccionCorrectiva
            WHERE ac.Responsable = '{usuario}'
                AND ar.FechaFinReal IS NULL
                AND ar.FechaFinPrevista IS NOT NULL
            """
            
            # Agregar filtros según el tipo de alerta
            if tipo_alerta == '15':
                fecha_limite_inferior = fecha_hoy + timedelta(days=8)
                fecha_limite_superior = fecha_hoy + timedelta(days=15)
                fecha_limite_inferior_str = self._formatear_fecha_access(fecha_limite_inferior)
                fecha_limite_superior_str = self._formatear_fecha_access(fecha_limite_superior)
                sql_query += f" AND ar.FechaFinPrevista >= {fecha_limite_inferior_str} AND ar.FechaFinPrevista <= {fecha_limite_superior_str}"
            elif tipo_alerta == '7':
                fecha_limite_inferior = fecha_hoy + timedelta(days=1)
                fecha_limite_superior = fecha_hoy + timedelta(days=7)
                fecha_limite_inferior_str = self._formatear_fecha_access(fecha_limite_inferior)
                fecha_limite_superior_str = self._formatear_fecha_access(fecha_limite_superior)
                sql_query += f" AND ar.FechaFinPrevista >= {fecha_limite_inferior_str} AND ar.FechaFinPrevista <= {fecha_limite_superior_str}"
            elif tipo_alerta == '0':
                fecha_hoy_str = self._formatear_fecha_access(fecha_hoy)
                sql_query += f" AND ar.FechaFinPrevista <= {fecha_hoy_str}"
            
            sql_query += " ORDER BY ar.FechaFinPrevista ASC"
            
            # Ejecutar la consulta
            resultados = self.db_nc.execute_query(sql_query)
            
            # Convertir resultados a diccionarios y calcular días para vencer
            arapcs = []
            for row in resultados:
                fecha_fin = row[5]
                if fecha_fin:
                    if isinstance(fecha_fin, str):
                        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
                    elif hasattr(fecha_fin, 'date'):
                        fecha_fin = fecha_fin.date()
                    
                    dias_para_vencer = (fecha_fin - fecha_hoy).days
                else:
                    dias_para_vencer = 0
                
                arapc = {
                    'id_nc': row[0],
                    'codigo_nc': row[1] or "",
                    'descripcion_nc': row[2] or "",
                    'id_accion': row[3],
                    'descripcion_accion': row[4] or "",
                    'fecha_fin_prevista': row[5],
                    'responsable': row[6] or "",
                    'dias_para_vencer': dias_para_vencer
                }
                arapcs.append(arapc)
            
            self.logger.info(f"ARAPs encontradas para usuario {usuario}: {len(arapcs)}")
            return arapcs
            
        except Exception as e:
            self.logger.error(f"Error obteniendo ARAPs para usuario {usuario}: {e}")
            return []

    def obtener_correo_usuario(self, usuario_red: str) -> str:
        """Obtiene el correo electrónico de un usuario"""
        try:
            sql = """
                SELECT CorreoUsuario
                FROM TbUsuariosAplicaciones
                WHERE UsuarioRed = ?
            """
            
            records = self.db_nc.execute_query(sql, [usuario_red])
            if records and records[0] and records[0][0]:
                return records[0][0]
            
            return ""
            
        except Exception as e:
            self.logger.error(f"Error obteniendo correo del usuario {usuario_red}: {e}")
            return ""
    
    def obtener_correo_calidad_nc(self, codigo_nc: str) -> str:
        """Obtiene el correo del responsable de calidad de una NC"""
        try:
            sql = """
                SELECT u.CorreoUsuario
                FROM TbNoConformidades nc
                LEFT JOIN TbUsuariosAplicaciones u ON nc.RESPONSABLECALIDAD = u.UsuarioRed
                WHERE nc.CodigoNoConformidad = ?
            """
            
            records = self.db_nc.execute_query(sql, [codigo_nc])
            if records and records[0] and records[0][0]:
                return records[0][0]
            
            return ""
            
        except Exception as e:
            self.logger.error(f"Error obteniendo correo de calidad para NC {codigo_nc}: {e}")
            return ""
    
    def obtener_correos_calidad_multiples(self, arapcs_15: List[Dict], arapcs_0: List[Dict]) -> str:
        """Obtiene los correos de calidad únicos de múltiples ARAPs"""
        try:
            correos_unicos = set()
            
            # Procesar ARAPs de 15 días
            for arapc in arapcs_15:
                correo = self.obtener_correo_calidad_nc(arapc.get('codigo_nc', ''))
                if correo:
                    correos_unicos.add(correo)
            
            # Procesar ARAPs vencidas
            for arapc in arapcs_0:
                correo = self.obtener_correo_calidad_nc(arapc.get('codigo_nc', ''))
                if correo:
                    correos_unicos.add(correo)
            
            return ";".join(correos_unicos) if correos_unicos else ""
            
        except Exception as e:
            self.logger.error(f"Error obteniendo correos de calidad múltiples: {e}")
            return ""
    
    def marcar_aviso_arapc_enviado(self, id_accion_realizada: int, tipo_alerta: str, id_correo: int):
        """Marca un aviso ARAPC como enviado"""
        try:
            # Verificar si ya existe el registro
            sql_check = "SELECT ID FROM TbNCARAvisos WHERE IDAR = ?"
            records = self.db_nc.execute_query(sql_check, [id_accion_realizada])
            
            if records:
                # Actualizar registro existente
                if tipo_alerta == "15":
                    sql_update = "UPDATE TbNCARAvisos SET IDCorreo15 = ? WHERE IDAR = ?"
                elif tipo_alerta == "7":
                    sql_update = "UPDATE TbNCARAvisos SET IDCorreo7 = ? WHERE IDAR = ?"
                elif tipo_alerta == "0":
                    sql_update = "UPDATE TbNCARAvisos SET IDCorreo0 = ? WHERE IDAR = ?"
                else:
                    return
                
                self.db_nc.execute_query(sql_update, [id_correo, id_accion_realizada])
            else:
                # Crear nuevo registro
                nuevo_id = self.obtener_siguiente_id_avisos()
                sql_insert = "INSERT INTO TbNCARAvisos (ID, IDAR"
                values = [nuevo_id, id_accion_realizada]
                
                if tipo_alerta == "15":
                    sql_insert += ", IDCorreo15"
                    values.append(id_correo)
                elif tipo_alerta == "7":
                    sql_insert += ", IDCorreo7"
                    values.append(id_correo)
                elif tipo_alerta == "0":
                    sql_insert += ", IDCorreo0"
                    values.append(id_correo)
                
                sql_insert += ") VALUES (" + ",".join(["?"] * len(values)) + ")"
                self.db_nc.execute_query(sql_insert, values)
            
            self.logger.info(f"Aviso ARAPC marcado como enviado: ID={id_accion_realizada}, Tipo={tipo_alerta}")
            
        except Exception as e:
            self.logger.error(f"Error marcando aviso ARAPC como enviado: {e}")
    
    def obtener_siguiente_id_correo(self) -> int:
        """Obtiene el siguiente ID disponible para correos"""
        try:
            sql = "SELECT MAX(IDCorreo) AS Maximo FROM TbCorreosEnviados"
            records = self.db_tareas.execute_query(sql)
            
            if records and records[0] and records[0][0] is not None:
                return records[0][0] + 1
            
            return 1
            
        except Exception as e:
            self.logger.error(f"Error obteniendo siguiente ID de correo: {e}")
            return 1
    
    def obtener_siguiente_id_avisos(self) -> int:
        """Obtiene el siguiente ID disponible para avisos"""
        try:
            sql = "SELECT MAX(ID) AS Maximo FROM TbNCARAvisos"
            records = self.db_nc.execute_query(sql)
            
            if records and records[0] and records[0][0] is not None:
                return records[0][0] + 1
            
            return 1
            
        except Exception as e:
            self.logger.error(f"Error obteniendo siguiente ID de avisos: {e}")
            return 1
    
    def registrar_correo_enviado(self, asunto: str, cuerpo: str, destinatarios: str, 
                                correo_calidad: str = "") -> int:
        """Registra un correo como enviado en la base de datos"""
        try:
            id_correo = self.obtener_siguiente_id_correo()
            
            sql = """
                INSERT INTO TbCorreosEnviados 
                (IDCorreo, Aplicacion, Asunto, Cuerpo, Destinatarios, DestinatariosConCopiaOculta, FechaGrabacion)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            
            admin_emails = get_admin_emails_string()
            
            self.db_tareas.execute_query(sql, [
                id_correo,
                "NC",
                asunto,
                cuerpo,
                destinatarios if "@" in destinatarios else "",
                admin_emails,
                datetime.now()
            ])
            
            self.logger.info(f"Correo registrado con ID: {id_correo}")
            return id_correo
            
        except Exception as e:
            self.logger.error(f"Error registrando correo enviado: {e}")
            return 0
    
    def es_dia_entre_semana(self) -> bool:
        """Verifica si hoy es día entre semana (lunes a viernes)"""
        hoy = datetime.now().weekday()  # 0=lunes, 6=domingo
        return 0 <= hoy <= 4  # lunes a viernes
    
    def requiere_tarea_calidad(self) -> bool:
        """Determina si se requiere ejecutar la tarea de calidad (lunes)"""
        try:
            hoy = datetime.now()
            
            # Verificar si es lunes (weekday 0)
            if hoy.weekday() != 0:
                return False
            
            # Verificar última ejecución
            ultima_ejecucion = self.obtener_ultima_ejecucion_calidad()
            
            if not ultima_ejecucion:
                return True
            
            # Si ya se ejecutó hoy, no ejecutar
            if ultima_ejecucion.date() == hoy.date():
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error verificando si requiere tarea de calidad: {e}")
            return False
    
    def requiere_tarea_tecnica(self) -> bool:
        """Determina si se requiere ejecutar la tarea técnica (cada cierto número de días)"""
        try:
            dias_necesarios = 7  # Configurar según necesidades
            
            ultima_ejecucion = self.obtener_ultima_ejecucion_tecnica()
            
            if not ultima_ejecucion:
                return True
            
            dias_transcurridos = (datetime.now() - ultima_ejecucion).days
            
            return dias_transcurridos >= dias_necesarios
            
        except Exception as e:
            self.logger.error(f"Error verificando si requiere tarea técnica: {e}")
            return False
    
    def obtener_ultima_ejecucion_calidad(self) -> Optional[datetime]:
        """Obtiene la fecha de la última ejecución de tarea de calidad"""
        try:
            sql = """
                SELECT MAX(FechaEjecucion)
                FROM TbEjecucionesTareas
                WHERE TipoTarea = 'CALIDAD_NC'
            """
            
            records = self.db_tareas.execute_query(sql)
            if records and records[0] and records[0][0]:
                return records[0][0]
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error obteniendo última ejecución de calidad: {e}")
            return None
    
    def obtener_ultima_ejecucion_tecnica(self) -> Optional[datetime]:
        """Obtiene la fecha de la última ejecución de tarea técnica"""
        try:
            sql = """
                SELECT MAX(FechaEjecucion)
                FROM TbEjecucionesTareas
                WHERE TipoTarea = 'TECNICA_NC'
            """
            
            records = self.db_tareas.execute_query(sql)
            if records and records[0] and records[0][0]:
                return records[0][0]
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error obteniendo última ejecución técnica: {e}")
            return None
    
    def obtener_estadisticas_nc(self) -> Dict[str, int]:
        """Obtiene estadísticas de NCs para reportes"""
        try:
            from datetime import datetime, timedelta
            
            estadisticas = {}
            
            # Calcular fechas en Python
            fecha_hoy = datetime.now().date()
            fecha_limite = fecha_hoy - timedelta(days=30)
            
            fecha_limite_str = self._formatear_fecha_access(fecha_limite)
            fecha_hoy_str = self._formatear_fecha_access(fecha_hoy)
            
            # NCs cerradas en los últimos 30 días
            sql_cerradas = f"""
                SELECT COUNT(nc.IDNoConformidad) AS Cuenta
                FROM TbNoConformidades nc
                INNER JOIN TbNCAccionCorrectivas ac ON nc.IDNoConformidad = ac.IDNoConformidad
                INNER JOIN TbNCAccionesRealizadas ar ON ac.IDAccionCorrectiva = ar.IDAccionCorrectiva
                WHERE ar.FechaFinReal IS NOT NULL
                AND nc.FECHACIERRE >= {fecha_limite_str}
                AND nc.FECHACIERRE <= {fecha_hoy_str}
            """
            
            records = self.db_nc.execute_query(sql_cerradas)
            estadisticas['nc_cerradas'] = records[0][0] if records and records[0] else 0
            
            # NCs abiertas en los últimos 30 días
            sql_abiertas = f"""
                SELECT COUNT(IDNoConformidad) AS Cuenta
                FROM TbNoConformidades
                WHERE FECHAAPERTURA >= {fecha_limite_str}
                AND FECHAAPERTURA <= {fecha_hoy_str}
            """
            
            records = self.db_nc.execute_query(sql_abiertas)
            estadisticas['nc_abiertas'] = records[0][0] if records and records[0] else 0
            
            # Replanificaciones en los últimos 30 días
            sql_replanif = f"""
                SELECT COUNT(IDReplanificacion) AS Cuenta
                FROM TbReplanificacionesProyecto
                WHERE FechaReprogramacion >= {fecha_limite_str}
                AND FechaReprogramacion <= {fecha_hoy_str}
            """
            
            records = self.db_nc.execute_query(sql_replanif)
            estadisticas['replanificaciones'] = records[0][0] if records and records[0] else 0
            
            return estadisticas
            
        except Exception as e:
            self.logger.error(f"Error obteniendo estadísticas de NC: {e}")
            return {'nc_cerradas': 0, 'nc_abiertas': 0, 'replanificaciones': 0}