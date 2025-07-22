#!/usr/bin/env python3
"""
Servidor web para el panel de control del sistema de gestión de tareas
Permite ejecutar módulos y tests desde una interfaz web
"""
import sys
import os
import subprocess
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import threading

# Añadir src al path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from common.config import config

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TaskControlHandler(BaseHTTPRequestHandler):
    """Handler para el servidor del panel de control"""
    
    def do_GET(self):
        """Manejar peticiones GET"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/':
            # Servir el panel HTML
            self.serve_panel()
        elif parsed_path.path == '/api/status':
            # API para obtener el estado del sistema
            self.get_system_status()
        elif parsed_path.path == '/api/environment':
            # API para obtener información del entorno
            self.get_environment_info()
        elif parsed_path.path.startswith('/static/'):
            # Servir archivos estáticos (CSS, JS, etc.)
            self.serve_static_file(parsed_path.path[8:])  # Quitar '/static/'
        else:
            self.send_error(404, "Página no encontrada")
    
    def do_POST(self):
        """Manejar peticiones POST"""
        parsed_path = urlparse(self.path)
        
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
        except (ValueError, KeyError) as e:
            self.send_error(400, f"Error en datos POST: {e}")
            return
        
        if parsed_path.path == '/api/execute':
            # Ejecutar módulo
            self.execute_module(data)
        elif parsed_path.path == '/api/test':
            # Ejecutar tests
            self.execute_tests(data)
        else:
            self.send_error(404, "Endpoint no encontrado")
    
    def serve_panel(self):
        """Servir el panel HTML principal"""
        try:
            panel_file = Path(__file__).parent / 'panel_control.html'
            with open(panel_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
        except Exception as e:
            logger.error(f"Error sirviendo panel: {e}")
            self.send_error(500, f"Error interno del servidor: {e}")
    
    def get_system_status(self):
        """Obtener estado del sistema"""
        try:
            status = {
                'environment': config.environment,
                'timestamp': datetime.now().isoformat(),
                'modules': {
                    'brass': {'status': 'migrado', 'available': True},
                    'noconformidades': {'status': 'pendiente', 'available': False},
                    'riesgos': {'status': 'pendiente', 'available': False},
                    'expedientes': {'status': 'pendiente', 'available': False},
                    'agedys': {'status': 'pendiente', 'available': False}
                },
                'tests': {
                    'total_tests': 49,
                    'coverage': '63%',
                    'last_run': 'N/A'
                }
            }
            
            self.send_json_response(status)
        except Exception as e:
            logger.error(f"Error obteniendo estado: {e}")
            self.send_error(500, f"Error obteniendo estado: {e}")
    
    def get_environment_info(self):
        """Obtener información del entorno"""
        try:
            env_info = {
                'environment': config.environment,
                'db_brass_path': str(config.db_brass_path),
                'db_tareas_path': str(config.db_tareas_path),
                'css_file_path': str(config.css_file_path),
                'log_level': config.log_level,
                'python_version': sys.version
            }
            
            self.send_json_response(env_info)
        except Exception as e:
            logger.error(f"Error obteniendo info entorno: {e}")
            self.send_error(500, f"Error obteniendo info entorno: {e}")
    
    def execute_module(self, data: Dict[str, Any]):
        """Ejecutar un módulo específico"""
        try:
            module_name = data.get('module')
            if not module_name:
                self.send_error(400, "Nombre del módulo requerido")
                return
            
            # Por ahora solo BRASS está disponible
            if module_name != 'brass':
                self.send_json_response({
                    'success': False,
                    'error': f'Módulo {module_name} no disponible aún'
                })
                return
            
            # Ejecutar en hilo separado para no bloquear
            def run_module():
                try:
                    result = subprocess.run(
                        [sys.executable, f'run_{module_name}.py'],
                        capture_output=True,
                        text=True,
                        timeout=300  # 5 minutos timeout
                    )
                    
                    return {
                        'success': result.returncode == 0,
                        'stdout': result.stdout,
                        'stderr': result.stderr,
                        'returncode': result.returncode
                    }
                except subprocess.TimeoutExpired:
                    return {
                        'success': False,
                        'error': 'Timeout: El módulo tardó más de 5 minutos'
                    }
                except Exception as e:
                    return {
                        'success': False,
                        'error': str(e)
                    }
            
            # Ejecutar y devolver resultado
            result = run_module()
            self.send_json_response(result)
            
        except Exception as e:
            logger.error(f"Error ejecutando módulo: {e}")
            self.send_error(500, f"Error ejecutando módulo: {e}")
    
    def execute_tests(self, data: Dict[str, Any]):
        """Ejecutar tests específicos"""
        try:
            test_type = data.get('type', 'all')
            module_name = data.get('module', '')
            
            # Construir comando pytest
            cmd = [sys.executable, '-m', 'pytest']
            
            if test_type == 'unit':
                if module_name:
                    cmd.extend([f'tests/unit/{module_name}/', '-v'])
                else:
                    cmd.extend(['tests/unit/', '-v'])
            elif test_type == 'integration':
                if module_name:
                    cmd.extend([f'tests/integration/{module_name}/', '-v'])
                else:
                    cmd.extend(['tests/integration/', '-v'])
            elif test_type == 'coverage':
                cmd.extend(['tests/', '--cov=src', '--cov-report=term-missing', '-v'])
            else:  # all
                cmd.extend(['tests/', '-v'])
            
            # Ejecutar tests
            def run_tests():
                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=600  # 10 minutos timeout para tests
                    )
                    
                    return {
                        'success': result.returncode == 0,
                        'stdout': result.stdout,
                        'stderr': result.stderr,
                        'returncode': result.returncode,
                        'command': ' '.join(cmd)
                    }
                except subprocess.TimeoutExpired:
                    return {
                        'success': False,
                        'error': 'Timeout: Los tests tardaron más de 10 minutos'
                    }
                except Exception as e:
                    return {
                        'success': False,
                        'error': str(e)
                    }
            
            result = run_tests()
            self.send_json_response(result)
            
        except Exception as e:
            logger.error(f"Error ejecutando tests: {e}")
            self.send_error(500, f"Error ejecutando tests: {e}")
    
    def send_json_response(self, data: Any):
        """Enviar respuesta JSON"""
        response = json.dumps(data, indent=2, ensure_ascii=False)
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))
    
    def serve_static_file(self, filename: str):
        """Servir archivos estáticos"""
        try:
            static_file = Path(__file__).parent / 'static' / filename
            if not static_file.exists():
                self.send_error(404, "Archivo no encontrado")
                return
            
            # Determinar content-type
            if filename.endswith('.css'):
                content_type = 'text/css'
            elif filename.endswith('.js'):
                content_type = 'application/javascript'
            elif filename.endswith('.png'):
                content_type = 'image/png'
            elif filename.endswith('.jpg') or filename.endswith('.jpeg'):
                content_type = 'image/jpeg'
            else:
                content_type = 'application/octet-stream'
            
            with open(static_file, 'rb') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-type', content_type)
            self.end_headers()
            self.wfile.write(content)
            
        except Exception as e:
            logger.error(f"Error sirviendo archivo estático {filename}: {e}")
            self.send_error(500, f"Error sirviendo archivo: {e}")
    
    def log_message(self, format, *args):
        """Personalizar logging de peticiones HTTP"""
        logger.info(f"{self.address_string()} - {format % args}")

def main():
    """Función principal del servidor"""
    # Configuración del servidor
    HOST = 'localhost'
    PORT = 8888
    
    # Crear servidor
    server = HTTPServer((HOST, PORT), TaskControlHandler)
    
    print(f"""
🚀 Servidor Panel de Control iniciado
======================================

🌐 URL: http://{HOST}:{PORT}
📁 Directorio: {Path(__file__).parent}
🔧 Entorno: {config.environment}
📊 Estado: Listo para recibir peticiones

Módulos disponibles:
✅ BRASS - Gestión de equipos de medida

Tests disponibles: 49 tests (63% cobertura)

Para detener el servidor: Ctrl+C
    """)
    
    try:
        # Iniciar servidor
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo servidor...")
        server.server_close()
        print("✅ Servidor detenido correctamente")

if __name__ == "__main__":
    main()
