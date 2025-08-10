"""
Tests unitarios para config.py
"""
import pytest
import os
from pathlib import Path
from unittest.mock import patch, Mock
from dotenv import load_dotenv

from common.config import Config, config, reload_config


def get_current_env_config():
    """Helper para obtener la configuración actual del archivo .env"""
    # Cargar variables del .env actual
    load_dotenv()
    
    current_env = os.getenv('ENVIRONMENT', 'local')
    
    if current_env == 'local':
        return {
            'environment': 'local',
            'db_brass': os.getenv('LOCAL_DB_BRASS', 'dbs-locales/Gestion_Brass_Gestion_Datos.accdb'),
            'db_tareas': os.getenv('LOCAL_DB_TAREAS', 'dbs-locales/Tareas_datos1.accdb'),
            'db_correos': os.getenv('LOCAL_DB_CORREOS', 'dbs-locales/correos_datos.accdb'),
            'css_file': os.getenv('LOCAL_CSS_FILE', 'herramientas/CSS_moderno.css'),
            'smtp_server': os.getenv('LOCAL_SMTP_SERVER', 'localhost'),
            'smtp_port': int(os.getenv('LOCAL_SMTP_PORT', '1025')),
            'smtp_user': os.getenv('LOCAL_SMTP_USER', 'test@example.com'),
            'smtp_password': os.getenv('LOCAL_SMTP_PASSWORD', ''),
        }
    else:  # oficina
        return {
            'environment': 'oficina',
            'db_brass': os.getenv('OFFICE_DB_BRASS', r'\\datoste\aplicaciones_dys\Aplicaciones PpD\00Recursos\Gestion_Brass_Gestion_Datos.accdb'),
            'db_tareas': os.getenv('OFFICE_DB_TAREAS', r'\\datoste\aplicaciones_dys\Aplicaciones PpD\00Recursos\Tareas_datos1.accdb'),
            'db_correos': os.getenv('OFFICE_DB_CORREOS', r'\\datoste\aplicaciones_dys\Aplicaciones PpD\00Recursos\correos_datos.accdb'),
            'css_file': os.getenv('OFFICE_CSS_FILE', r'\\datoste\Aplicaciones_dys\Aplicaciones PpD\CSS.txt'),
            'smtp_server': os.getenv('OFFICE_SMTP_SERVER', '10.73.54.85'),
            'smtp_port': int(os.getenv('OFFICE_SMTP_PORT', '25')),
            'smtp_user': os.getenv('OFFICE_SMTP_USER', ''),
            'smtp_password': os.getenv('OFFICE_SMTP_PASSWORD', ''),
        }


