"""
Script maestro de producción para ejecutar todos los scripts del sistema.
[...]
"""

import argparse
import json
import logging
import os
import signal
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta
from pathlib import Path

# --- MODIFICACIÓN AQUÍ ---
# Centralizamos la configuración del logging al inicio para capturar todo.
def setup_global_logging(log_level_str: str = 'INFO'):
    """Configura el logging para escribir en consola y en un archivo."""
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "app.log" # Nombre de archivo genérico que Promtail vigilará

    log_level = getattr(logging, log_level_str.upper(), logging.INFO)

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout) # Mantenemos el log en consola
        ]
    )
    # Silenciar logs muy verbosos de librerías de terceros si es necesario
    # logging.getLogger("urllib3").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


############################################################
# MODO SIMPLE (Nueva arquitectura de tareas - ejecución única)
############################################################
class SimpleMasterTaskRunner:
    """Ejecutor maestro simplificado usando el registro de BaseTask."""
    def __init__(self):
        # El logging ya está configurado globalmente, solo obtenemos el logger.
        self.logger = logging.getLogger(f"{__name__}.SimpleMasterTaskRunner")
        # ... resto del __init__ sin cambios ...
        src_path = Path(__file__).parent.parent / "src"
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))
        dry = os.getenv("MASTER_DRY_SUBPROCESS") == "1"
        try:
            if dry:
                self.logger.info(
                    "⚡ Modo dry subprocess detectado - inicialización ligera de tareas "
                    "(listas vacías)"
                )
                self.task_registry = None
                self.daily_tasks = []
                self.continuous_tasks = []
            else:
                from common.task_registry import TaskRegistry
                self.task_registry = TaskRegistry()
                self.daily_tasks = self.task_registry.get_daily_tasks()
                self.continuous_tasks = self.task_registry.get_continuous_tasks()
        except Exception as e:
            self.logger.warning(
                f"Fallo cargando registro de tareas, usando listas vacías: {e}"
            )
            self.daily_tasks = []
            self.continuous_tasks = []
        self.logger.info("🚀 Iniciando Simple Master Task Runner (nueva arquitectura)")
        self.logger.info(f"📋 Tareas diarias registradas: {len(self.daily_tasks)}")
        self.logger.info(
            f"🔄 Tareas continuas registradas: {len(self.continuous_tasks)}"
        )
    # ... resto de la clase SimpleMasterTaskRunner sin cambios ...
    def run_daily_tasks(self) -> tuple[int, int]:
        from datetime import date as _date

        from common.utils import is_workday  # type: ignore

        if not is_workday(_date.today()):
            self.logger.info("📅 Hoy no es día laborable, omitiendo tareas diarias")
            return 0, len(self.daily_tasks)
        ejecutadas = 0
        total = len(self.daily_tasks)
        for task in self.daily_tasks:
            try:
                self.logger.info(f"🔍 Verificando tarea: {task.name}")
                if task.debe_ejecutarse():
                    self.logger.info(f"▶️  Ejecutando tarea: {task.name}")
                    if task.ejecutar():
                        self.logger.info(f"✅ Tarea {task.name} ejecutada exitosamente")
                        task.marcar_como_completada()
                        ejecutadas += 1
                    else:
                        self.logger.error(f"❌ Error ejecutando tarea: {task.name}")
                else:
                    self.logger.info(f"⏭️  Tarea {task.name} no necesita ejecutarse")
            except Exception as e:  # pragma: no cover - defensivo
                self.logger.error(f"💥 Error procesando tarea {task.name}: {e}")
        return ejecutadas, total

    def run_continuous_tasks(self) -> tuple[int, int]:
        self.logger.info("🔄 Ejecutando tareas continuas...")
        ejecutadas = 0
        total = len(self.continuous_tasks)
        for task in self.continuous_tasks:
            try:
                self.logger.info(f"▶️  Ejecutando tarea continua: {task.name}")
                if task.ejecutar():
                    self.logger.info(
                        f"✅ Tarea continua {task.name} ejecutada exitosamente"
                    )
                    ejecutadas += 1
                else:
                    self.logger.error(f"❌ Error ejecutando tarea continua: {task.name}")
            except Exception as e:  # pragma: no cover - defensivo
                self.logger.error(f"💥 Error procesando tarea continua {task.name}: {e}")
        return ejecutadas, total

    def run(self):
        inicio = datetime.now()
        self.logger.info(
            f"🎯 Iniciando ejecución (modo simple) - {inicio.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        try:
            d_exec, d_total = self.run_daily_tasks()
            c_exec, c_total = self.run_continuous_tasks()
            total_exec = d_exec + c_exec
            total = d_total + c_total
            duracion = datetime.now() - inicio
            self.logger.info("=" * 60)
            self.logger.info("📊 RESUMEN (MODO SIMPLE)")
            self.logger.info("=" * 60)
            self.logger.info(f"📅 Tareas diarias: {d_exec}/{d_total}")
            self.logger.info(f"🔄 Tareas continuas: {c_exec}/{c_total}")
            self.logger.info(f"🎯 Total ejecutadas: {total_exec}/{total}")
            self.logger.info(f"⏱️  Duración: {duracion}")
            tasa = (total_exec / total * 100) if total else 0
            self.logger.info(f"📈 Tasa de éxito: {tasa:.1f}%")
            if total_exec == total:
                self.logger.info("🎉 Todas las tareas se ejecutaron exitosamente")
            else:
                self.logger.warning(
                    f"⚠️  {total - total_exec} tareas no se ejecutaron correctamente"
                )
        except Exception as e:  # pragma: no cover - defensivo
            self.logger.error(f"💥 Error crítico en modo simple: {e}")
            raise
        finally:
            # Cierre de conexiones si las tareas lo soportan
            for task in self.daily_tasks + self.continuous_tasks:
                try:
                    task.close_connections()
                except Exception as e:  # pragma: no cover - defensivo
                    self.logger.warning(
                        f"⚠️  Error cerrando conexiones de {task.name}: {e}"
                    )

############################################################
# MODO CLÁSICO (ciclos continuos)
############################################################
class MasterRunner:
    """Script maestro que ejecuta todos los scripts del sistema según horarios específicos"""
    def __init__(self, verbose: bool = False, single_cycle: bool = False):
        # El logging ya está configurado globalmente, solo obtenemos el logger.
        self.logger_adapter = logging.getLogger(f"{__name__}.MasterRunner")
        # ... resto del __init__ sin la llamada a _setup_logging() ...
        self.running = True
        self.verbose_mode = verbose
        self.single_cycle = single_cycle
        self.project_root = Path(__file__).parent.parent
        self.scripts_dir = self.project_root / "scripts"
        self._load_config()
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        self.cycle_count = 0
        self.total_scripts_executed = 0
        self.successful_scripts = 0
        self.failed_scripts = 0
        self.max_workers = int(os.getenv("MASTER_MAX_WORKERS", "3"))
        self.thread_lock = threading.Lock()
        self.available_scripts = {}
        self.daily_scripts: list[str] = []
        self.continuous_scripts: list[str] = []
        self.script_to_task_name: dict[str, str | list[str]] = {}
        config_file = self.project_root / "scripts_config.json"
        try:
            with open(config_file, encoding="utf-8") as f:
                data = json.load(f)
            scripts_cfg = data.get("scripts", {})
            for name, meta in scripts_cfg.items():
                file_name = meta.get("file")
                tipo = meta.get("type")
                task_name = meta.get("task_name")
                if not file_name or not tipo:
                    continue
                self.available_scripts[name] = file_name
                if tipo == "daily":
                    self.daily_scripts.append(name)
                    if task_name:
                        self.script_to_task_name[name] = task_name
                elif tipo == "continuous":
                    self.continuous_scripts.append(name)
            preferred_order = [
                "riesgos",
                "brass",
                "expedientes",
                "no_conformidades",
                "agedys",
            ]
            self.daily_scripts.sort(
                key=lambda x:
                    (preferred_order.index(x) if x in preferred_order else 999, x)
            )
        except Exception as e:
            self.logger_adapter.error(f"❌ Error cargando scripts_config.json: {e}")
        if os.getenv("MASTER_DRY_SUBPROCESS") == "1":
            self.db_tareas = None
        else:
            self._init_database_connection()
        mode_info = "MODO VERBOSE" if self.verbose_mode else "MODO NORMAL"
        cycle_info = " - UN SOLO CICLO" if self.single_cycle else ""
        self.logger_adapter.info(
            f"🚀 Master Runner inicializado correctamente - {mode_info}{cycle_info}"
        )
        self.logger_adapter.info(f"📁 Directorio de scripts: {self.scripts_dir}")
        self.logger_adapter.info(f"📅 Archivo de festivos: {self.festivos_file}")
        self.logger_adapter.info(f"⚙️  Scripts disponibles: {list(self.available_scripts.keys())}")
        self.logger_adapter.info(f"🧵 Máximo de hilos concurrentes: {self.max_workers}")
        if self.single_cycle:
            self.logger_adapter.info(
                "🔄 MODO UN SOLO CICLO ACTIVADO - El script se detendrá después del "
                "primer ciclo"
            )
            self.logger_adapter.info("resumen: ciclo único inicializado")
        if self.verbose_mode:
            self.logger_adapter.info(
                "🔍 MODO VERBOSE ACTIVADO - Se mostrarán todos los detalles de ejecución"
            )
            self.logger_adapter.info(f"📋 Scripts diarios: {self.daily_scripts}")
            self.logger_adapter.info(f"📧 Scripts continuos: {self.continuous_scripts}")
            self.logger_adapter.info(
                f"🧵 Ejecución en paralelo habilitada con {self.max_workers} hilos"
            )
    # ... resto de la clase MasterRunner sin cambios ...
    # El método _setup_logging() ya no es necesario aquí.
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
            self.db_tareas = AccessDatabase(
                self.config.get_db_tareas_connection_string()
            )

            self.logger_adapter.info(
                "✅ Conexión a base de datos de tareas inicializada correctamente"
            )

        except Exception as e:
            self.logger_adapter.error(f"❌ Error inicializando conexión a base de datos: {e}")
            self.db_tareas = None

    def _register_task_completion_for_script(self, script_name: str):
        """
        Registra la finalización de una tarea basándose en el nombre del script

        Args:
            script_name: Nombre del script ejecutado
        """
        if not self.db_tareas:
            self.logger_adapter.warning(
                f"⚠️  No hay conexión a BD, no se puede registrar tarea para {script_name}"
            )
            return

        try:
            # Importar la función común
            from common.utils import register_task_completion

            # Obtener el nombre de la tarea en la base de datos
            task_names = self.script_to_task_name.get(script_name)

            if not task_names:
                self.logger_adapter.warning(
                    f"⚠️  No se encontró mapeo de tarea para script {script_name}"
                )
                return

            # Si es una lista de tareas (como riesgos o no_conformidades)
            if isinstance(task_names, list):
                for task_name in task_names:
                    success = register_task_completion(self.db_tareas, task_name)
                    if success:
                        self.logger_adapter.info(
                            f"✅ Tarea {task_name} registrada como completada"
                        )
                    else:
                        self.logger_adapter.error(
                            f"❌ Error registrando tarea {task_name}"
                        )
            else:
                # Si es una sola tarea
                success = register_task_completion(self.db_tareas, task_names)
                if success:
                    self.logger_adapter.info(
                        f"✅ Tarea {task_names} registrada como completada"
                    )
                else:
                    self.logger_adapter.error(f"❌ Error registrando tarea {task_names}")

        except Exception as e:
            self.logger_adapter.error(
                f"❌ Error registrando finalización de tarea para {script_name}: {e}"
            )

    def _load_config(self):
        """Carga la configuración desde archivo .env"""
        try:
            # Intentar cargar desde .env en la raíz del proyecto
            env_file = self.project_root / ".env"
            if env_file.exists():
                self._load_env_file(env_file)
            else:
                self.logger_adapter.warning("Archivo .env no encontrado, usando valores por defecto")

            # Configurar rutas y valores con fallbacks
            self.festivos_file = self.project_root / os.getenv(
                "MASTER_FESTIVOS_FILE", "herramientas/Festivos.txt"
            )
            self.status_file = self.project_root / os.getenv(
                "MASTER_STATUS_FILE", "logs/run_master_status.json"
            )

            # Tiempos de ciclo (en minutos)
            self.cycle_times = {
                "laborable_dia": int(os.getenv("MASTER_CYCLE_LABORABLE_DIA", "5")),
                "laborable_noche": int(os.getenv("MASTER_CYCLE_LABORABLE_NOCHE", "60")),
                "no_laborable_dia": int(
                    os.getenv("MASTER_CYCLE_NO_LABORABLE_DIA", "60")
                ),
                "no_laborable_noche": int(
                    os.getenv("MASTER_CYCLE_NO_LABORABLE_NOCHE", "120")
                ),
            }

            # Timeout para scripts
            self.script_timeout = int(os.getenv("MASTER_SCRIPT_TIMEOUT", "1800"))

            self.logger_adapter.info(
                f"⚙️  Configuración cargada: ciclos={self.cycle_times}, timeout={self.script_timeout}s"
            )

        except Exception as e:
            self.logger_adapter.error(f"❌ Error cargando configuración: {e}")
            # Usar valores por defecto
            self.festivos_file = self.project_root / "herramientas" / "Festivos.txt"
            self.status_file = self.project_root / "logs" / "run_master.json"
            self.cycle_times = {
                "laborable_dia": 5,
                "laborable_noche": 60,
                "no_laborable_dia": 60,
                "no_laborable_noche": 120,
            }
            self.script_timeout = 1800

    def _load_env_file(self, env_file: Path):
        """Carga variables de entorno desde archivo .env"""
        try:
            with open(env_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        os.environ[key.strip()] = value.strip()
        except Exception as e:
            self.logger_adapter.warning(f"Error leyendo archivo .env: {e}")

    def _update_cycle_context(self):
        """Actualiza el contexto del ciclo en el logger"""
        pass

    def es_noche(self) -> bool:
        """Determina si es horario nocturno (20:00-07:00)"""
        hora = datetime.now().hour
        return (hora >= 20) or (hora < 7)

    def es_laborable(self, fecha: date = None) -> bool:
        """Determina si una fecha es día laborable (no fin de semana ni festivo)"""
        if fecha is None:
            fecha = date.today()

        if fecha.weekday() >= 5:
            return False

        if self.festivos_file.exists():
            try:
                with open(self.festivos_file, encoding="utf-8") as f:
                    for linea in f:
                        linea = linea.strip()
                        if fecha.strftime("%d/%m/%Y") in linea:
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
                minutos = self.cycle_times["laborable_noche"]
            else:
                minutos = self.cycle_times["laborable_dia"]
        else:
            if es_noche:
                minutos = self.cycle_times["no_laborable_noche"]
            else:
                minutos = self.cycle_times["no_laborable_dia"]

        return minutos * 60

    def ejecutar_script(self, script_name: str) -> dict[str, any]:
        """
        Ejecuta un script específico y retorna información detallada del resultado
        """
        if script_name not in self.available_scripts:
            self.logger_adapter.error(f"Script {script_name} no disponible")
            return {
                "success": False,
                "duration": 0,
                "output": "",
                "error": f"Script {script_name} no disponible",
                "return_code": -1,
            }

        script_file = self.available_scripts[script_name]
        script_path = self.scripts_dir / script_file

        if not script_path.exists():
            self.logger_adapter.warning(
                f"Script {script_file} no encontrado, saltando..."
            )
            return {
                "success": False,
                "duration": 0,
                "output": "",
                "error": f"Script {script_file} no encontrado",
                "return_code": -1,
            }

        try:
            if os.getenv("MASTER_DRY_SUBPROCESS") == "1":
                fake_duration = 0.01
                with self.thread_lock:
                    self.total_scripts_executed += 1
                    self.successful_scripts += 1
                self.logger_adapter.debug(
                    f"(dry-run) Simulando ejecución de {script_name}"
                )
                return {
                    "success": True,
                    "duration": fake_duration,
                    "output": "dry-run",
                    "error": "",
                    "return_code": 0,
                }
            if self.verbose_mode:
                self.logger_adapter.info(f"🔄 INICIANDO SCRIPT: {script_name}")
                self.logger_adapter.info(f"   📄 Archivo: {script_file}")
                self.logger_adapter.info(f"   📍 Ruta completa: {script_path}")
                self.logger_adapter.info(
                    f"   ⏰ Hora de inicio: {datetime.now().strftime('%H:%M:%S')}"
                )
                self.logger_adapter.info(
                    f"   🧵 Hilo: {threading.current_thread().name}"
                )
            else:
                self.logger_adapter.info(
                    f"▶️  Ejecutando {script_name} ({script_file}) - Hilo: "
                    f"{threading.current_thread().name}"
                )

            start_time = datetime.now()

            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=str(self.scripts_dir.parent),
                capture_output=True,
                text=True,
                timeout=self.script_timeout,
            )

            execution_time = (datetime.now() - start_time).total_seconds()

            with self.thread_lock:
                self.total_scripts_executed += 1

                if result.returncode == 0:
                    self.successful_scripts += 1

                    if self.verbose_mode:
                        self.logger_adapter.info(
                            f"✅ SCRIPT COMPLETADO EXITOSAMENTE: {script_name}"
                        )
                        self.logger_adapter.info(
                            f"   ⏱️  Tiempo de ejecución: {execution_time:.2f} segundos"
                        )
                        self.logger_adapter.info(
                            f"   📤 Código de salida: {result.returncode}"
                        )
                        self.logger_adapter.info(
                            f"   🧵 Hilo: {threading.current_thread().name}"
                        )
                        if result.stdout and result.stdout.strip():
                            self.logger_adapter.info("   📋 SALIDA ESTÁNDAR:")
                            for line in result.stdout.strip().split("\n"):
                                self.logger_adapter.info(f"      {line}")
                        if result.stderr and result.stderr.strip():
                            self.logger_adapter.info("   ⚠️  SALIDA DE ERROR:")
                            for line in result.stderr.strip().split("\n"):
                                self.logger_adapter.info(f"      {line}")
                        else:
                            self.logger_adapter.info(
                                "   🚨 No hay información adicional de error"
                            )
                    else:
                        self.logger_adapter.info(
                            f"✅ {script_name} completado exitosamente en "
                            f"{execution_time:.1f}s"
                        )

                    if result.stdout and result.stdout.strip():
                        self.logger_adapter.debug(
                            f"Output de {script_name}: {result.stdout.strip()}"
                        )
                    if result.stderr and result.stderr.strip():
                        self.logger_adapter.debug(
                            f"Stderr de {script_name}: {result.stderr.strip()}"
                        )

                    return {
                        "success": True,
                        "duration": execution_time,
                        "output": result.stdout,
                        "error": "",
                        "return_code": result.returncode,
                    }
                else:
                    self.failed_scripts += 1

                    if self.verbose_mode:
                        self.logger_adapter.error(f"❌ SCRIPT FALLÓ: {script_name}")
                        self.logger_adapter.error(
                            f"   ⏱️  Tiempo de ejecución: {execution_time:.2f} segundos"
                        )
                        self.logger_adapter.error(
                            f"   📤 Código de salida: {result.returncode}"
                        )
                        self.logger_adapter.error(
                            f"   🧵 Hilo: {threading.current_thread().name}"
                        )
                        if result.stdout and result.stdout.strip():
                            self.logger_adapter.error("   📋 SALIDA ESTÁNDAR:")
                            for line in result.stdout.strip().split("\n"):
                                self.logger_adapter.error(f"      {line}")
                        if result.stderr and result.stderr.strip():
                            self.logger_adapter.error("   🚨 SALIDA DE ERROR:")
                            for line in result.stderr.strip().split("\n"):
                                self.logger_adapter.error(f"      {line}")
                        else:
                            self.logger_adapter.error(
                                "   🚨 No hay información adicional de error"
                            )
                    else:
                        self.logger_adapter.error(
                            f"❌ {script_name} falló con código {result.returncode} en "
                            f"{execution_time:.1f}s"
                        )

                    if result.stderr:
                        self.logger_adapter.error(f"Error stderr: {result.stderr}")
                    if result.stdout:
                        self.logger_adapter.error(f"Output stdout: {result.stdout}")

                    return {
                        "success": False,
                        "duration": execution_time,
                        "output": result.stdout,
                        "error": result.stderr,
                        "return_code": result.returncode,
                    }

        except subprocess.TimeoutExpired:
            with self.thread_lock:
                self.failed_scripts += 1
                self.total_scripts_executed += 1
            execution_time = self.script_timeout

            if self.verbose_mode:
                self.logger_adapter.error(f"⏰ TIMEOUT: {script_name}")
                self.logger_adapter.error(
                    f"   ⏱️  Tiempo transcurrido: {execution_time:.2f} segundos"
                )
                self.logger_adapter.error(
                    f"   🚨 El script excedió el límite de {self.script_timeout} segundos"
                )
                self.logger_adapter.error(
                    f"   🧵 Hilo: {threading.current_thread().name}"
                )
            else:
                self.logger_adapter.error(
                    f"❌ {script_name} excedió el tiempo límite de {self.script_timeout}s"
                )

            return {
                "success": False,
                "duration": execution_time,
                "output": "",
                "error": f"Timeout después de {self.script_timeout}s",
                "return_code": -2,
            }
        except Exception as e:
            with self.thread_lock:
                self.failed_scripts += 1
                self.total_scripts_executed += 1

            if self.verbose_mode:
                self.logger_adapter.error(f"💥 EXCEPCIÓN EN SCRIPT: {script_name}")
                self.logger_adapter.error(f"   🚨 Error: {str(e)}")
                self.logger_adapter.error(f"   📍 Tipo de error: {type(e).__name__}")
                self.logger_adapter.error(
                    f"   🧵 Hilo: {threading.current_thread().name}"
                )
            else:
                self.logger_adapter.error(f"❌ Error ejecutando {script_name}: {e}")

            return {
                "success": False,
                "duration": 0,
                "output": "",
                "error": str(e),
                "return_code": -3,
            }

    def ejecutar_tareas_diarias(self) -> dict[str, any]:
        """Ejecuta las tareas diarias consultando la lógica OO de cada TareaDiaria."""
        src_path = Path(__file__).parent.parent / "src"
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))
        try:
            from common.task_registry import TaskRegistry

            task_instances = TaskRegistry().get_daily_tasks()
        except Exception as e:
            self.logger_adapter.warning(
                f"No se pudo importar task_registry: {e}. Saltando tareas diarias."
            )
            return {}
        file_to_key = {v: k for k, v in self.available_scripts.items()}
        if self.verbose_mode:
            self.logger_adapter.info("🌅 ===== INICIANDO TAREAS DIARIAS =====")
            self.logger_adapter.info(f"   📅 Fecha: {date.today().strftime('%d/%m/%Y')}")
            self.logger_adapter.info(f"   🧵 Máximo de hilos: {self.max_workers}")
            self.logger_adapter.info(
                "   Verificando debe_ejecutarse() de cada tarea registrada"
            )

        scripts_a_ejecutar: list[str] = []
        for task in task_instances:
            try:
                if task.debe_ejecutarse():
                    key = file_to_key.get(task.script_filename)
                    if key:
                        scripts_a_ejecutar.append(key)
                    else:
                        self.logger_adapter.warning(
                            f"⚠️  No se encontró clave de script para {task.script_filename}"
                        )
                elif self.verbose_mode:
                    self.logger_adapter.info(f"⏭️  {task.name} no requiere ejecución")
            except Exception as e:
                self.logger_adapter.error(f"❌ Error evaluando {task.name}: {e}")

        if not scripts_a_ejecutar:
            self.logger_adapter.info(
                "✅ No hay tareas diarias pendientes (debe_ejecutarse() = False en todas)"
            )
            return {}

        if self.verbose_mode:
            self.logger_adapter.info(f"📋 Scripts a ejecutar: {scripts_a_ejecutar}")

        resultados = {}
        tiempo_inicio = datetime.now()

        with ThreadPoolExecutor(
            max_workers=self.max_workers, thread_name_prefix="Daily"
        ) as executor:
            future_to_script = {
                executor.submit(self.ejecutar_script, script_name): script_name
                for script_name in scripts_a_ejecutar
            }

            for i, future in enumerate(as_completed(future_to_script), 1):
                script_name = future_to_script[future]

                try:
                    resultado = future.result()
                    resultados[script_name] = resultado

                    if resultado["success"]:
                        self._register_task_completion_for_script(script_name)

                    if self.verbose_mode:
                        status = "✅ EXITOSO" if resultado["success"] else "❌ FALLIDO"
                        self.logger_adapter.info(
                            f"📌 TAREA DIARIA COMPLETADA {i}/{len(scripts_a_ejecutar)}: "
                            f"{script_name} - {status}"
                        )
                    else:
                        status = "✅" if resultado["success"] else "❌"
                        self.logger_adapter.info(
                            f"📋 Tarea {i}/{len(scripts_a_ejecutar)}: {script_name} {status}"
                        )

                except Exception as e:
                    self.logger_adapter.error(
                        f"❌ Error procesando resultado de {script_name}: {e}"
                    )
                    resultados[script_name] = {
                        "success": False,
                        "duration": 0,
                        "output": "",
                        "error": str(e),
                        "return_code": -4,
                    }

        tareas_exitosas = sum(1 for r in resultados.values() if r["success"])
        total_tareas = len(scripts_a_ejecutar)
        tiempo_total = (datetime.now() - tiempo_inicio).total_seconds()

        if self.verbose_mode:
            self.logger_adapter.info("🌅 RESUMEN DE TAREAS DIARIAS COMPLETADO")
            self.logger_adapter.info(f"   ✅ Exitosas: {tareas_exitosas}")
            self.logger_adapter.info(f"   ❌ Fallidas: {total_tareas - tareas_exitosas}")
            self.logger_adapter.info(f"   📊 Total: {total_tareas}")
            self.logger_adapter.info(f"   ⏱️  Tiempo total: {tiempo_total:.1f}s")
            self.logger_adapter.info("   " + "=" * 50)
        else:
            self.logger_adapter.info(
                f"✅ TAREAS DIARIAS COMPLETADAS: {tareas_exitosas}/{total_tareas} "
                f"exitosas en {tiempo_total:.1f}s"
            )

        return {
            "success": tareas_exitosas > 0,
            "total_tasks": total_tareas,
            "successful_tasks": tareas_exitosas,
            "failed_tasks": total_tareas - tareas_exitosas,
            "duration": tiempo_total,
            "results": resultados,
        }

    def ejecutar_tareas_continuas(self) -> dict[str, bool]:
        """
        Ejecuta todas las tareas continuas en cada ciclo usando threading
        """
        if self.verbose_mode:
            self.logger_adapter.info("📧 INICIANDO EJECUCIÓN DE TAREAS CONTINUAS")
            self.logger_adapter.info(f"   🔄 Ciclo número: {self.cycle_count}")
            self.logger_adapter.info(
                f"   📝 Scripts a ejecutar: {self.continuous_scripts}"
            )
            self.logger_adapter.info(f"   🧵 Máximo de hilos: {self.max_workers}")
            self.logger_adapter.info("   " + "=" * 50)
        else:
            self.logger_adapter.info("📧 Ejecutando tareas continuas...")

        results = {}
        tiempo_inicio = datetime.now()

        with ThreadPoolExecutor(
            max_workers=self.max_workers, thread_name_prefix="Continuous"
        ) as executor:
            future_to_script = {
                executor.submit(self.ejecutar_script, script_name): script_name
                for script_name in self.continuous_scripts
            }

            for i, future in enumerate(as_completed(future_to_script), 1):
                script_name = future_to_script[future]

                try:
                    resultado = future.result()
                    results[script_name] = resultado["success"]

                    if self.verbose_mode:
                        status = "✅ EXITOSO" if resultado["success"] else "❌ FALLIDO"
                        self.logger_adapter.info(
                            f"📌 TAREA CONTINUA COMPLETADA {i}/"
                            f"{len(self.continuous_scripts)}: {script_name} - {status}"
                        )
                    else:
                        status = "✅" if resultado["success"] else "❌"
                        self.logger_adapter.info(
                            f"📧 Tarea {i}/{len(self.continuous_scripts)}: {script_name} {status}"
                        )

                except Exception as e:
                    self.logger_adapter.error(
                        f"❌ Error procesando resultado de {script_name}: {e}"
                    )
                    results[script_name] = False

        successful_count = sum(1 for success in results.values() if success)
        failed_count = len(self.continuous_scripts) - successful_count
        tiempo_total = (datetime.now() - tiempo_inicio).total_seconds()

        if self.verbose_mode:
            self.logger_adapter.info("📧 RESUMEN DE TAREAS CONTINUAS COMPLETADO")
            self.logger_adapter.info(f"   ✅ Exitosas: {successful_count}")
            self.logger_adapter.info(f"   ❌ Fallidas: {failed_count}")
            self.logger_adapter.info(f"   📊 Total: {len(self.continuous_scripts)}")
            self.logger_adapter.info(f"   ⏱️  Tiempo total: {tiempo_total:.1f}s")
            self.logger_adapter.info("   " + "=" * 50)
        else:
            self.logger_adapter.info(
                f"📧 Tareas continuas completadas: {successful_count} exitosas, "
                f"{failed_count} fallidas en {tiempo_total:.1f}s"
            )

        return results

    def run(self):
        """Ejecuta el ciclo principal del script maestro"""
        if self.verbose_mode:
            self.logger_adapter.info(
                "🚀 ===== INICIANDO SCRIPT MAESTRO DE PRODUCCIÓN (MODO VERBOSE) ====="
            )
            self.logger_adapter.info(f"📁 Directorio de scripts: {self.scripts_dir}")
            self.logger_adapter.info(f"📅 Archivo de festivos: {self.festivos_file}")
            self.logger_adapter.info(f"⚙️  Configuración de ciclos: {self.cycle_times}")
            self.logger_adapter.info(f"⏰ Timeout de scripts: {self.script_timeout}s")
            self.logger_adapter.info(f"🧵 Máximo de hilos: {self.max_workers}")
            self.logger_adapter.info(f"📋 Scripts diarios: {self.daily_scripts}")
            self.logger_adapter.info(f"📧 Scripts continuos: {self.continuous_scripts}")
            self.logger_adapter.info("   " + "=" * 50)
        else:
            self.logger_adapter.info(
                "🚀 ===== INICIANDO SCRIPT MAESTRO DE PRODUCCIÓN ====="
            )
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
                    self.logger_adapter.info(
                        f"🔄 ===== INICIANDO CICLO {self.cycle_count} ====="
                    )
                    self.logger_adapter.info(
                        f"📅 Fecha: {fecha_actual} | Laborable: {es_laborable_hoy} | "
                        f"Hora: {hora_actual:02d}:00 | Noche: {es_noche}"
                    )
                    self.logger_adapter.info(
                        f"⏰ Hora completa: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
                    )
                    self.logger_adapter.info("   " + "=" * 50)
                else:
                    self.logger_adapter.info(f"🔄 ===== CICLO {self.cycle_count} =====")
                    self.logger_adapter.info(
                        f"📅 Fecha: {fecha_actual} | Laborable: {es_laborable_hoy} | "
                        f"Hora: {hora_actual:02d}:00 | Noche: {es_noche}"
                    )

                ciclo_inicio = datetime.now()

                ejecutar_diarias = es_laborable_hoy and hora_actual >= 7

                if ejecutar_diarias:
                    if self.verbose_mode:
                        self.logger_adapter.info(
                            "🌅 CONDICIONES PARA TAREAS DIARIAS CUMPLIDAS"
                        )
                        self.logger_adapter.info(f"   📅 Fecha actual: {fecha_actual}")
                        self.logger_adapter.info(
                            "   🚀 Iniciando ejecución de tareas diarias..."
                        )
                    else:
                        self.logger_adapter.info(
                            "🌅 Ejecutando tareas diarias pendientes"
                        )

                    self.ejecutar_tareas_diarias()

                    if self.verbose_mode:
                        self.logger_adapter.info(
                            "✅ EJECUCIÓN DE TAREAS DIARIAS COMPLETADA"
                        )
                else:
                    if self.verbose_mode:
                        self.logger_adapter.info("⏭️  SALTANDO TAREAS DIARIAS")
                        if not es_laborable_hoy:
                            self.logger_adapter.info("   📅 Razón: No es día laborable")
                        elif hora_actual < 7:
                            self.logger_adapter.info(
                                f"   ⏰ Razón: Muy temprano (hora actual: {hora_actual:02d}:00, "
                                f"mínimo: 07:00)"
                            )
                        else:
                            self.logger_adapter.info(
                                "   ✅ Razón: Lógica interna indicó no ejecutar"
                            )
                    else:
                        self.logger_adapter.info(
                            "⏭️  Saltando tareas diarias (condiciones no cumplidas)"
                        )

                if self.verbose_mode:
                    self.logger_adapter.info("📧 INICIANDO TAREAS CONTINUAS DEL CICLO")

                self.ejecutar_tareas_continuas()

                tiempo_ciclo = (datetime.now() - ciclo_inicio).total_seconds()

                tiempo_espera = self.get_tiempo_espera()

                if self.verbose_mode:
                    self.logger_adapter.info(
                        f"📊 RESUMEN DETALLADO DEL CICLO {self.cycle_count}:"
                    )
                    self.logger_adapter.info(
                        f"   ⏱️  Duración del ciclo: {tiempo_ciclo:.2f} segundos"
                    )
                    self.logger_adapter.info(
                        f"   📈 Scripts ejecutados (total): {self.total_scripts_executed}"
                    )
                    self.logger_adapter.info(
                        f"   ✅ Scripts exitosos (total): {self.successful_scripts}"
                    )
                    self.logger_adapter.info(
                        f"   ❌ Scripts fallidos (total): {self.failed_scripts}"
                    )
                    if self.total_scripts_executed > 0:
                        success_rate = (
                            self.successful_scripts / self.total_scripts_executed
                        ) * 100
                        self.logger_adapter.info(
                            f"   📊 Tasa de éxito: {success_rate:.1f}%"
                        )
                    self.logger_adapter.info(
                        f"   ⏰ Próximo ciclo en: {tiempo_espera//60} minutos ({tiempo_espera} segundos)"
                    )
                    self.logger_adapter.info("   " + "=" * 50)
                else:
                    self.logger_adapter.info(f"📊 RESUMEN CICLO {self.cycle_count}:")
                    self.logger_adapter.info(
                        f"   ⏱️  Duración del ciclo: {tiempo_ciclo:.1f}s"
                    )
                    self.logger_adapter.info(
                        f"   📈 Scripts ejecutados en total: {self.total_scripts_executed}"
                    )
                    self.logger_adapter.info(
                        f"   ✅ Scripts exitosos: {self.successful_scripts}"
                    )
                    self.logger_adapter.info(
                        f"   ❌ Scripts fallidos: {self.failed_scripts}"
                    )
                    self.logger_adapter.info(
                        f"   ⏰ Próximo ciclo en: {tiempo_espera//60} minutos"
                    )

                self._actualizar_estado()

                if self.single_cycle:
                    if self.verbose_mode:
                        self.logger_adapter.info("🔄 MODO UN SOLO CICLO COMPLETADO")
                        self.logger_adapter.info(
                            "   ✅ Ciclo único ejecutado exitosamente"
                        )
                        self.logger_adapter.info(
                            "   🛑 Terminando ejecución del script maestro"
                        )
                    else:
                        self.logger_adapter.info(
                            "🔄 Ciclo único completado, terminando ejecución"
                        )
                    break

                if self.verbose_mode:
                    self.logger_adapter.info(
                        f"😴 ESPERANDO {tiempo_espera//60} MINUTOS HASTA EL PRÓXIMO CICLO..."
                    )
                    self.logger_adapter.info(
                        f"   ⏰ Hora de reanudación estimada: {(datetime.now() + timedelta(seconds=tiempo_espera)).strftime('%H:%M:%S')}"
                    )
                else:
                    self.logger_adapter.info(
                        f"😴 Esperando {tiempo_espera//60} minutos hasta el próximo ciclo..."
                    )

                tiempo_restante = tiempo_espera

                while tiempo_restante > 0 and self.running:
                    sleep_time = min(60, tiempo_restante)
                    time.sleep(sleep_time)
                    tiempo_restante -= sleep_time

                    if (
                        self.verbose_mode
                        and tiempo_espera > 300
                        and tiempo_restante > 0
                        and tiempo_restante % 300 == 0
                    ):
                        self.logger_adapter.info(
                            f"⏳ Tiempo restante de espera: {tiempo_restante//60} minutos"
                        )

                    if date.today() != fecha_actual:
                        if self.verbose_mode:
                            self.logger_adapter.info("📅 CAMBIO DE DÍA DETECTADO")
                            self.logger_adapter.info(
                                f"   📅 Nueva fecha: {date.today()}"
                            )
                        else:
                            self.logger_adapter.info("📅 Cambio de día detectado")
                        break

        except KeyboardInterrupt:
            if self.verbose_mode:
                self.logger_adapter.info(
                    "⚠️  INTERRUPCIÓN POR TECLADO DETECTADA (Ctrl+C)"
                )
                self.logger_adapter.info(
                    "   🔄 Iniciando proceso de parada limpia..."
                )
            else:
                self.logger_adapter.info("⚠️  Interrupción por teclado detectada")
        except Exception as e:
            if self.verbose_mode:
                self.logger_adapter.error("❌ ERROR CRÍTICO EN CICLO PRINCIPAL")
                self.logger_adapter.error(f"   🚨 Error: {e}")
                self.logger_adapter.error(f"   📍 Tipo de error: {type(e).__name__}")
                self.logger_adapter.error(
                    "   🔄 Iniciando proceso de parada de emergencia..."
                )
            else:
                self.logger_adapter.error(
                    f"❌ Error en ciclo principal: {e}", exc_info=True
                )
        finally:
            self.stop()

    def list_tasks(self) -> int:
        """Lista tareas diarias y continuas indicando si deben ejecutarse (según lógica OO)."""
        src_path = Path(__file__).parent.parent / "src"
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))
        try:
            from common.task_registry import TaskRegistry

            registry = TaskRegistry()
            daily = registry.get_daily_tasks()
            cont = registry.get_continuous_tasks()
        except Exception as e:
            print(f"Error importando registro de tareas: {e}")
            return 1
        print("TASK TYPE        SHOULD_RUN  SCRIPT")
        print("------------------------------------------")
        file_to_key = {v: k for k, v in self.available_scripts.items()}
        for t in daily:
            try:
                should = t.debe_ejecutarse()
            except Exception:
                should = False
            key = file_to_key.get(t.script_filename, t.script_filename)
            print(f"DAILY {key:<12} {str(should):<11} {t.script_filename}")
        for t in cont:
            print(f"CONT  {t.name:<12} True        {t.script_filename}")
        return 0

    def stop(self):
        """Detiene la ejecución del script maestro"""
        self.logger_adapter.info("🛑 Deteniendo script maestro...")
        self.running = False
        self.logger_adapter.info("✅ Script maestro detenido correctamente")
        self.logger_adapter.info("📊 ESTADÍSTICAS FINALES:")
        self.logger_adapter.info(f"   🔄 Ciclos completados: {self.cycle_count}")
        self.logger_adapter.info(
            f"   📈 Scripts ejecutados: {self.total_scripts_executed}"
        )
        self.logger_adapter.info(f"   ✅ Scripts exitosos: {self.successful_scripts}")
        self.logger_adapter.info(f"   ❌ Scripts fallidos: {self.failed_scripts}")

    def _actualizar_estado(self):
        """Actualiza el archivo de estado del script maestro"""
        try:
            estado = {
                "timestamp": datetime.now().isoformat(),
                "running": self.running,
                "cycle_count": self.cycle_count,
                "fecha_actual": date.today().isoformat(),
                "es_laborable": self.es_laborable(),
                "es_noche": self.es_noche(),
                "scripts_disponibles": list(self.available_scripts.keys()),
                "proximo_tiempo_espera_minutos": self.get_tiempo_espera() // 60,
                "estadisticas": {
                    "total_scripts_executed": self.total_scripts_executed,
                    "successful_scripts": self.successful_scripts,
                    "failed_scripts": self.failed_scripts,
                    "success_rate": (
                        self.successful_scripts / max(1, self.total_scripts_executed)
                    )
                    * 100,
                },
                "configuracion": {
                    "cycle_times": self.cycle_times,
                    "script_timeout": self.script_timeout,
                    "festivos_file": str(self.festivos_file),
                    "daily_scripts": self.daily_scripts,
                    "continuous_scripts": self.continuous_scripts,
                },
            }

            self.status_file.parent.mkdir(exist_ok=True)
            with open(self.status_file, "w", encoding="utf-8") as f:
                json.dump(estado, f, indent=2, ensure_ascii=False)

        except Exception as e:
            self.logger_adapter.warning(f"Error actualizando estado: {e}")

    def _signal_handler(self, signum, frame):
        """Maneja señales del sistema para parada limpia"""
        self.logger_adapter.info(
            f"📡 Señal {signum} recibida, iniciando parada limpia..."
        )
        self.stop()


