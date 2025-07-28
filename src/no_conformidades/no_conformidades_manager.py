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

from ..common.database import get_database_instance
from ..common.email_sender import EmailSender
from ..common.config import Config
from ..common.logger import setup_logger


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


@dataclass
class Usuario:
    """Representa un usuario del sistema"""
    usuario_red: str
    nombre: str
    correo: str


class NoConformidadesManager:
    """Gestor principal de No Conformidades"""
    
    def __init__(self):
        self.config = Config()
        self.logger = setup_logger(__name__)
        self.email_sender = EmailSender()
        
        # Bases de datos
        self.db_nc = None
        self.db_tareas = None
        
        # Colecciones de usuarios
        self.usuarios_administradores: List[Usuario] = []
        self.usuarios_calidad: List[Usuario] = []
        self.usuarios_tecnicos: List[Usuario] = []
        
        # Configuración de días
        self.dias_alerta_arapc = 15
        self.dias_alerta_nc = 16
        
    def conectar_bases_datos(self):
        """Conecta a las bases de datos necesarias"""
        try:
            # Conexión a base de datos de No Conformidades
            nc_connection_string = self.config.get_db_no_conformidades_connection_string()
            self.db_nc = get_database_instance(nc_connection_string)
            
            # Conexión a base de datos de Tareas
            tareas_connection_string = self.config.get_db_tareas_connection_string()
            self.db_tareas = get_database_instance(tareas_connection_string)
            
            self.logger.info("Conexiones a bases de datos establecidas correctamente")
            
        except Exception as e:
            self.logger.error(f"Error conectando a bases de datos: {e}")
            raise
    
    def desconectar_bases_datos(self):
        """Desconecta de las bases de datos"""
        try:
            if self.db_nc:
                self.db_nc.close()
            if self.db_tareas:
                self.db_tareas.close()
            self.logger.info("Conexiones a bases de datos cerradas")
        except Exception as e:
            self.logger.error(f"Error cerrando conexiones: {e}")
    
    def cargar_usuarios(self):
        """Carga los usuarios del sistema por categorías"""
        try:
            # Cargar usuarios administradores
            sql_admin = """
                SELECT UsuarioRed, Nombre, CorreoUsuario 
                FROM TbUsuarios 
                WHERE EsAdministrador = True
            """
            admin_records = self.db_nc.execute_query(sql_admin)
            self.usuarios_administradores = [
                Usuario(record[0], record[1], record[2]) 
                for record in admin_records
            ]
            
            # Cargar usuarios de calidad
            sql_calidad = """
                SELECT UsuarioRed, Nombre, CorreoUsuario 
                FROM TbUsuarios 
                WHERE EsCalidad = True
            """
            calidad_records = self.db_nc.execute_query(sql_calidad)
            self.usuarios_calidad = [
                Usuario(record[0], record[1], record[2]) 
                for record in calidad_records
            ]
            
            # Cargar usuarios técnicos
            sql_tecnicos = """
                SELECT UsuarioRed, Nombre, CorreoUsuario 
                FROM TbUsuarios 
                WHERE EsTecnico = True
            """
            tecnicos_records = self.db_nc.execute_query(sql_tecnicos)
            self.usuarios_tecnicos = [
                Usuario(record[0], record[1], record[2]) 
                for record in tecnicos_records
            ]
            
            self.logger.info(f"Usuarios cargados: {len(self.usuarios_administradores)} admin, "
                           f"{len(self.usuarios_calidad)} calidad, {len(self.usuarios_tecnicos)} técnicos")
            
        except Exception as e:
            self.logger.error(f"Error cargando usuarios: {e}")
            raise
    
    def obtener_nc_resueltas_pendientes_eficacia(self) -> List[NoConformidad]:
        """Obtiene NCs resueltas pendientes de control de eficacia"""
        try:
            sql = """
                SELECT DISTINCT nc.CodigoNoConformidad, nc.Nemotecnico, nc.DESCRIPCION,
                       nc.RESPONSABLECALIDAD, nc.FECHAAPERTURA, nc.FPREVCIERRE
                FROM TbNoConformidades nc
                INNER JOIN TbNCAccionCorrectivas ac ON nc.IDNoConformidad = ac.IDNoConformidad
                INNER JOIN TbNCAccionesRealizadas ar ON ac.IDAccionCorrectiva = ar.IDAccionCorrectiva
                WHERE ar.FechaFinReal IS NOT NULL 
                AND nc.ControlEficacia IS NULL
                AND DATEDIFF('d', ar.FechaFinReal, NOW()) >= 30
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
        """Obtiene ARAPs próximas a vencer o vencidas"""
        try:
            sql = """
                SELECT ac.IDAccionCorrectiva, nc.CodigoNoConformidad, ac.DESCRIPCION,
                       ac.RESPONSABLE, ac.FECHAFINPREVISTA, ar.FechaFinReal,
                       DATEDIFF('d', NOW(), ac.FECHAFINPREVISTA) as DiasParaVencer
                FROM TbNCAccionCorrectivas ac
                INNER JOIN TbNoConformidades nc ON ac.IDNoConformidad = nc.IDNoConformidad
                LEFT JOIN TbNCAccionesRealizadas ar ON ac.IDAccionCorrectiva = ar.IDAccionCorrectiva
                WHERE ar.FechaFinReal IS NULL 
                AND DATEDIFF('d', NOW(), ac.FECHAFINPREVISTA) <= ?
            """
            
            records = self.db_nc.execute_query(sql, [self.dias_alerta_arapc])
            arapcs = []
            
            for record in records:
                arapc = ARAPC(
                    id_accion=record[0],
                    codigo_nc=record[1] or "",
                    descripcion=record[2] or "",
                    responsable=record[3] or "",
                    fecha_fin_prevista=record[4] if record[4] else datetime.now(),
                    fecha_fin_real=record[5]
                )
                arapcs.append(arapc)
            
            self.logger.info(f"Encontradas {len(arapcs)} ARAPs próximas a vencer")
            return arapcs
            
        except Exception as e:
            self.logger.error(f"Error obteniendo ARAPs próximas a vencer: {e}")
            return []
    
    def obtener_nc_proximas_caducar(self) -> List[NoConformidad]:
        """Obtiene NCs próximas a caducar o caducadas"""
        try:
            sql = """
                SELECT DISTINCT DATEDIFF('d', NOW(), nc.FPREVCIERRE) AS DiasParaCierre,
                       nc.CodigoNoConformidad, nc.Nemotecnico, nc.DESCRIPCION,
                       nc.RESPONSABLECALIDAD, nc.FECHAAPERTURA, nc.FPREVCIERRE
                FROM TbNoConformidades nc
                INNER JOIN TbNCAccionCorrectivas ac ON nc.IDNoConformidad = ac.IDNoConformidad
                INNER JOIN TbNCAccionesRealizadas ar ON ac.IDAccionCorrectiva = ar.IDAccionCorrectiva
                WHERE ar.FechaFinReal IS NULL 
                AND DATEDIFF('d', NOW(), nc.FPREVCIERRE) < ?
            """
            
            records = self.db_nc.execute_query(sql, [self.dias_alerta_nc])
            ncs = []
            
            for record in records:
                nc = NoConformidad(
                    codigo=record[1] or "",
                    nemotecnico=record[2] or "",
                    descripcion=record[3] or "",
                    responsable_calidad=record[4] or "",
                    fecha_apertura=record[5] if record[5] else datetime.now(),
                    fecha_prev_cierre=record[6] if record[6] else datetime.now(),
                    dias_para_cierre=record[0] if record[0] is not None else 0
                )
                ncs.append(nc)
            
            self.logger.info(f"Encontradas {len(ncs)} NCs próximas a caducar")
            return ncs
            
        except Exception as e:
            self.logger.error(f"Error obteniendo NCs próximas a caducar: {e}")
            return []
    
    def obtener_nc_registradas_sin_acciones(self) -> List[NoConformidad]:
        """Obtiene NCs registradas que no tienen acciones definidas"""
        try:
            sql = """
                SELECT DISTINCT nc.CodigoNoConformidad, nc.Nemotecnico, nc.DESCRIPCION,
                       nc.RESPONSABLECALIDAD, nc.FECHAAPERTURA, nc.FPREVCIERRE
                FROM TbNoConformidades nc
                LEFT JOIN TbNCAccionCorrectivas ac ON nc.IDNoConformidad = ac.IDNoConformidad
                WHERE ac.IDNoConformidad IS NULL
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
            
            self.logger.info(f"Encontradas {len(ncs)} NCs sin acciones definidas")
            return ncs
            
        except Exception as e:
            self.logger.error(f"Error obteniendo NCs sin acciones: {e}")
            return []
    
    def determinar_si_requiere_tarea_calidad(self) -> bool:
        """Determina si se requiere ejecutar la tarea de calidad"""
        try:
            # Verificar última ejecución de tarea de calidad
            sql = """
                SELECT MAX(FechaEjecucion) 
                FROM TbTareas 
                WHERE NombreTarea = 'NoConformidadesCalidad'
            """
            
            result = self.db_tareas.execute_query(sql)
            if result and result[0] and result[0][0]:
                ultima_ejecucion = result[0][0]
                dias_desde_ultima = (datetime.now() - ultima_ejecucion).days
                
                # Ejecutar cada 7 días
                requiere = dias_desde_ultima >= 7
                self.logger.info(f"Última ejecución tarea calidad: {ultima_ejecucion}, "
                               f"días transcurridos: {dias_desde_ultima}, requiere: {requiere}")
                return requiere
            else:
                # Si no hay registro previo, ejecutar
                self.logger.info("No hay registro previo de tarea de calidad, se requiere ejecutar")
                return True
                
        except Exception as e:
            self.logger.error(f"Error determinando si requiere tarea calidad: {e}")
            return True
    
    def determinar_si_requiere_tarea_tecnica(self) -> bool:
        """Determina si se requiere ejecutar la tarea técnica"""
        try:
            # Verificar última ejecución de tarea técnica
            sql = """
                SELECT MAX(FechaEjecucion) 
                FROM TbTareas 
                WHERE NombreTarea = 'NoConformidadesTecnica'
            """
            
            result = self.db_tareas.execute_query(sql)
            if result and result[0] and result[0][0]:
                ultima_ejecucion = result[0][0]
                dias_desde_ultima = (datetime.now() - ultima_ejecucion).days
                
                # Ejecutar cada 3 días
                requiere = dias_desde_ultima >= 3
                self.logger.info(f"Última ejecución tarea técnica: {ultima_ejecucion}, "
                               f"días transcurridos: {dias_desde_ultima}, requiere: {requiere}")
                return requiere
            else:
                # Si no hay registro previo, ejecutar
                self.logger.info("No hay registro previo de tarea técnica, se requiere ejecutar")
                return True
                
        except Exception as e:
            self.logger.error(f"Error determinando si requiere tarea técnica: {e}")
            return True
    
    def obtener_cadena_correos_administradores(self) -> str:
        """Obtiene la cadena de correos de administradores separados por ;"""
        if not self.usuarios_administradores:
            return ""
        
        correos = [usuario.correo for usuario in self.usuarios_administradores if usuario.correo]
        return ";".join(correos)
    
    def obtener_cadena_correos_calidad(self) -> str:
        """Obtiene la cadena de correos de calidad separados por ;"""
        if not self.usuarios_calidad:
            return ""
        
        correos = [usuario.correo for usuario in self.usuarios_calidad if usuario.correo]
        return ";".join(correos)
    
    def registrar_tarea_calidad(self):
        """Registra la ejecución de la tarea de calidad"""
        try:
            from ..common.task_manager import register_task_completion
            register_task_completion("NoConformidadesCalidad")
            self.logger.info("Tarea de calidad registrada correctamente")
        except Exception as e:
            self.logger.error(f"Error registrando tarea de calidad: {e}")
    
    def registrar_tarea_tecnica(self):
        """Registra la ejecución de la tarea técnica"""
        try:
            from ..common.task_manager import register_task_completion
            register_task_completion("NoConformidadesTecnica")
            self.logger.info("Tarea técnica registrada correctamente")
        except Exception as e:
            self.logger.error(f"Error registrando tarea técnica: {e}")