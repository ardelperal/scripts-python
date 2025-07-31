"""
Script maestro de producción para ejecutar todos los scripts del sistema.

Este script reemplaza al legacy script-continuo.vbs y maneja la ejecución
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
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Optional

# Configurar logging básico
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MasterRunner:
    """Script maestro que ejecuta todos los scripts del sistema según horarios específicos"""
    
    def __init__(self, verbose: bool = False):
        self.running = True
        self.verbose_mode = verbose
        
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
        self.last_daily_tasks_date = None
        self.daily_tasks_completed = False
        self.cycle_count = 0
        self.total_scripts_executed = 0
        self.successful_scripts = 0
        self.failed_scripts = 0
        
        # Scripts disponibles y sus configuraciones
        self.available_scripts = {
            'correos': 'run_correos.py',
            'brass': 'run_brass.py', 
            'expedientes': 'run_expedientes.py',
            'riesgos': 'run_riesgos.py',
            'no_conformidades': 'run_no_conformidades.py',
            'agedys': 'run_agedys.py',
            'tareas': 'run_tareas.py'
        }
        
        # Scripts de tareas diarias (orden de ejecución)
        self.daily_scripts = ['riesgos', 'brass', 'expedientes', 'no_conformidades', 'agedys']
        
        # Scripts de tareas continuas
        self.continuous_scripts = ['correos', 'tareas']
        
        # Mostrar información de inicialización
        mode_info = "MODO VERBOSE" if self.verbose_mode else "MODO NORMAL"
        logger.info(f"🚀 Master Runner inicializado correctamente - {mode_info}")
        logger.info(f"📁 Directorio de scripts: {self.scripts_dir}")
        logger.info(f"📅 Archivo de festivos: {self.festivos_file}")
        logger.info(f"⚙️  Scripts disponibles: {list(self.available_scripts.keys())}")
        
        if self.verbose_mode:
            logger.info("🔍 MODO VERBOSE ACTIVADO - Se mostrarán todos los detalles de ejecución")
            logger.info(f"📋 Scripts diarios: {self.daily_scripts}")
            logger.info(f"📧 Scripts continuos: {self.continuous_scripts}")
    
    def _load_config(self):
        """Carga la configuración desde archivo .env"""
        try:
            # Intentar cargar desde .env
            env_file = self.project_root / "config" / ".env"
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
            
            # Configurar formato detallado
            detailed_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - [Ciclo:%(cycle)s] - %(message)s',
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
            
            # Crear adaptador para incluir información de ciclo
            self.logger_adapter = logging.LoggerAdapter(logger, {'cycle': 0})
            
        except Exception as e:
            logger.error(f"❌ Error configurando logging: {e}")
            self.logger_adapter = logging.LoggerAdapter(logger, {'cycle': 0})
    
    def _update_cycle_context(self):
        """Actualiza el contexto del ciclo en el logger"""
        self.logger_adapter.extra['cycle'] = self.cycle_count
    
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
            else:
                self.logger_adapter.info(f"▶️  Ejecutando {script_name} ({script_file})")
            
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
            
            # Actualizar estadísticas
            self.total_scripts_executed += 1
            
            if result.returncode == 0:
                self.successful_scripts += 1
                
                # Éxito - log detallado en modo verbose
                if self.verbose_mode:
                    self.logger_adapter.info(f"✅ SCRIPT COMPLETADO EXITOSAMENTE: {script_name}")
                    self.logger_adapter.info(f"   ⏱️  Tiempo de ejecución: {execution_time:.2f} segundos")
                    self.logger_adapter.info(f"   📤 Código de salida: {result.returncode}")
                    
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
            self.failed_scripts += 1
            self.total_scripts_executed += 1
            execution_time = self.script_timeout
            
            if self.verbose_mode:
                self.logger_adapter.error(f"⏰ TIMEOUT: {script_name}")
                self.logger_adapter.error(f"   ⏱️  Tiempo transcurrido: {execution_time:.2f} segundos")
                self.logger_adapter.error(f"   🚨 El script excedió el límite de {self.script_timeout} segundos")
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
            self.failed_scripts += 1
            self.total_scripts_executed += 1
            
            if self.verbose_mode:
                self.logger_adapter.error(f"💥 EXCEPCIÓN EN SCRIPT: {script_name}")
                self.logger_adapter.error(f"   🚨 Error: {str(e)}")
                self.logger_adapter.error(f"   📍 Tipo de error: {type(e).__name__}")
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
        """Ejecuta las tareas que se realizan una vez por día laborable"""
        if self.verbose_mode:
            self.logger_adapter.info("🌅 ===== INICIANDO TAREAS DIARIAS =====")
            self.logger_adapter.info(f"   📅 Fecha: {date.today().strftime('%d/%m/%Y')}")
            self.logger_adapter.info(f"   📝 Scripts a ejecutar: {self.daily_scripts}")
            self.logger_adapter.info("   " + "="*50)
        else:
            self.logger_adapter.info("🌅 ===== INICIANDO TAREAS DIARIAS =====")
        
        resultados = {}
        tareas_exitosas = 0
        total_tareas = len(self.daily_scripts)
        tiempo_inicio = datetime.now()
        
        for i, script_name in enumerate(self.daily_scripts, 1):
            if self.verbose_mode:
                self.logger_adapter.info(f"📌 PROCESANDO TAREA DIARIA {i}/{total_tareas}: {script_name}")
            else:
                self.logger_adapter.info(f"📋 Tarea {i}/{total_tareas}: {script_name}")
            
            resultado = self.ejecutar_script(script_name)
            resultados[script_name] = resultado
            
            if resultado['success']:
                tareas_exitosas += 1
            
            if self.verbose_mode:
                status = "✅ EXITOSO" if resultado['success'] else "❌ FALLIDO"
                self.logger_adapter.info(f"   📊 Resultado tarea diaria: {status}")
            
            # No hay delay entre scripts - ejecución secuencial inmediata
        
        # Nota: AGEDYS pendiente de implementación
        
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
        Ejecuta todas las tareas continuas en cada ciclo
        
        Returns:
            Dict[str, bool]: Diccionario con el resultado de cada script
        """
        if self.verbose_mode:
            logger.info("📧 INICIANDO EJECUCIÓN DE TAREAS CONTINUAS")
            logger.info(f"   🔄 Ciclo número: {self.cycle_count}")
            logger.info(f"   📝 Scripts a ejecutar: {self.continuous_scripts}")
            logger.info("   " + "="*50)
        else:
            logger.info("📧 Ejecutando tareas continuas...")
        
        results = {}
        successful_count = 0
        failed_count = 0
        
        for script_name in self.continuous_scripts:
            if self.verbose_mode:
                logger.info(f"📌 PROCESANDO TAREA CONTINUA: {script_name}")
            
            success = self.ejecutar_script(script_name)
            results[script_name] = success
            
            if success:
                successful_count += 1
            else:
                failed_count += 1
            
            if self.verbose_mode:
                status = "✅ EXITOSO" if success else "❌ FALLIDO"
                logger.info(f"   📊 Resultado: {status}")
        
        # Resumen final
        if self.verbose_mode:
            logger.info("📧 RESUMEN DE TAREAS CONTINUAS COMPLETADO")
            logger.info(f"   ✅ Exitosas: {successful_count}")
            logger.info(f"   ❌ Fallidas: {failed_count}")
            logger.info(f"   📊 Total: {len(self.continuous_scripts)}")
            logger.info("   " + "="*50)
        else:
            logger.info(f"📧 Tareas continuas completadas: {successful_count} exitosas, {failed_count} fallidas")
        
        return results
    
    def run(self):
        """Ejecuta el ciclo principal del script maestro"""
        if self.verbose_mode:
            self.logger_adapter.info("🚀 ===== INICIANDO SCRIPT MAESTRO DE PRODUCCIÓN (MODO VERBOSE) =====")
            self.logger_adapter.info(f"📁 Directorio de scripts: {self.scripts_dir}")
            self.logger_adapter.info(f"📅 Archivo de festivos: {self.festivos_file}")
            self.logger_adapter.info(f"⚙️  Configuración de ciclos: {self.cycle_times}")
            self.logger_adapter.info(f"⏰ Timeout de scripts: {self.script_timeout}s")
            self.logger_adapter.info(f"📋 Scripts diarios: {self.daily_scripts}")
            self.logger_adapter.info(f"📧 Scripts continuos: {self.continuous_scripts}")
            self.logger_adapter.info("   " + "="*50)
        else:
            self.logger_adapter.info("🚀 ===== INICIANDO SCRIPT MAESTRO DE PRODUCCIÓN =====")
            self.logger_adapter.info(f"📁 Directorio de scripts: {self.scripts_dir}")
            self.logger_adapter.info(f"📅 Archivo de festivos: {self.festivos_file}")
            self.logger_adapter.info(f"⚙️  Configuración de ciclos: {self.cycle_times}")
        
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
                ejecutar_diarias = (
                    es_laborable_hoy and 
                    hora_actual >= 7 and 
                    (self.last_daily_tasks_date != fecha_actual or not self.daily_tasks_completed)
                )
                
                if ejecutar_diarias:
                    if self.verbose_mode:
                        self.logger_adapter.info("🌅 CONDICIONES PARA TAREAS DIARIAS CUMPLIDAS")
                        self.logger_adapter.info(f"   📅 Última ejecución: {self.last_daily_tasks_date or 'Nunca'}")
                        self.logger_adapter.info(f"   📅 Fecha actual: {fecha_actual}")
                        self.logger_adapter.info("   🚀 Iniciando ejecución de tareas diarias...")
                    else:
                        self.logger_adapter.info("🌅 Ejecutando tareas diarias (primera vez del día)")
                    
                    resultado_diarias = self.ejecutar_tareas_diarias()
                    self.last_daily_tasks_date = fecha_actual
                    self.daily_tasks_completed = True
                    
                    if self.verbose_mode:
                        self.logger_adapter.info("✅ TAREAS DIARIAS MARCADAS COMO COMPLETADAS PARA HOY")
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
                    
                    # Si cambió el día, resetear flag de tareas diarias
                    if date.today() != fecha_actual:
                        self.daily_tasks_completed = False
                        if self.verbose_mode:
                            self.logger_adapter.info("📅 CAMBIO DE DÍA DETECTADO")
                            self.logger_adapter.info("   🔄 Reseteando flag de tareas diarias")
                            self.logger_adapter.info(f"   📅 Nueva fecha: {date.today()}")
                        else:
                            self.logger_adapter.info("📅 Cambio de día detectado, reseteando flag de tareas diarias")
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
                'last_daily_tasks_date': self.last_daily_tasks_date.isoformat() if self.last_daily_tasks_date else None,
                'daily_tasks_completed': self.daily_tasks_completed,
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
  python run_master.py              # Modo normal
  python run_master.py --verbose    # Modo verbose (muestra todos los logs)
  python run_master.py -v           # Modo verbose (forma corta)
        """
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Activar modo verbose para ver todos los detalles de ejecución'
    )
    
    args = parser.parse_args()
    
    try:
        # Crear y ejecutar el script maestro
        master = MasterRunner(verbose=args.verbose)
        master.run()
    except Exception as e:
        logger.error(f"❌ Error fatal en main: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
