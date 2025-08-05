"""
Script maestro simplificado para la ejecución de tareas
Utiliza la nueva arquitectura de tareas con clases base
"""

import os
import sys
import logging
from datetime import datetime, date
from typing import List

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from common.logger import setup_logger
from common.utils import is_workday
from common.task_registry import get_all_daily_tasks, get_all_continuous_tasks
from common.base_task import BaseTask


class MasterTaskRunner:
    """
    Ejecutor maestro de tareas simplificado
    """
    
    def __init__(self):
        """Inicializa el ejecutor maestro"""
        self.logger = setup_logger('master_runner')
        self.daily_tasks = get_all_daily_tasks()
        self.continuous_tasks = get_all_continuous_tasks()
        
        self.logger.info("🚀 Iniciando Master Task Runner")
        self.logger.info(f"📋 Tareas diarias registradas: {len(self.daily_tasks)}")
        self.logger.info(f"🔄 Tareas continuas registradas: {len(self.continuous_tasks)}")
    
    def run_daily_tasks(self) -> tuple[int, int]:
        """
        Ejecuta las tareas diarias si es día laborable
        
        Returns:
            Tupla con (ejecutadas, total)
        """
        if not is_workday(date.today()):
            self.logger.info("📅 Hoy no es día laborable, omitiendo tareas diarias")
            return 0, len(self.daily_tasks)
        
        self.logger.info("💼 Es día laborable, verificando tareas diarias...")
        
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
                    
            except Exception as e:
                self.logger.error(f"💥 Error procesando tarea {task.name}: {e}")
        
        return ejecutadas, total
    
    def run_continuous_tasks(self) -> tuple[int, int]:
        """
        Ejecuta las tareas continuas (siempre se ejecutan)
        
        Returns:
            Tupla con (ejecutadas, total)
        """
        self.logger.info("🔄 Ejecutando tareas continuas...")
        
        ejecutadas = 0
        total = len(self.continuous_tasks)
        
        for task in self.continuous_tasks:
            try:
                self.logger.info(f"▶️  Ejecutando tarea continua: {task.name}")
                
                if task.ejecutar():
                    self.logger.info(f"✅ Tarea continua {task.name} ejecutada exitosamente")
                    ejecutadas += 1
                else:
                    self.logger.error(f"❌ Error ejecutando tarea continua: {task.name}")
                    
            except Exception as e:
                self.logger.error(f"💥 Error procesando tarea continua {task.name}: {e}")
        
        return ejecutadas, total
    
    def run(self):
        """
        Ejecuta todas las tareas según su tipo
        """
        inicio = datetime.now()
        self.logger.info(f"🎯 Iniciando ejecución de tareas - {inicio.strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # Ejecutar tareas diarias (solo en días laborables)
            diarias_ejecutadas, diarias_total = self.run_daily_tasks()
            
            # Ejecutar tareas continuas (siempre)
            continuas_ejecutadas, continuas_total = self.run_continuous_tasks()
            
            # Resumen final
            total_ejecutadas = diarias_ejecutadas + continuas_ejecutadas
            total_tareas = diarias_total + continuas_total
            
            fin = datetime.now()
            duracion = fin - inicio
            
            self.logger.info("=" * 60)
            self.logger.info("📊 RESUMEN DE EJECUCIÓN")
            self.logger.info("=" * 60)
            self.logger.info(f"📅 Tareas diarias: {diarias_ejecutadas}/{diarias_total}")
            self.logger.info(f"🔄 Tareas continuas: {continuas_ejecutadas}/{continuas_total}")
            self.logger.info(f"🎯 Total ejecutadas: {total_ejecutadas}/{total_tareas}")
            self.logger.info(f"⏱️  Duración: {duracion}")
            self.logger.info(f"📈 Tasa de éxito: {(total_ejecutadas/total_tareas*100):.1f}%")
            self.logger.info("=" * 60)
            
            if total_ejecutadas == total_tareas:
                self.logger.info("🎉 Todas las tareas se ejecutaron exitosamente")
            else:
                self.logger.warning(f"⚠️  {total_tareas - total_ejecutadas} tareas no se ejecutaron correctamente")
            
        except Exception as e:
            self.logger.error(f"💥 Error crítico en la ejecución del master: {e}")
            raise
        
        finally:
            # Cerrar conexiones de todas las tareas
            for task in self.daily_tasks + self.continuous_tasks:
                try:
                    task.close_connections()
                except Exception as e:
                    self.logger.warning(f"⚠️  Error cerrando conexiones de {task.name}: {e}")


def main():
    """Función principal"""
    try:
        runner = MasterTaskRunner()
        runner.run()
        
    except KeyboardInterrupt:
        print("\n🛑 Ejecución interrumpida por el usuario")
        sys.exit(1)
        
    except Exception as e:
        print(f"💥 Error crítico: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()