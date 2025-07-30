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

Mejoras implementadas:
- Sin delays entre scripts individuales (ejecución secuencial)
- Sistema de logging mejorado con diferentes niveles
- Configuración centralizada en .env
- Mejor manejo de errores y estado

Autor: Sistema de Automatización
Fecha: 2024
"""

import json
import logging
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, date
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
    
    def __init__(self):
        self.running = True
        
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
            'no_conformidades': 'run_no_conformidades.py'
        }
        
        # Scripts de tareas diarias (orden de ejecución)
        self.daily_scripts = ['riesgos', 'brass', 'expedientes', 'no_conformidades']
        
        # Scripts de tareas continuas
        self.continuous_scripts = ['correos']
        
        logger.info("🚀 Master Runner inicializado correctamente")
        logger.info(f"📁 Directorio de scripts: {self.scripts_dir}")
        logger.info(f"📅 Archivo de festivos: {self.festivos_file}")
        logger.info(f"⚙️  Scripts disponibles: {list(self.available_scripts.keys())}")
    
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
                self.logger_adapter.info(f"✅ {script_name} completado exitosamente en {execution_time:.1f}s")
                
                # Log de output si hay información relevante
                if result.stdout and result.stdout.strip():
                    self.logger_adapter.debug(f"Output de {script_name}: {result.stdout.strip()}")
                
                return {
                    'success': True,
                    'duration': execution_time,
                    'output': result.stdout,
                    'error': '',
                    'return_code': result.returncode
                }
            else:
                self.failed_scripts += 1
                self.logger_adapter.error(f"❌ {script_name} falló con código {result.returncode} en {execution_time:.1f}s")
                
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
        self.logger_adapter.info("🌅 ===== INICIANDO TAREAS DIARIAS =====")
        
        resultados = {}
        tareas_exitosas = 0
        total_tareas = len(self.daily_scripts)
        tiempo_inicio = datetime.now()
        
        for i, script_name in enumerate(self.daily_scripts, 1):
            self.logger_adapter.info(f"📋 Tarea {i}/{total_tareas}: {script_name}")
            
            resultado = self.ejecutar_script(script_name)
            resultados[script_name] = resultado
            
            if resultado['success']:
                tareas_exitosas += 1
            
            # No hay delay entre scripts - ejecución secuencial inmediata
        
        # Tareas no implementadas aún (solo log informativo)
        self.logger_adapter.info("📋 NoConformidades - No implementado aún")
        self.logger_adapter.info("📋 AGEDYS - No implementado aún")
        
        tiempo_total = (datetime.now() - tiempo_inicio).total_seconds()
        
        self.logger_adapter.info(f"✅ TAREAS DIARIAS COMPLETADAS: {tareas_exitosas}/{total_tareas} exitosas en {tiempo_total:.1f}s")
        
        return {
            'success': tareas_exitosas > 0,
            'total_tasks': total_tareas,
            'successful_tasks': tareas_exitosas,
            'failed_tasks': total_tareas - tareas_exitosas,
            'duration': tiempo_total,
            'results': resultados
        }
    
    def ejecutar_tareas_continuas(self) -> Dict[str, any]:
        """Ejecuta las tareas que se realizan en cada ciclo"""
        self.logger_adapter.info("📧 ===== INICIANDO TAREAS CONTINUAS =====")
        
        resultados = {}
        tareas_exitosas = 0
        total_tareas = len(self.continuous_scripts)
        tiempo_inicio = datetime.now()
        
        for script_name in self.continuous_scripts:
            self.logger_adapter.info(f"📧 Ejecutando tarea continua: {script_name}")
            
            resultado = self.ejecutar_script(script_name)
            resultados[script_name] = resultado
            
            if resultado['success']:
                tareas_exitosas += 1
            
            # No hay delay entre scripts - ejecución secuencial inmediata
        
        tiempo_total = (datetime.now() - tiempo_inicio).total_seconds()
        
        self.logger_adapter.info(f"✅ TAREAS CONTINUAS COMPLETADAS: {tareas_exitosas}/{total_tareas} exitosas en {tiempo_total:.1f}s")
        
        return {
            'success': tareas_exitosas > 0,
            'total_tasks': total_tareas,
            'successful_tasks': tareas_exitosas,
            'failed_tasks': total_tareas - tareas_exitosas,
            'duration': tiempo_total,
            'results': resultados
        }
    
    def run(self):
        """Ejecuta el ciclo principal del script maestro"""
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
                    self.logger_adapter.info("🌅 Ejecutando tareas diarias (primera vez del día)")
                    resultado_diarias = self.ejecutar_tareas_diarias()
                    self.last_daily_tasks_date = fecha_actual
                    self.daily_tasks_completed = True
                else:
                    self.logger_adapter.info("⏭️  Saltando tareas diarias (ya ejecutadas hoy o fuera de horario)")
                
                # Ejecutar tareas continuas (siempre)
                resultado_continuas = self.ejecutar_tareas_continuas()
                
                # Calcular tiempo total del ciclo
                tiempo_ciclo = (datetime.now() - ciclo_inicio).total_seconds()
                
                # Calcular tiempo de espera hasta el próximo ciclo
                tiempo_espera = self.get_tiempo_espera()
                
                self.logger_adapter.info(f"📊 RESUMEN CICLO {self.cycle_count}:")
                self.logger_adapter.info(f"   ⏱️  Duración del ciclo: {tiempo_ciclo:.1f}s")
                self.logger_adapter.info(f"   📈 Scripts ejecutados en total: {self.total_scripts_executed}")
                self.logger_adapter.info(f"   ✅ Scripts exitosos: {self.successful_scripts}")
                self.logger_adapter.info(f"   ❌ Scripts fallidos: {self.failed_scripts}")
                self.logger_adapter.info(f"   ⏰ Próximo ciclo en: {tiempo_espera//60} minutos")
                
                # Actualizar estado
                self._actualizar_estado()
                
                # Esperar con verificación periódica para poder responder a señales
                self.logger_adapter.info(f"😴 Esperando {tiempo_espera//60} minutos hasta el próximo ciclo...")
                tiempo_restante = tiempo_espera
                
                while tiempo_restante > 0 and self.running:
                    sleep_time = min(60, tiempo_restante)  # Verificar cada minuto
                    time.sleep(sleep_time)
                    tiempo_restante -= sleep_time
                    
                    # Si cambió el día, resetear flag de tareas diarias
                    if date.today() != fecha_actual:
                        self.daily_tasks_completed = False
                        self.logger_adapter.info("📅 Cambio de día detectado, reseteando flag de tareas diarias")
                        break
                        
        except KeyboardInterrupt:
            self.logger_adapter.info("⚠️  Interrupción por teclado detectada")
        except Exception as e:
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
    try:
        # Crear y ejecutar el script maestro
        master = MasterRunner()
        master.run()
    except Exception as e:
        logger.error(f"❌ Error fatal en main: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