def main():
    """Función principal del script maestro"""
    parser = argparse.ArgumentParser(
        description="Script maestro de producción para ejecutar todos los scripts del sistema",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python run_master.py                  # Modo normal (ciclo continuo)
  python run_master.py --verbose        # Modo verbose (muestra todos los logs)
  python run_master.py -v               # Modo verbose (forma corta)
  python run_master.py --single-cycle   # Ejecutar solo un ciclo y terminar
  python run_master.py -s -v            # Un solo ciclo en modo verbose
    python run_master.py --simple         # Ejecutar en modo simple (nueva arquitectura) una sola vez
    python run_master.py --simple -v      # Modo simple con logs verbose
    """,
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Activar modo verbose para ver todos los detalles de ejecución",
    )

    parser.add_argument(
        "-s",
        "--single-cycle",
        action="store_true",
        help="Ejecutar solo un ciclo y terminar (útil para pruebas)",
    )
    parser.add_argument(
        "--simple",
        action="store_true",
        help="Usar el modo simple (nueva arquitectura de tareas) en lugar del modo clásico",
    )
    parser.add_argument(
        "--list-tasks",
        action="store_true",
        help="Listar tareas y si deben ejecutarse según su lógica interna y salir",
    )

    args = parser.parse_args()

    # --- MODIFICACIÓN AQUÍ ---
    # Llamamos a nuestra nueva función de setup al inicio de main()
    setup_global_logging(os.getenv("MASTER_LOG_LEVEL", "INFO"))

    try:
        if args.list_tasks:
            master = MasterRunner(verbose=args.verbose, single_cycle=True)
            code = master.list_tasks()
            sys.exit(code)
        if args.simple:
            runner = SimpleMasterTaskRunner()
            if args.verbose:
                runner.logger.info("(simple) Verbose activo")
            runner.run()
        else:
            master = MasterRunner(verbose=args.verbose, single_cycle=args.single_cycle)
            master.run()
    except Exception as e:
        logger.error(f"❌ Error fatal en main: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