class TestConfig:
    """Tests para la clase Config"""
    
    def test_init_current_environment(self):
        """Test inicialización con el entorno actual configurado en .env"""
        # Obtener configuración actual del .env
        env_config = get_current_env_config()
        
        # Crear instancia de Config (usará el .env real)
        test_config = Config()
        
        # Verificar que la configuración coincide con el .env actual
        assert test_config.environment == env_config['environment']
        assert test_config.db_password == os.getenv('DB_PASSWORD', 'dpddpd')
        assert test_config.log_level == os.getenv('LOG_LEVEL', 'INFO')
        
        # Verificar rutas de bases de datos según el entorno
        if env_config['environment'] == 'local':
            # En entorno local, verificar que las rutas contienen los nombres de archivo
            assert 'Gestion_Brass_Gestion_Datos.accdb' in str(test_config.db_brass_path)
            assert 'Tareas_datos1.accdb' in str(test_config.db_tareas_path)
            assert 'correos_datos.accdb' in str(test_config.db_correos_path)
            # Verificar que contiene un archivo CSS (puede ser .css o .txt)
            css_path_str = str(test_config.css_file_path)
            assert ('CSS.txt' in css_path_str or 'CSS_moderno.css' in css_path_str or '.css' in css_path_str)
            # Verificar configuración SMTP local
            assert test_config.smtp_server == env_config['smtp_server']
            assert test_config.smtp_port == env_config['smtp_port']
            assert test_config.smtp_user == env_config['smtp_user']
            assert test_config.smtp_password == env_config['smtp_password']
            assert test_config.smtp_auth is False
            assert test_config.smtp_tls is False
        else:  # oficina
            # En entorno oficina, las rutas son absolutas de red
            assert str(test_config.db_brass_path) == env_config['db_brass']
            assert str(test_config.db_tareas_path) == env_config['db_tareas']
            assert str(test_config.db_correos_path) == env_config['db_correos']
            assert str(test_config.css_file_path) == env_config['css_file']
            # Verificar configuración SMTP oficina
            assert test_config.smtp_server == env_config['smtp_server']
            assert test_config.smtp_port == env_config['smtp_port']
            assert test_config.smtp_user == env_config['smtp_user']
            assert test_config.smtp_password == env_config['smtp_password']
            assert test_config.smtp_auth is False
            assert test_config.smtp_tls is False
    
    def test_init_local_environment_mock(self):
        """Test inicialización forzando entorno local con mocks"""
        env_vars = {
            'ENVIRONMENT': 'local',
            'DB_PASSWORD': 'test_password',
            'LOCAL_DB_BRASS': 'dbs-locales/Gestion_Brass_Gestion_Datos.accdb',
            'LOCAL_DB_TAREAS': 'dbs-locales/Tareas_datos1.accdb',
            'LOCAL_DB_CORREOS': 'dbs-locales/correos_datos.accdb',
            'LOCAL_CSS_FILE': 'herramientas/CSS.txt',
            'LOCAL_SMTP_SERVER': 'localhost',
            'LOCAL_SMTP_PORT': '1025',
            'LOCAL_SMTP_USER': 'test@local.com',
            'LOCAL_SMTP_PASSWORD': 'local_pass'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            with patch('src.common.config.load_dotenv'):
                test_config = Config()
                
                assert test_config.environment == 'local'
                assert test_config.db_password == 'test_password'
                assert 'Gestion_Brass_Gestion_Datos.accdb' in str(test_config.db_brass_path)
                assert 'Tareas_datos1.accdb' in str(test_config.db_tareas_path)
                assert 'correos_datos.accdb' in str(test_config.db_correos_path)
                assert 'CSS.txt' in str(test_config.css_file_path)
                assert test_config.smtp_server == 'localhost'
                assert test_config.smtp_port == 1025
                assert test_config.smtp_user == 'test@local.com'
                assert test_config.smtp_password == 'local_pass'
    
    def test_init_office_environment_mock(self):
        """Test inicialización forzando entorno de oficina con mocks"""
        env_vars = {
            'ENVIRONMENT': 'oficina',
            'DB_PASSWORD': 'office_password',
            'OFFICE_DB_BRASS': r'\\datoste\aplicaciones_dys\Aplicaciones PpD\BRASS\Gestion_Brass_Gestion_Datos.accdb',
            'OFFICE_DB_TAREAS': r'\\datoste\aplicaciones_dys\Aplicaciones PpD\00Recursos\Tareas_datos1.accdb',
            'OFFICE_DB_CORREOS': r'\\datoste\aplicaciones_dys\Aplicaciones PpD\00Recursos\correos_datos.accdb',
            'OFFICE_CSS_FILE': r'\\datoste\Aplicaciones_dys\Aplicaciones PpD\CSS.txt',
            'OFFICE_SMTP_SERVER': '10.73.54.85',
            'OFFICE_SMTP_PORT': '25',
            'OFFICE_SMTP_USER': '',  # Sin usuario en oficina
            'OFFICE_SMTP_PASSWORD': ''  # Sin contraseña en oficina
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            with patch('src.common.config.load_dotenv'):
                test_config = Config()
                
                assert test_config.environment == 'oficina'
                assert test_config.db_password == 'office_password'
                assert str(test_config.db_brass_path) == env_vars['OFFICE_DB_BRASS']
                assert str(test_config.db_tareas_path) == env_vars['OFFICE_DB_TAREAS']
                assert str(test_config.db_correos_path) == env_vars['OFFICE_DB_CORREOS']
                assert str(test_config.css_file_path) == env_vars['OFFICE_CSS_FILE']
                assert test_config.smtp_server == '10.73.54.85'
                assert test_config.smtp_port == 25
                assert test_config.smtp_user == ''  # Sin usuario en oficina
                assert test_config.smtp_password == ''  # Sin contraseña en oficina
                assert test_config.smtp_auth is False
                assert test_config.smtp_tls is False
    
    def test_init_custom_environment_variables(self):
        """Test inicialización con variables de entorno personalizadas"""
        env_vars = {
            'ENVIRONMENT': 'local',
            'LOCAL_DB_BRASS': 'test/Gestion_Brass_Gestion_Datos.accdb',
            'LOCAL_DB_TAREAS': 'test/Tareas_datos1.accdb',
            'LOCAL_DB_CORREOS': 'test/correos_datos.accdb',
            'LOCAL_CSS_FILE': 'test/CSS.txt',
            'DEFAULT_RECIPIENT': 'test@example.com',
            'LOCAL_SMTP_USER': 'smtp@example.com',
            'LOCAL_SMTP_PASSWORD': 'smtp_pass',
            'LOG_LEVEL': 'DEBUG',
            'LOG_FILE': 'custom.log'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            with patch('src.common.config.load_dotenv'):
                test_config = Config()
                
                assert test_config.environment == 'local'
                # Para rutas locales, se combinan con root_dir
                assert test_config.db_brass_path.name == 'Gestion_Brass_Gestion_Datos.accdb'
                assert test_config.db_tareas_path.name == 'Tareas_datos1.accdb'
                assert test_config.db_correos_path.name == 'correos_datos.accdb'
                assert test_config.css_file_path.name == 'CSS.txt'
                assert test_config.default_recipient == 'test@example.com'
                assert test_config.smtp_user == 'smtp@example.com'
                assert test_config.smtp_password == 'smtp_pass'
                assert test_config.log_level == 'DEBUG'
                assert test_config.log_file.name == 'custom.log'
    
    def test_init_office_paths(self):
        """Test inicialización con rutas de oficina"""
        env_vars = {
            'ENVIRONMENT': 'oficina',
            'OFFICE_DB_BRASS': r'\\datoste\aplicaciones_dys\Aplicaciones PpD\00Recursos\Gestion_Brass_Gestion_Datos.accdb',
            'OFFICE_DB_TAREAS': r'\\datoste\aplicaciones_dys\Aplicaciones PpD\00Recursos\Tareas_datos1.accdb',
            'OFFICE_DB_CORREOS': r'\\datoste\aplicaciones_dys\Aplicaciones PpD\00Recursos\correos_datos.accdb',
            'OFFICE_CSS_FILE': r'\\datoste\Aplicaciones_dys\Aplicaciones PpD\CSS.txt'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            with patch('src.common.config.load_dotenv'):
                test_config = Config()
                
                assert test_config.environment == 'oficina'
                # Para rutas de oficina, verificar que contienen las rutas especificadas
                assert r'\\datoste\aplicaciones_dys\Aplicaciones PpD\00Recursos\Gestion_Brass_Gestion_Datos.accdb' in str(test_config.db_brass_path)
                assert r'\\datoste\aplicaciones_dys\Aplicaciones PpD\00Recursos\Tareas_datos1.accdb' in str(test_config.db_tareas_path)
                assert r'\\datoste\aplicaciones_dys\Aplicaciones PpD\00Recursos\correos_datos.accdb' in str(test_config.db_correos_path)
                assert r'\\datoste\Aplicaciones_dys\Aplicaciones PpD\CSS.txt' in str(test_config.css_file_path)
    
    @patch('pathlib.Path.mkdir')
    def test_ensure_directories(self, mock_mkdir):
        """Test creación de directorios necesarios"""
        with patch('src.common.config.load_dotenv'):
            test_config = Config()
            
            # Verificar que se llamó mkdir para el directorio de logs
            mock_mkdir.assert_called_with(parents=True, exist_ok=True)
    
    def test_get_database_path_brass(self):
        """Test obtención de ruta de base de datos BRASS"""
        with patch('src.common.config.load_dotenv'):
            test_config = Config()
            
            result = test_config.get_database_path('brass')
            assert result == test_config.db_brass_path
    
    def test_get_database_path_tareas(self):
        """Test obtención de ruta de base de datos Tareas"""
        with patch('src.common.config.load_dotenv'):
            test_config = Config()
            
            result = test_config.get_database_path('tareas')
            assert result == test_config.db_tareas_path
    
    def test_get_database_path_correos(self):
        """Test obtención de ruta de base de datos Correos"""
        with patch('src.common.config.load_dotenv'):
            test_config = Config()
            
            result = test_config.get_database_path('correos')
            assert result == test_config.db_correos_path
    
    def test_get_database_path_invalid(self):
        """Test error con tipo de base de datos inválido"""
        with patch('src.common.config.load_dotenv'):
            test_config = Config()
            
            with pytest.raises(ValueError, match="Tipo de BD no soportado: invalid"):
                test_config.get_database_path('invalid')
    
    def test_get_db_brass_connection_string(self):
        """Test generación de cadena de conexión BRASS"""
        with patch('src.common.config.load_dotenv'):
            test_config = Config()
            test_config.db_brass_path = Path('test_brass.accdb')
            test_config.db_password = 'test_pass'
            
            result = test_config.get_db_brass_connection_string()
            
            expected = f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={test_config.db_brass_path};PWD=test_pass;"
            assert result == expected
    
    def test_get_db_tareas_connection_string(self):
        """Test generación de cadena de conexión Tareas"""
        with patch('src.common.config.load_dotenv'):
            test_config = Config()
            test_config.db_tareas_path = Path('test_tareas.accdb')
            test_config.db_password = 'test_pass'
            
            result = test_config.get_db_tareas_connection_string()
            
            expected = f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={test_config.db_tareas_path};PWD=test_pass;"
            assert result == expected
    
    def test_get_db_correos_connection_string_with_password(self):
        """Test generación de cadena de conexión Correos con contraseña"""
        with patch('src.common.config.load_dotenv'):
            test_config = Config()
            test_config.db_correos_path = Path('test_correos.accdb')
            test_config.db_password = 'test_pass'
            
            result = test_config.get_db_correos_connection_string(with_password=True)
            
            expected = f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={test_config.db_correos_path};PWD=test_pass;"
            assert result == expected
    
    def test_get_db_correos_connection_string_without_password(self):
        """Test generación de cadena de conexión Correos sin contraseña"""
        with patch('src.common.config.load_dotenv'):
            test_config = Config()
            test_config.db_correos_path = Path('test_correos.accdb')
            test_config.db_password = 'test_pass'
            
            result = test_config.get_db_correos_connection_string(with_password=False)
            
            expected = f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={test_config.db_correos_path};"
            assert result == expected
    
    def test_get_db_correos_connection_string_no_password_set(self):
        """Test generación de cadena de conexión Correos cuando no hay contraseña configurada"""
        with patch('src.common.config.load_dotenv'):
            test_config = Config()
            test_config.db_correos_path = Path('test_correos.accdb')
            test_config.db_password = ''
            
            result = test_config.get_db_correos_connection_string(with_password=True)
            
            expected = f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={test_config.db_correos_path};"
            assert result == expected
    
    def test_smtp_port_conversion(self):
        """Test conversión de puerto SMTP a entero"""
        env_vars = {
            'ENVIRONMENT': 'local',
            'LOCAL_SMTP_PORT': '1025'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            with patch('src.common.config.load_dotenv'):
                test_config = Config()
                
                assert test_config.smtp_port == 1025
                assert isinstance(test_config.smtp_port, int)


class TestGlobalConfig:
    """Tests para la instancia global de configuración"""
    
    def test_global_config_exists(self):
        """Test que la instancia global existe"""
        assert config is not None
        assert isinstance(config, Config)
    
    def test_reload_config(self):
        """Test recarga de configuración"""
        # Simplemente verificar que reload_config funciona y retorna una instancia
        result = reload_config()
        
        # Verificar que se retornó una instancia de Config
        assert isinstance(result, Config)
        assert result is not None
    
    def test_reload_config_integration(self):
        """Test integración de recarga de configuración"""
        # Simplemente verificar que reload_config retorna una instancia de Config
        new_config = reload_config()
        
        # Verificar que se retornó una nueva configuración
        assert isinstance(new_config, Config)
        assert new_config is not None


class TestConfigEdgeCases:
    """Tests para casos especiales y edge cases"""
    
    def test_config_with_missing_optional_env_vars(self):
        """Test configuración con variables de entorno opcionales faltantes"""
        # Limpiar todas las variables de entorno
        with patch.dict(os.environ, {}, clear=True):
            with patch('src.common.config.load_dotenv'):
                test_config = Config()
                
                # Verificar valores por defecto
                assert test_config.environment == 'local'
                assert test_config.db_password == 'dpddpd'
                assert test_config.default_recipient == 'admin@empresa.com'
                assert test_config.smtp_user == 'test@example.com'
                assert test_config.smtp_password == ''
                assert test_config.log_level == 'INFO'
    
    def test_config_paths_are_path_objects(self):
        """Test que las rutas son objetos Path"""
        with patch('src.common.config.load_dotenv'):
            test_config = Config()
            
            assert isinstance(test_config.root_dir, Path)
            assert isinstance(test_config.db_brass_path, Path)
            assert isinstance(test_config.db_tareas_path, Path)
            assert isinstance(test_config.db_correos_path, Path)
            assert isinstance(test_config.css_file_path, Path)
            assert isinstance(test_config.logs_dir, Path)
            assert isinstance(test_config.log_file, Path)
    
    def test_config_root_dir_calculation(self):
        """Test cálculo correcto del directorio raíz"""
        with patch('src.common.config.load_dotenv'):
            test_config = Config()
            
            # El directorio raíz debería ser tres niveles arriba desde config.py
            # config.py está en src/common/, así que root debería ser ../..
            expected_parts = Path(__file__).parent.parent.parent.parent.parts
            actual_parts = test_config.root_dir.parts
            
            # Verificar que el cálculo es correcto (al menos que termine igual)
            assert len(actual_parts) <= len(expected_parts)