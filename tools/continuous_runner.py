"""
Sistema de ejecución continua de scripts
Equivalente a un servicio Windows para mantener scripts ejecutándose
"""
import time
import logging
import threading
import signal
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Callable, Optional
import importlib
import traceback
import json

logger = logging.getLogger(__name__)

class ContinuousRunner:
    """Ejecutor continuo de scripts"""
    
    def __init__(self):
        """Inicializa el runner continuo."""
        self.running = True
        self.scripts = {}
        self.threads = {}
        
        # Usar ruta absoluta basada en el directorio del proyecto
        project_root = Path(__file__).parent.parent
        self.status_file = project_root / 'logs' / 'runner_status.json'
        
        # Asegurar que el directorio de logs existe
        self.status_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Configurar logging con ruta absoluta
        log_file = project_root / 'logs' / 'continuous_runner.log'
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        # Configurar manejo de señales
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def register_script(self, name: str, module_path: str, interval_minutes: int, 
                       enabled: bool = True, max_retries: int = 3):
        """Registra un script para ejecución continua"""
        self.scripts[name] = {
            'module_path': module_path,
            'interval_minutes': interval_minutes,
            'enabled': enabled,
            'max_retries': max_retries,
            'last_run': None,
            'last_success': None,
            'consecutive_failures': 0,
            'total_executions': 0,
            'total_failures': 0
        }
        logger.info(f"Script registrado: {name} (cada {interval_minutes} min)")
    
    def start(self):
        """Inicia la ejecución continua de todos los scripts"""
        logger.info("🚀 Iniciando ejecutor continuo de scripts")
        
        # Crear threads para cada script
        for script_name, config in self.scripts.items():
            if config['enabled']:
                thread = threading.Thread(
                    target=self._run_script_loop,
                    args=(script_name, config),
                    name=f"Script-{script_name}",
                    daemon=True
                )
                self.threads[script_name] = thread
                thread.start()
                logger.info(f"Thread iniciado para {script_name}")
        
        # Thread para actualizar estado
        status_thread = threading.Thread(
            target=self._status_updater,
            name="StatusUpdater",
            daemon=True
        )
        status_thread.start()
        
        # Mantener el proceso principal vivo
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Interrupción detectada")
        finally:
            self.stop()
    
    def stop(self):
        """Detiene la ejecución de todos los scripts"""
        logger.info("🛑 Deteniendo ejecutor continuo...")
        self.running = False
        
        # Esperar que terminen los threads
        for script_name, thread in self.threads.items():
            if thread.is_alive():
                logger.info(f"Esperando que termine {script_name}...")
                thread.join(timeout=5)
        
        logger.info("✅ Ejecutor continuo detenido")
    
    def _run_script_loop(self, script_name: str, config: Dict[str, Any]):
        """Loop de ejecución de un script específico"""
        logger.info(f"Iniciando loop para {script_name}")
        
        while self.running:
            try:
                # Verificar si es tiempo de ejecutar
                if self._should_run_script(script_name, config):
                    logger.info(f"▶️  Ejecutando {script_name}")
                    
                    start_time = datetime.now()
                    success = self._execute_script(script_name, config)
                    execution_time = (datetime.now() - start_time).total_seconds()
                    
                    # Actualizar estadísticas
                    config['last_run'] = start_time
                    config['total_executions'] += 1
                    
                    if success:
                        config['last_success'] = start_time
                        config['consecutive_failures'] = 0
                        logger.info(f"✅ {script_name} completado en {execution_time:.1f}s")
                    else:
                        config['consecutive_failures'] += 1
                        config['total_failures'] += 1
                        logger.error(f"❌ {script_name} falló (fallos consecutivos: {config['consecutive_failures']})")
                        
                        # Si hay muchos fallos consecutivos, aumentar intervalo temporalmente
                        if config['consecutive_failures'] >= config['max_retries']:
                            logger.warning(f"🔄 {script_name}: demasiados fallos, esperando más tiempo")
                            time.sleep(config['interval_minutes'] * 60 * 2)  # Doble tiempo
                
                # Esperar antes de la siguiente verificación
                time.sleep(30)  # Revisar cada 30 segundos
                
            except Exception as e:
                logger.error(f"Error en loop de {script_name}: {e}")
                time.sleep(60)  # Esperar un minuto antes de reintentar
    
    def _should_run_script(self, script_name: str, config: Dict[str, Any]) -> bool:
        """Determina si un script debe ejecutarse ahora"""
        if not config['enabled']:
            return False
        
        # Primera ejecución
        if config['last_run'] is None:
            return True
        
        # Verificar intervalo
        time_since_last = datetime.now() - config['last_run']
        return time_since_last >= timedelta(minutes=config['interval_minutes'])
    
    def _execute_script(self, script_name: str, config: Dict[str, Any]) -> bool:
        """Ejecuta un script específico"""
        try:
            # Importar dinámicamente el módulo
            module = importlib.import_module(config['module_path'])
            
            # Recargar el módulo para obtener cambios
            importlib.reload(module)
            
            # Ejecutar la función main del script
            if hasattr(module, 'main'):
                module.main()
                return True
            else:
                logger.error(f"Script {script_name} no tiene función main()")
                return False
                
        except Exception as e:
            logger.error(f"Error ejecutando {script_name}: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def _status_updater(self):
        """Actualiza archivo de estado periódicamente"""
        while self.running:
            try:
                status = {
                    'timestamp': datetime.now().isoformat(),
                    'running': self.running,
                    'scripts': {}
                }
                
                for script_name, config in self.scripts.items():
                    status['scripts'][script_name] = {
                        'enabled': config['enabled'],
                        'interval_minutes': config['interval_minutes'],
                        'last_run': config['last_run'].isoformat() if config['last_run'] else None,
                        'last_success': config['last_success'].isoformat() if config['last_success'] else None,
                        'consecutive_failures': config['consecutive_failures'],
                        'total_executions': config['total_executions'],
                        'total_failures': config['total_failures']
                    }
                
                # Escribir estado a archivo
                self.status_file.parent.mkdir(exist_ok=True)
                with open(self.status_file, 'w', encoding='utf-8') as f:
                    json.dump(status, f, indent=2, ensure_ascii=False)
                
            except Exception as e:
                logger.error(f"Error actualizando estado: {e}")
            
            time.sleep(60)  # Actualizar cada minuto
    
    def _signal_handler(self, signum, frame):
        """Maneja señales del sistema"""
        logger.info(f"Señal {signum} recibida, deteniendo...")
        self.running = False


def main():
    """Función principal"""
    runner = ContinuousRunner()
    
    # Registrar scripts - configurar según necesidades
    
    # Script de correos no enviados (cada 15 minutos)
    runner.register_script(
        name="correos_no_enviados",
        module_path="scripts.enviar_correo_no_enviado",
        interval_minutes=15,
        enabled=True
    )
    
    # Script BRASS (cada 30 minutos)
    runner.register_script(
        name="brass_calibraciones",
        module_path="scripts.brass_script",  # Se creará
        interval_minutes=30,
        enabled=True
    )
    
    # Script de Tareas (cada 60 minutos)
    runner.register_script(
        name="tareas_pendientes",
        module_path="scripts.tareas_script",  # Se creará
        interval_minutes=60,
        enabled=True
    )
    
    # Script de Gestión de Riesgos (cada 2 horas)
    runner.register_script(
        name="gestion_riesgos",
        module_path="scripts.riesgos_script",  # Se creará
        interval_minutes=120,
        enabled=True
    )
    
    # Scripts adicionales según necesidades
    # runner.register_script(...)
    
    # Iniciar ejecución continua
    logger.info("Sistema de scripts continuos iniciado")
    runner.start()


if __name__ == "__main__":
    # Crear directorio de logs
    Path("logs").mkdir(exist_ok=True)
    
    main()
