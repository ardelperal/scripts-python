"""
Script maestro de producción para ejecutar todos los scripts del sistema.

Este script reemplaza al script original script-continuo.vbs y maneja la ejecución
automática de todos los scripts de producción según horarios específicos.

Funcionalidades:
- Ejecuta tareas diarias una vez por día laborable después de las 7 AM
- Ejecuta tareas continuas (correos) en cada ciclo
- Respeta días festivos definidos en archivo configurable
- Ajusta tiempos de espera según horario (día/noche) y tipo de día (laborable/no laborable)
- Maneja señales del sistema para parada limpia
- Genera logs detallados y archivo de estado
- Configuración desde archivo .env
- Modo verbose para ver todos los detalles de ejecución

Mejoras implementadas:
- Sin delays entre scripts individuales (ejecución secuencial)
- Sistema de logging mejorado con diferentes niveles
- Configuración centralizada en .env
- Mejor manejo de errores y estado
- Modo verbose con logs detallados de todos los scripts

Uso:
    python run_master.py              # Modo normal
    python run_master.py --verbose    # Modo verbose (muestra todos los logs)
    python run_master.py -v           # Modo verbose (forma corta)

Autor: Sistema de Automatización
Fecha: 2024
"""

import argparse
import json
import logging
import os
import signal
import subprocess
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Optional

# Añadir el directorio raíz del proyecto al path para importaciones
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configurar logging básico
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MasterRunner:
    """Script maestro que ejecuta todos los scripts del sistema según horarios específicos"""
    
    def __init__(self, verbose: bool = False, single_cycle: bool = False):
        self.running = True
        self.verbose_mode = verbose
        self.single_cycle = single_cycle
        
        # Configurar rutas relativas al directorio del proyecto
        self.project_root = Path(__file__).parent.parent
        self.scripts_dir = self.project_root / "scripts"
        
        # Cargar configuración desde .env
        self._load_config()
        
        # Configurar logging específico
        self._setup_logging()
        
        # Configurar manejo de señales
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Estado de ejecución
        self.cycle_count = 0
        self.total_scripts_executed = 0
        self.successful_scripts = 0
        self.failed_scripts = 0
        
        # Configuración de threading
        self.max_workers = int(os.getenv('MASTER_MAX_WORKERS', '3'))  # Máximo 3 hilos por defecto
        self.thread_lock = threading.Lock()  # Para sincronizar acceso a estadísticas
        
        # Scripts disponibles y sus configuraciones
        self.available_scripts = {
            'correos': 'run_correos.py',
            'brass': 'run_brass.py', 
            'expedientes': 'run_expedientes.py',
            'riesgos': 'run_riesgos.py',
            'no_conformidades': 'run_no_conformidades.py',
            'agedys': 'run_agedys.py',
            'tareas': 'run_correo_tareas.py'
        }
        
        # Scripts de tareas diarias (orden de ejecución) con sus nombres de tarea en BD
        self.daily_scripts = ['riesgos', 'brass', 'expedientes', 'no_conformidades', 'agedys']
        
        # Mapeo de scripts a nombres de tareas en la base de datos
        self.script_to_task_name = {
            'agedys': 'AGEDYSDiario',
            'brass': 'BRASSDiario', 
            'expedientes': 'ExpedientesDiario',
            'no_conformidades': ['NoConformidadesCalidad', 'NoConformidadesTecnica'],
            'riesgos': ['RiesgosDiariosTecnicos', 'RiesgosSemanalesCalidad', 'RiesgosMensualesCalidad']
        }
        
        # Scripts de tareas continuas
        self.continuous_scripts = ['correos', 'tareas']
        
        # Inicializar conexión a base de datos de tareas
        self._init_database_connection()
        
        # Mostrar información de inicialización
        mode_info = "MODO VERBOSE" if self.verbose_mode else "MODO NORMAL"
        cycle_info = " - UN SOLO CICLO" if self.single_cycle else ""
        logger.info(f"🚀 Master Runner inicializado correctamente - {mode_info}{cycle_info}")
        logger.info(f"📁 Directorio de scripts: {self.scripts_dir}")
        logger.info(f"📅 Archivo de festivos: {self.festivos_file}")
        logger.info(f"⚙️  Scripts disponibles: {list(self.available_scripts.keys())}")
        logger.info(f"🧵 Máximo de hilos concurrentes: {self.max_workers}")
        
        if self.single_cycle:
            logger.info("🔄 MODO UN SOLO CICLO ACTIVADO - El script se detendrá después del primer ciclo")
        
        if self.verbose_mode:
            logger.info("🔍 MODO VERBOSE ACTIVADO - Se mostrarán todos los detalles de ejecución")
            logger.info(f"📋 Scripts diarios: {self.daily_scripts}")
            logger.info(f"📧 Scripts continuos: {self.continuous_scripts}")
            logger.info(f"🧵 Ejecución en paralelo habilitada con {self.max_workers} hilos")
    
    def _init_database_connection(self):
        """Inicializa la conexión a la base de datos de tareas"""
        try:
            # Importar las clases necesarias
            sys.path.insert(0, str(self.project_root / "src"))
            from common.config import Config
            from common.database import AccessDatabase
            
            # Cargar configuración
            self.config = Config()
            
            # Crear conexión a base de datos de tareas
            self.db_tareas = AccessDatabase(self.config.get_db_tareas_connection_string())
            
            logger.info("✅ Conexión a base de datos de tareas inicializada correctamente")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando conexión a base de datos: {e}")
            self.db_tareas = None
    
    def _is_task_completed_today(self, task_name: str) -> bool:
        """
        Verifica si una tarea debe ejecutarse basándose en su frecuencia configurada
        
        Args:
            task_name: Nombre de la tarea en la base de datos
            
        Returns:
            bool: True si NO debe ejecutarse (ya se ejecutó según su frecuencia), False si debe ejecutarse
        """
        if not self.db_tareas:
            logger.warning(f"⚠️  No hay conexión a BD, no se puede verificar tarea {task_name}")
            return False
            
        try:
            from datetime import date, timedelta
            import os
            
            # Obtener la frecuencia de la tarea desde configuración
            frecuencia_dias = self._get_task_frequency(task_name)
            
            # Consultar la última ejecución de la tarea
            query = """
                SELECT TOP 1 FechaEjecucion 
                FROM TbTareas 
                WHERE Tarea = ? 
                ORDER BY FechaEjecucion DESC
            """
            
            result = self.db_tareas.execute_query(query, [task_name])
            
            if not result:
                logger.info(f"📋 Tarea {task_name} no tiene registros previos - debe ejecutarse")
                return False
                
            last_execution_date = result[0]['FechaEjecucion']
            
            # Convertir a date si es datetime
            if hasattr(last_execution_date, 'date'):
                last_execution_date = last_execution_date.date()
            
            today = date.today()
            
            # Calcular días transcurridos desde la última ejecución
            dias_transcurridos = (today - last_execution_date).days
            
            if dias_transcurridos >= frecuencia_dias:
                logger.info(f"📅 Tarea {task_name} debe ejecutarse - Días transcurridos: {dias_transcurridos}, Frecuencia: {frecuencia_dias}")
                return False
            else:
                logger.info(f"✅ Tarea {task_name} no debe ejecutarse aún - Días transcurridos: {dias_transcurridos}, Frecuencia: {frecuencia_dias}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error verificando tarea {task_name}: {e}")
            return False
    
    def _register_task_completion_for_script(self, script_name: str):
        """
        Registra la finalización de una tarea basándose en el nombre del script
        
        Args:
            script_name: Nombre del script ejecutado
        """
        if not self.db_tareas:
            self.logger_adapter.warning(f"⚠️  No hay conexión a BD, no se puede registrar tarea para {script_name}")
            return
            
        try:
            # Importar la función común
            from common.utils import register_task_completion
            
            # Obtener el nombre de la tarea en la base de datos
            task_names = self.script_to_task_name.get(script_name)
            
            if not task_names:
                self.logger_adapter.warning(f"⚠️  No se encontró mapeo de tarea para script {script_name}")
                return
            
            # Si es una lista de tareas (como riesgos o no_conformidades)
            if isinstance(task_names, list):
                for task_name in task_names:
                    success = register_task_completion(self.db_tareas, task_name)
                    if success:
                        self.logger_adapter.info(f"✅ Tarea {task_name} registrada como completada")
                    else:
                        self.logger_adapter.error(f"❌ Error registrando tarea {task_name}")
            else:
                # Si es una sola tarea
                success = register_task_completion(self.db_tareas, task_names)
                if success:
                    self.logger_adapter.info(f"✅ Tarea {task_names} registrada como completada")
                else:
                    self.logger_adapter.error(f"❌ Error registrando tarea {task_names}")
                    
        except Exception as e:
            self.logger_adapter.error(f"❌ Error registrando finalización de tarea para {script_name}: {e}")

    def _get_task_frequency(self, task_name: str) -> int:
        """
        Obtiene la frecuencia en días para una tarea específica
        
        Args:
            task_name: Nombre de la tarea
            
        Returns:
            int: Número de días de frecuencia
        """
        # Mapeo de tareas a variables de entorno de frecuencia
        frequency_map = {
            'RiesgosDiariosTecnicos': 'RIESGOS_TECNICOS_FRECUENCIA_DIAS',
            'RiesgosSemanalesCalidad': 'RIESGOS_CALIDAD_SEMANAL_FRECUENCIA_DIAS', 
            'RiesgosMensualesCalidad': 'RIESGOS_CALIDAD_MENSUAL_FRECUENCIA_DIAS',
            'NoConformidadesCalidad': 'NO_CONFORMIDADES_DIAS_TAREA_CALIDAD',
            'NoConformidadesTecnica': 'NO_CONFORMIDADES_DIAS_TAREA_TECNICA',
            'BRASSDiario': 'BRASS_FRECUENCIA_DIAS',
            'ExpedientesDiario': 'EXPEDIENTES_FRECUENCIA_DIAS',
            'AGEDYSDiario': 'AGEDYS_FRECUENCIA_DIAS',
            'CorreoTareas': 'CORREO_TAREAS_FRECUENCIA_DIAS'
        }
        
        # Obtener variable de entorno correspondiente
        env_var = frequency_map.get(task_name)
        if env_var:
            try:
                return int(os.getenv(env_var, '1'))  # Default 1 día si no está configurado
            except ValueError:
                logger.warning(f"⚠️  Valor inválido para {env_var}, usando 1 día por defecto")
                return 1
        else:
            # Para tareas no mapeadas, usar frecuencia diaria por defecto
            logger.info(f"📋 Tarea {task_name} no tiene frecuencia configurada, usando 1 día por defecto")
            return 1

    def _load_config(self):
        """Carga la configuración desde archivo .env"""
        try:
            # Intentar cargar desde .env en la raíz del proyecto
            env_file = self.project_root / ".env"
            if env_file.exists():
                self._load_env_file(env_file)
            else:
                logger.warning("Archivo .env no encontrado, usando valores por defecto")
            
            # Configurar rutas y valores con fallbacks
            self.festivos_file = self.project_root / os.getenv('MASTER_FESTIVOS_FILE', 'herramientas/Festivos.txt')
            self.status_file = self.project_root / os.getenv('MASTER_STATUS_FILE', 'logs/run_master_status.json')
            
            # Tiempos de ciclo (en minutos)
            self.cycle_times = {
                'laborable_dia': int(os.getenv('MASTER_CYCLE_LABORABLE_DIA', '5')),
                'laborable_noche': int(os.getenv('MASTER_CYCLE_LABORABLE_NOCHE', '60')),
                'no_laborable_dia': int(os.getenv('MASTER_CYCLE_NO_LABORABLE_DIA', '60')),
                'no_laborable_noche': int(os.getenv('MASTER_CYCLE_NO_LABORABLE_NOCHE', '120'))
            }
            
            # Timeout para scripts
            self.script_timeout = int(os.getenv('MASTER_SCRIPT_TIMEOUT', '1800'))
            
            logger.info(f"⚙️  Configuración cargada: ciclos={self.cycle_times}, timeout={self.script_timeout}s")
            
        except Exception as e:
            logger.error(f"❌ Error cargando configuración: {e}")
            # Usar valores por defecto
            self.festivos_file = self.project_root / "herramientas" / "Festivos.txt"
            self.status_file = self.project_root / "logs" / "run_master_status.json"
            self.cycle_times = {
                'laborable_dia': 5,
                'laborable_noche': 60,
                'no_laborable_dia': 60,
                'no_laborable_noche': 120
            }
            self.script_timeout = 1800
    
    def _load_env_file(self, env_file: Path):
        """Carga variables de entorno desde archivo .env"""
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
        except Exception as e:
            logger.warning(f"Error leyendo archivo .env: {e}")
    
    def _setup_logging(self):
        """Configura el sistema de logging mejorado"""
        try:
            # Crear directorio de logs
            log_dir = self.project_root / "logs"
            log_dir.mkdir(exist_ok=True)
            
            # Configurar nivel de logging
            log_level = os.getenv('MASTER_LOG_LEVEL', 'INFO').upper()
            numeric_level = getattr(logging, log_level, logging.INFO)
            
            # Configurar formato detallado sin %(cycle)s para evitar KeyError
            detailed_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            
            # Configurar handler para archivo
            log_file = log_dir / os.getenv('MASTER_LOG_FILE', 'run_master.log')
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(numeric_level)
            file_handler.setFormatter(detailed_formatter)
            
            # Configurar handler para consola
            console_handler = logging.StreamHandler()
            console_handler.setLevel(numeric_level)
            console_handler.setFormatter(detailed_formatter)
            
            # Aplicar configuración al logger
            logger.handlers.clear()
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)
            logger.setLevel(numeric_level)
            
            # Usar el logger directamente sin adaptador para evitar problemas de contexto
            self.logger_adapter = logger
            
        except Exception as e:
            logger.error(f"❌ Error configurando logging: {e}")
            self.logger_adapter = logger
    
    def _update_cycle_context(self):
        """Actualiza el contexto del ciclo en el logger"""
        # Ya no necesitamos actualizar el contexto del ciclo
        # porque ahora usamos el logger directamente
        pass
    
    def es_noche(self) -> bool:
        """Determina si es horario nocturno (20:00-07:00)"""
        hora = datetime.now().hour
        return (hora >= 20) or (hora < 7)
    
    def es_laborable(self, fecha: date = None) -> bool:
        """Determina si una fecha es día laborable (no fin de semana ni festivo)"""
        if fecha is None:
            fecha = date.today()
        
        # Verificar si es fin de semana (sábado=5, domingo=6)
        if fecha.weekday() >= 5:
            return False
        
        # Verificar si es festivo
        if self.festivos_file.exists():
            try:
                with open(self.festivos_file, 'r', encoding='utf-8') as f:
                    for linea in f:
                        linea = linea.strip()
                        if fecha.strftime('%d/%m/%Y') in linea:
                            return False
            except Exception as e:
                self.logger_adapter.warning(f"Error leyendo archivo de festivos: {e}")
        
        return True
    
    def get_tiempo_espera(self) -> int:
        """Calcula el tiempo de espera según horario y tipo de día"""
        es_noche = self.es_noche()
        es_laborable = self.es_laborable()
        
        if es_laborable:
            if es_noche:
                minutos = self.cycle_times['laborable_noche']
            else:
                minutos = self.cycle_times['laborable_dia']
        else:
            if es_noche:
                minutos = self.cycle_times['no_laborable_noche']
            else:
                minutos = self.cycle_times['no_laborable_dia']
        
        return minutos * 60  # Convertir a segundos
    
    def ejecutar_script(self, script_name: str) -> Dict[str, any]:
        """
        Ejecuta un script específico y retorna información detallada del resultado
        
        Returns:
            Dict con información de la ejecución: success, duration, output, error
        """
        if script_name not in self.available_scripts:
            self.logger_adapter.error(f"Script {script_name} no disponible")
            return {
                'success': False,
                'duration': 0,
                'output': '',
                'error': f'Script {script_name} no disponible',
                'return_code': -1
            }

        script_file = self.available_scripts[script_name]
        script_path = self.scripts_dir / script_file

        if not script_path.exists():
            self.logger_adapter.warning(f"Script {script_file} no encontrado, saltando...")
            return {
                'success': False,
                'duration': 0,
                'output': '',
                'error': f'Script {script_file} no encontrado',
                'return_code': -1
            }

        try:
            # Log inicial con información detallada en modo verbose
            if self.verbose_mode:
                self.logger_adapter.info(f"🔄 INICIANDO SCRIPT: {script_name}")
                self.logger_adapter.info(f"   📄 Archivo: {script_file}")
                self.logger_adapter.info(f"   📍 Ruta completa: {script_path}")
                self.logger_adapter.info(f"   ⏰ Hora de inicio: {datetime.now().strftime('%H:%M:%S')}")
                self.logger_adapter.info(f"   🧵 Hilo: {threading.current_thread().name}")
            else:
                self.logger_adapter.info(f"▶️  Ejecutando {script_name} ({script_file}) - Hilo: {threading.current_thread().name}")

            start_time = datetime.now()

            # Ejecutar el script
            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=str(self.scripts_dir.parent),
                capture_output=True,
                text=True,
                timeout=self.script_timeout
            )

            execution_time = (datetime.now() - start_time).total_seconds()

            # Actualizar estadísticas de forma thread-safe
            with self.thread_lock:
                self.total_scripts_executed += 1

                if result.returncode == 0:
                    self.successful_scripts += 1

                    # Éxito - log detallado en modo verbose
                    if self.verbose_mode:
                        self.logger_adapter.info(f"✅ SCRIPT COMPLETADO EXITOSAMENTE: {script_name}")
                        self.logger_adapter.info(f"   ⏱️  Tiempo de ejecución: {execution_time:.2f} segundos")
                        self.logger_adapter.info(f"   📤 Código de salida: {result.returncode}")
                        self.logger_adapter.info(f"   🧵 Hilo: {threading.current_thread().name}")

                        # Mostrar stdout si hay contenido
                        if result.stdout and result.stdout.strip():
                            self.logger_adapter.info(f"   📋 SALIDA ESTÁNDAR:")
                            for line in result.stdout.strip().split('\n'):
                                self.logger_adapter.info(f"      {line}")

                        # Mostrar stderr si hay contenido (aunque sea exitoso)
                        if result.stderr and result.stderr.strip():
                            self.logger_adapter.info(f"   ⚠️  SALIDA DE ERROR:")
                            for line in result.stderr.strip().split('\n'):
                                self.logger_adapter.info(f"      {line}")
                    else:
                        self.logger_adapter.info(f"✅ {script_name} completado exitosamente en {execution_time:.1f}s")

                    # Log debug para salida del script (siempre se guarda en archivo)
                    if result.stdout and result.stdout.strip():
                        self.logger_adapter.debug(f"Output de {script_name}: {result.stdout.strip()}")
                    if result.stderr and result.stderr.strip():
                        self.logger_adapter.debug(f"Stderr de {script_name}: {result.stderr.strip()}")

                    return {
                        'success': True,
                        'duration': execution_time,
                        'output': result.stdout,
                        'error': '',
                        'return_code': result.returncode
                    }
                else:
                    self.failed_scripts += 1

                    # Error - log detallado en modo verbose
                    if self.verbose_mode:
                        self.logger_adapter.error(f"❌ SCRIPT FALLÓ: {script_name}")
                        self.logger_adapter.error(f"   ⏱️  Tiempo de ejecución: {execution_time:.2f} segundos")
                        self.logger_adapter.error(f"   📤 Código de salida: {result.returncode}")
                        self.logger_adapter.error(f"   🧵 Hilo: {threading.current_thread().name}")

                        # Mostrar stdout si hay contenido
                        if result.stdout and result.stdout.strip():
                            self.logger_adapter.error(f"   📋 SALIDA ESTÁNDAR:")
                            for line in result.stdout.strip().split('\n'):
                                self.logger_adapter.error(f"      {line}")

                        # Mostrar stderr
                        if result.stderr and result.stderr.strip():
                            self.logger_adapter.error(f"   🚨 SALIDA DE ERROR:")
                            for line in result.stderr.strip().split('\n'):
                                self.logger_adapter.error(f"      {line}")
                        else:
                            self.logger_adapter.error(f"   🚨 No hay información adicional de error")
                    else:
                        self.logger_adapter.error(f"❌ {script_name} falló con código {result.returncode} en {execution_time:.1f}s")

                    # Log completo del error
                    if result.stderr:
                        self.logger_adapter.error(f"Error stderr: {result.stderr}")
                    if result.stdout:
                        self.logger_adapter.error(f"Output stdout: {result.stdout}")

                    return {
                        'success': False,
                        'duration': execution_time,
                        'output': result.stdout,
                        'error': result.stderr,
                        'return_code': result.returncode
                    }

        except subprocess.TimeoutExpired:
            with self.thread_lock:
                self.failed_scripts += 1
                self.total_scripts_executed += 1
            execution_time = self.script_timeout

            if self.verbose_mode:
                self.logger_adapter.error(f"⏰ TIMEOUT: {script_name}")
                self.logger_adapter.error(f"   ⏱️  Tiempo transcurrido: {execution_time:.2f} segundos")
                self.logger_adapter.error(f"   🚨 El script excedió el límite de {self.script_timeout} segundos")
                self.logger_adapter.error(f"   🧵 Hilo: {threading.current_thread().name}")
            else:
                self.logger_adapter.error(f"❌ {script_name} excedió el tiempo límite de {self.script_timeout}s")

            return {
                'success': False,
                'duration': execution_time,
                'output': '',
                'error': f'Timeout después de {self.script_timeout}s',
                'return_code': -2
            }
        except Exception as e:
            with self.thread_lock:
                self.failed_scripts += 1
                self.total_scripts_executed += 1

            if self.verbose_mode:
                self.logger_adapter.error(f"💥 EXCEPCIÓN EN SCRIPT: {script_name}")
                self.logger_adapter.error(f"   🚨 Error: {str(e)}")
                self.logger_adapter.error(f"   📍 Tipo de error: {type(e).__name__}")
                self.logger_adapter.error(f"   🧵 Hilo: {threading.current_thread().name}")
            else:
                self.logger_adapter.error(f"❌ Error ejecutando {script_name}: {e}")

            return {
                'success': False,
                'duration': 0,
                'output': '',
                'error': str(e),
                'return_code': -3
            }
    
    def ejecutar_tareas_diarias(self) -> Dict[str, any]:
        """Ejecuta las tareas que se realizan una vez por día laborable usando threading"""
        if self.verbose_mode:
            self.logger_adapter.info("🌅 ===== INICIANDO TAREAS DIARIAS =====")
            self.logger_adapter.info(f"   📅 Fecha: {date.today().strftime('%d/%m/%Y')}")
            self.logger_adapter.info(f"   📝 Scripts a ejecutar: {self.daily_scripts}")
            self.logger_adapter.info(f"   🧵 Máximo de hilos: {self.max_workers}")
            self.logger_adapter.info("   " + "="*50)
        else:
            self.logger_adapter.info("🌅 ===== INICIANDO TAREAS DIARIAS =====")
        
        # Filtrar solo las tareas que no se han ejecutado hoy
        scripts_a_ejecutar = []
        for script_name in self.daily_scripts:
            task_name = self.script_to_task_name.get(script_name)
            if task_name and not self._is_task_completed_today(task_name):
                scripts_a_ejecutar.append(script_name)
            elif self.verbose_mode:
                self.logger_adapter.info(f"⏭️  Saltando {script_name} - ya ejecutado hoy")
        
        if not scripts_a_ejecutar:
            self.logger_adapter.info("✅ Todas las tareas diarias ya están completadas")
            return {}
        
        if self.verbose_mode:
            self.logger_adapter.info(f"📋 Scripts pendientes a ejecutar: {scripts_a_ejecutar}")
        
        resultados = {}
        tiempo_inicio = datetime.now()
        
        # Ejecutar scripts en paralelo usando ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=self.max_workers, thread_name_prefix="Daily") as executor:
            # Enviar todas las tareas al pool de hilos
            future_to_script = {
                executor.submit(self.ejecutar_script, script_name): script_name 
                for script_name in scripts_a_ejecutar
            }
            
            # Procesar resultados conforme van completándose
            for i, future in enumerate(as_completed(future_to_script), 1):
                script_name = future_to_script[future]
                
                try:
                    resultado = future.result()
                    resultados[script_name] = resultado
                    
                    # Si la tarea fue exitosa, registrar su finalización
                    if resultado['success']:
                        self._register_task_completion_for_script(script_name)
                    
                    if self.verbose_mode:
                        status = "✅ EXITOSO" if resultado['success'] else "❌ FALLIDO"
                        self.logger_adapter.info(f"📌 TAREA DIARIA COMPLETADA {i}/{len(scripts_a_ejecutar)}: {script_name} - {status}")
                    else:
                        status = "✅" if resultado['success'] else "❌"
                        self.logger_adapter.info(f"📋 Tarea {i}/{len(scripts_a_ejecutar)}: {script_name} {status}")
                        
                except Exception as e:
                    self.logger_adapter.error(f"❌ Error procesando resultado de {script_name}: {e}")
                    resultados[script_name] = {
                        'success': False,
                        'duration': 0,
                        'output': '',
                        'error': str(e),
                        'return_code': -4
                    }
        
        # Calcular estadísticas
        tareas_exitosas = sum(1 for r in resultados.values() if r['success'])
        total_tareas = len(scripts_a_ejecutar)
        tiempo_total = (datetime.now() - tiempo_inicio).total_seconds()
        
        # Resumen final
        if self.verbose_mode:
            self.logger_adapter.info("🌅 RESUMEN DE TAREAS DIARIAS COMPLETADO")
            self.logger_adapter.info(f"   ✅ Exitosas: {tareas_exitosas}")
            self.logger_adapter.info(f"   ❌ Fallidas: {total_tareas - tareas_exitosas}")
            self.logger_adapter.info(f"   📊 Total: {total_tareas}")
            self.logger_adapter.info(f"   ⏱️  Tiempo total: {tiempo_total:.1f}s")
            self.logger_adapter.info("   " + "="*50)
        else:
            self.logger_adapter.info(f"✅ TAREAS DIARIAS COMPLETADAS: {tareas_exitosas}/{total_tareas} exitosas en {tiempo_total:.1f}s")
        
        return {
            'success': tareas_exitosas > 0,
            'total_tasks': total_tareas,
            'successful_tasks': tareas_exitosas,
            'failed_tasks': total_tareas - tareas_exitosas,
            'duration': tiempo_total,
            'results': resultados
        }
    
    def ejecutar_tareas_continuas(self) -> Dict[str, bool]:
        """
        Ejecuta todas las tareas continuas en cada ciclo usando threading
        
        Returns:
            Dict[str, bool]: Diccionario con el resultado de cada script
        """
        if self.verbose_mode:
            self.logger_adapter.info("📧 INICIANDO EJECUCIÓN DE TAREAS CONTINUAS")
            self.logger_adapter.info(f"   🔄 Ciclo número: {self.cycle_count}")
            self.logger_adapter.info(f"   📝 Scripts a ejecutar: {self.continuous_scripts}")
            self.logger_adapter.info(f"   🧵 Máximo de hilos: {self.max_workers}")
            self.logger_adapter.info("   " + "="*50)
        else:
            self.logger_adapter.info("📧 Ejecutando tareas continuas...")
        
        results = {}
        tiempo_inicio = datetime.now()
        
        # Ejecutar scripts en paralelo usando ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=self.max_workers, thread_name_prefix="Continuous") as executor:
            # Enviar todas las tareas al pool de hilos
            future_to_script = {
                executor.submit(self.ejecutar_script, script_name): script_name 
                for script_name in self.continuous_scripts
            }
            
            # Procesar resultados conforme van completándose
            for i, future in enumerate(as_completed(future_to_script), 1):
                script_name = future_to_script[future]
                
                try:
                    resultado = future.result()
                    results[script_name] = resultado['success']
                    
                    if self.verbose_mode:
                        status = "✅ EXITOSO" if resultado['success'] else "❌ FALLIDO"
                        self.logger_adapter.info(f"📌 TAREA CONTINUA COMPLETADA {i}/{len(self.continuous_scripts)}: {script_name} - {status}")
                    else:
                        status = "✅" if resultado['success'] else "❌"
                        self.logger_adapter.info(f"📧 Tarea {i}/{len(self.continuous_scripts)}: {script_name} {status}")
                        
                except Exception as e:
                    self.logger_adapter.error(f"❌ Error procesando resultado de {script_name}: {e}")
                    results[script_name] = False
        
        # Calcular estadísticas
        successful_count = sum(1 for success in results.values() if success)
        failed_count = len(self.continuous_scripts) - successful_count
        tiempo_total = (datetime.now() - tiempo_inicio).total_seconds()
        
        # Resumen final
        if self.verbose_mode:
            self.logger_adapter.info("📧 RESUMEN DE TAREAS CONTINUAS COMPLETADO")
            self.logger_adapter.info(f"   ✅ Exitosas: {successful_count}")
            self.logger_adapter.info(f"   ❌ Fallidas: {failed_count}")
            self.logger_adapter.info(f"   📊 Total: {len(self.continuous_scripts)}")
            self.logger_adapter.info(f"   ⏱️  Tiempo total: {tiempo_total:.1f}s")
            self.logger_adapter.info("   " + "="*50)
        else:
            self.logger_adapter.info(f"📧 Tareas continuas completadas: {successful_count} exitosas, {failed_count} fallidas en {tiempo_total:.1f}s")
        
        return results
    
    def run(self):
        """Ejecuta el ciclo principal del script maestro"""
        if self.verbose_mode:
            self.logger_adapter.info("🚀 ===== INICIANDO SCRIPT MAESTRO DE PRODUCCIÓN (MODO VERBOSE) =====")
            self.logger_adapter.info(f"📁 Directorio de scripts: {self.scripts_dir}")
            self.logger_adapter.info(f"📅 Archivo de festivos: {self.festivos_file}")
            self.logger_adapter.info(f"⚙️  Configuración de ciclos: {self.cycle_times}")
            self.logger_adapter.info(f"⏰ Timeout de scripts: {self.script_timeout}s")
            self.logger_adapter.info(f"🧵 Máximo de hilos: {self.max_workers}")
            self.logger_adapter.info(f"📋 Scripts diarios: {self.daily_scripts}")
            self.logger_adapter.info(f"📧 Scripts continuos: {self.continuous_scripts}")
            self.logger_adapter.info("   " + "="*50)
        else:
            self.logger_adapter.info("🚀 ===== INICIANDO SCRIPT MAESTRO DE PRODUCCIÓN =====")
            self.logger_adapter.info(f"📁 Directorio de scripts: {self.scripts_dir}")
            self.logger_adapter.info(f"📅 Archivo de festivos: {self.festivos_file}")
            self.logger_adapter.info(f"⚙️  Configuración de ciclos: {self.cycle_times}")
            self.logger_adapter.info(f"🧵 Máximo de hilos: {self.max_workers}")
        
        try:
            while self.running:
                self.cycle_count += 1
                self._update_cycle_context()
                
                fecha_actual = date.today()
                es_laborable_hoy = self.es_laborable(fecha_actual)
                hora_actual = datetime.now().hour
                es_noche = self.es_noche()
                
                if self.verbose_mode:
                    self.logger_adapter.info(f"🔄 ===== INICIANDO CICLO {self.cycle_count} =====")
                    self.logger_adapter.info(f"📅 Fecha: {fecha_actual} | Laborable: {es_laborable_hoy} | Hora: {hora_actual:02d}:00 | Noche: {es_noche}")
                    self.logger_adapter.info(f"⏰ Hora completa: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
                    self.logger_adapter.info("   " + "="*50)
                else:
                    self.logger_adapter.info(f"🔄 ===== CICLO {self.cycle_count} =====")
                    self.logger_adapter.info(f"📅 Fecha: {fecha_actual} | Laborable: {es_laborable_hoy} | Hora: {hora_actual:02d}:00 | Noche: {es_noche}")
                
                ciclo_inicio = datetime.now()
                
                # Verificar si necesitamos ejecutar tareas diarias
                # Primero verificar condiciones básicas (día laborable y horario)
                condiciones_basicas = es_laborable_hoy and hora_actual >= 7
                
                if condiciones_basicas:
                    # Verificar si alguna tarea diaria no se ha ejecutado hoy
                    tareas_pendientes = []
                    for script_name in self.daily_scripts:
                        task_name = self.script_to_task_name.get(script_name)
                        if task_name and not self._is_task_completed_today(task_name):
                            tareas_pendientes.append(script_name)
                    
                    ejecutar_diarias = len(tareas_pendientes) > 0
                    
                    if self.verbose_mode and condiciones_basicas:
                        if tareas_pendientes:
                            self.logger_adapter.info(f"📋 Tareas pendientes de ejecutar: {tareas_pendientes}")
                        else:
                            self.logger_adapter.info("✅ Todas las tareas diarias ya se ejecutaron hoy")
                else:
                    ejecutar_diarias = False
                
                if ejecutar_diarias:
                    if self.verbose_mode:
                        self.logger_adapter.info("🌅 CONDICIONES PARA TAREAS DIARIAS CUMPLIDAS")
                        self.logger_adapter.info(f"   📅 Fecha actual: {fecha_actual}")
                        self.logger_adapter.info("   🚀 Iniciando ejecución de tareas diarias...")
                    else:
                        self.logger_adapter.info("🌅 Ejecutando tareas diarias pendientes")
                    
                    resultado_diarias = self.ejecutar_tareas_diarias()
                    
                    if self.verbose_mode:
                        self.logger_adapter.info("✅ EJECUCIÓN DE TAREAS DIARIAS COMPLETADA")
                else:
                    if self.verbose_mode:
                        self.logger_adapter.info("⏭️  SALTANDO TAREAS DIARIAS")
                        if not es_laborable_hoy:
                            self.logger_adapter.info("   📅 Razón: No es día laborable")
                        elif hora_actual < 7:
                            self.logger_adapter.info(f"   ⏰ Razón: Muy temprano (hora actual: {hora_actual:02d}:00, mínimo: 07:00)")
                        else:
                            self.logger_adapter.info("   ✅ Razón: Ya ejecutadas hoy")
                    else:
                        self.logger_adapter.info("⏭️  Saltando tareas diarias (ya ejecutadas hoy o fuera de horario)")
                
                # Ejecutar tareas continuas (siempre)
                if self.verbose_mode:
                    self.logger_adapter.info("📧 INICIANDO TAREAS CONTINUAS DEL CICLO")
                
                resultado_continuas = self.ejecutar_tareas_continuas()
                
                # Calcular tiempo total del ciclo
                tiempo_ciclo = (datetime.now() - ciclo_inicio).total_seconds()
                
                # Calcular tiempo de espera hasta el próximo ciclo
                tiempo_espera = self.get_tiempo_espera()
                
                if self.verbose_mode:
                    self.logger_adapter.info(f"📊 RESUMEN DETALLADO DEL CICLO {self.cycle_count}:")
                    self.logger_adapter.info(f"   ⏱️  Duración del ciclo: {tiempo_ciclo:.2f} segundos")
                    self.logger_adapter.info(f"   📈 Scripts ejecutados (total): {self.total_scripts_executed}")
                    self.logger_adapter.info(f"   ✅ Scripts exitosos (total): {self.successful_scripts}")
                    self.logger_adapter.info(f"   ❌ Scripts fallidos (total): {self.failed_scripts}")
                    if self.total_scripts_executed > 0:
                        success_rate = (self.successful_scripts / self.total_scripts_executed) * 100
                        self.logger_adapter.info(f"   📊 Tasa de éxito: {success_rate:.1f}%")
                    self.logger_adapter.info(f"   ⏰ Próximo ciclo en: {tiempo_espera//60} minutos ({tiempo_espera} segundos)")
                    self.logger_adapter.info("   " + "="*50)
                else:
                    self.logger_adapter.info(f"📊 RESUMEN CICLO {self.cycle_count}:")
                    self.logger_adapter.info(f"   ⏱️  Duración del ciclo: {tiempo_ciclo:.1f}s")
                    self.logger_adapter.info(f"   📈 Scripts ejecutados en total: {self.total_scripts_executed}")
                    self.logger_adapter.info(f"   ✅ Scripts exitosos: {self.successful_scripts}")
                    self.logger_adapter.info(f"   ❌ Scripts fallidos: {self.failed_scripts}")
                    self.logger_adapter.info(f"   ⏰ Próximo ciclo en: {tiempo_espera//60} minutos")
                
                # Actualizar estado
                self._actualizar_estado()
                
                # Si es modo de un solo ciclo, terminar aquí
                if self.single_cycle:
                    if self.verbose_mode:
                        self.logger_adapter.info("🔄 MODO UN SOLO CICLO COMPLETADO")
                        self.logger_adapter.info("   ✅ Ciclo único ejecutado exitosamente")
                        self.logger_adapter.info("   🛑 Terminando ejecución del script maestro")
                    else:
                        self.logger_adapter.info("🔄 Ciclo único completado, terminando ejecución")
                    break
                
                # Esperar con verificación periódica para poder responder a señales
                if self.verbose_mode:
                    self.logger_adapter.info(f"😴 ESPERANDO {tiempo_espera//60} MINUTOS HASTA EL PRÓXIMO CICLO...")
                    self.logger_adapter.info(f"   ⏰ Hora de reanudación estimada: {(datetime.now() + timedelta(seconds=tiempo_espera)).strftime('%H:%M:%S')}")
                else:
                    self.logger_adapter.info(f"😴 Esperando {tiempo_espera//60} minutos hasta el próximo ciclo...")
                
                tiempo_restante = tiempo_espera
                
                while tiempo_restante > 0 and self.running:
                    sleep_time = min(60, tiempo_restante)  # Verificar cada minuto
                    time.sleep(sleep_time)
                    tiempo_restante -= sleep_time
                    
                    # En modo verbose, mostrar progreso de espera para esperas largas
                    if self.verbose_mode and tiempo_espera > 300 and tiempo_restante > 0 and tiempo_restante % 300 == 0:
                        self.logger_adapter.info(f"⏳ Tiempo restante de espera: {tiempo_restante//60} minutos")
                    
                    # Si cambió el día, no necesitamos hacer nada especial
                    # La verificación de tareas se hace consultando la BD
                    if date.today() != fecha_actual:
                        if self.verbose_mode:
                            self.logger_adapter.info("📅 CAMBIO DE DÍA DETECTADO")
                            self.logger_adapter.info(f"   📅 Nueva fecha: {date.today()}")
                        else:
                            self.logger_adapter.info("📅 Cambio de día detectado")
                        break
                        
        except KeyboardInterrupt:
            if self.verbose_mode:
                self.logger_adapter.info("⚠️  INTERRUPCIÓN POR TECLADO DETECTADA (Ctrl+C)")
                self.logger_adapter.info("   🔄 Iniciando proceso de parada limpia...")
            else:
                self.logger_adapter.info("⚠️  Interrupción por teclado detectada")
        except Exception as e:
            if self.verbose_mode:
                self.logger_adapter.error("❌ ERROR CRÍTICO EN CICLO PRINCIPAL")
                self.logger_adapter.error(f"   🚨 Error: {e}")
                self.logger_adapter.error(f"   📍 Tipo de error: {type(e).__name__}")
                self.logger_adapter.error("   🔄 Iniciando proceso de parada de emergencia...")
            else:
                self.logger_adapter.error(f"❌ Error en ciclo principal: {e}", exc_info=True)
        finally:
            self.stop()
    
    def stop(self):
        """Detiene la ejecución del script maestro"""
        self.logger_adapter.info("🛑 Deteniendo script maestro...")
        self.running = False
        self.logger_adapter.info("✅ Script maestro detenido correctamente")
        self.logger_adapter.info(f"📊 ESTADÍSTICAS FINALES:")
        self.logger_adapter.info(f"   🔄 Ciclos completados: {self.cycle_count}")
        self.logger_adapter.info(f"   📈 Scripts ejecutados: {self.total_scripts_executed}")
        self.logger_adapter.info(f"   ✅ Scripts exitosos: {self.successful_scripts}")
        self.logger_adapter.info(f"   ❌ Scripts fallidos: {self.failed_scripts}")
    
    def _actualizar_estado(self):
        """Actualiza el archivo de estado del script maestro"""
        try:
            estado = {
                'timestamp': datetime.now().isoformat(),
                'running': self.running,
                'cycle_count': self.cycle_count,
                'fecha_actual': date.today().isoformat(),
                'es_laborable': self.es_laborable(),
                'es_noche': self.es_noche(),
                'scripts_disponibles': list(self.available_scripts.keys()),
                'proximo_tiempo_espera_minutos': self.get_tiempo_espera() // 60,
                'estadisticas': {
                    'total_scripts_executed': self.total_scripts_executed,
                    'successful_scripts': self.successful_scripts,
                    'failed_scripts': self.failed_scripts,
                    'success_rate': (self.successful_scripts / max(1, self.total_scripts_executed)) * 100
                },
                'configuracion': {
                    'cycle_times': self.cycle_times,
                    'script_timeout': self.script_timeout,
                    'festivos_file': str(self.festivos_file),
                    'daily_scripts': self.daily_scripts,
                    'continuous_scripts': self.continuous_scripts
                }
            }
            
            self.status_file.parent.mkdir(exist_ok=True)
            with open(self.status_file, 'w', encoding='utf-8') as f:
                json.dump(estado, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger_adapter.warning(f"Error actualizando estado: {e}")
    
    def _signal_handler(self, signum, frame):
        """Maneja señales del sistema para parada limpia"""
        self.logger_adapter.info(f"📡 Señal {signum} recibida, iniciando parada limpia...")
        self.stop()


def main():
    """Función principal del script maestro"""
    # Configurar argumentos de línea de comandos
    parser = argparse.ArgumentParser(
        description='Script maestro de producción para ejecutar todos los scripts del sistema',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python run_master.py                  # Modo normal (ciclo continuo)
  python run_master.py --verbose        # Modo verbose (muestra todos los logs)
  python run_master.py -v               # Modo verbose (forma corta)
  python run_master.py --single-cycle   # Ejecutar solo un ciclo y terminar
  python run_master.py -s -v            # Un solo ciclo en modo verbose
        """
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Activar modo verbose para ver todos los detalles de ejecución'
    )
    
    parser.add_argument(
        '-s', '--single-cycle',
        action='store_true',
        help='Ejecutar solo un ciclo y terminar (útil para pruebas)'
    )
    
    args = parser.parse_args()
    
    try:
        # Crear y ejecutar el script maestro
        master = MasterRunner(verbose=args.verbose, single_cycle=args.single_cycle)
        master.run()
    except Exception as e:
        logger.error(f"❌ Error fatal en main: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
