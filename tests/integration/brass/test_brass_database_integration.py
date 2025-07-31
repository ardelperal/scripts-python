"""
Tests de integración de base de datos para BRASS
Estos tests verifican la conectividad y operaciones con bases de datos reales locales
"""
import pytest
import sys
import os
from datetime import date, datetime, timedelta

# Agregar el directorio src al path para imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
src_dir = os.path.join(project_root, 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from common.config import config
from common.database import AccessDatabase


class TestBrassDatabaseIntegration:
    """Tests de integración con bases de datos reales para BRASS"""
    
    def test_database_connectivity(self, local_brass_manager):
        """Test: Conectividad básica con bases de datos de BRASS"""
        # Test conexión a base de datos BRASS
        result_brass = local_brass_manager.db.execute_query("SELECT COUNT(*) as total FROM TbEquiposMedida")
        assert result_brass is not None
        assert len(result_brass) > 0
        assert 'total' in result_brass[0]
        
        # Test conexión a base de datos de tareas
        result_tareas = local_brass_manager.tareas_db.execute_query("SELECT COUNT(*) as total FROM TbTareas")
        assert result_tareas is not None
        assert len(result_tareas) > 0
        assert 'total' in result_tareas[0]
    
    def test_equipos_medida_structure(self, local_brass_manager):
        """Test: Verificar estructura de tabla TbEquiposMedida"""
        query = """
        SELECT TOP 1 IDEquipoMedida, NOMBRE, NS, PN, MARCA, MODELO, FechaFinServicio
        FROM TbEquiposMedida
        ORDER BY IDEquipoMedida
        """
        result = local_brass_manager.db.execute_query(query)
        
        if result:
            equipo = result[0]
            # Verificar campos esperados
            expected_fields = ['IDEquipoMedida', 'NOMBRE', 'NS', 'PN', 'MARCA', 'MODELO']
            for field in expected_fields:
                assert field in equipo, f"Campo {field} no encontrado en TbEquiposMedida"
    
    def test_calibraciones_structure(self, local_brass_manager):
        """Test: Verificar estructura de tabla TbEquiposMedidaCalibraciones"""
        query = """
        SELECT TOP 1 IDCalibracion, IDEquipoMedida, FechaFinCalibracion
        FROM TbEquiposMedidaCalibraciones
        ORDER BY IDCalibracion
        """
        result = local_brass_manager.db.execute_query(query)
        
        if result:
            calibracion = result[0]
            # Verificar campos esperados
            expected_fields = ['IDCalibracion', 'IDEquipoMedida', 'FechaFinCalibracion']
            for field in expected_fields:
                assert field in calibracion, f"Campo {field} no encontrado en TbEquiposMedidaCalibraciones"
    
    def test_equipos_activos_query(self, local_brass_manager):
        """Test: Consulta de equipos activos (sin fecha fin de servicio)"""
        query = """
        SELECT IDEquipoMedida, NOMBRE, NS, PN, MARCA, MODELO
        FROM TbEquiposMedida 
        WHERE FechaFinServicio IS NULL
        """
        result = local_brass_manager.db.execute_query(query)
        
        # Debe devolver una lista (puede estar vacía)
        assert isinstance(result, list)
        
        # Si hay equipos, verificar estructura
        if result:
            equipo = result[0]
            assert 'IDEquipoMedida' in equipo
            assert 'NOMBRE' in equipo
    
    def test_calibracion_vigente_query(self, local_brass_manager):
        """Test: Consulta de calibraciones vigentes"""
        # Primero obtener un equipo
        equipos_query = """
        SELECT IDEquipoMedida
        FROM TbEquiposMedida 
        WHERE FechaFinServicio IS NULL
        ORDER BY IDEquipoMedida
        """
        equipos = local_brass_manager.db.execute_query(equipos_query)
        
        if equipos:
            id_equipo = equipos[0]['IDEquipoMedida']
            
            # Consultar calibraciones para ese equipo
            calibracion_query = f"""
            SELECT FechaFinCalibracion
            FROM TbEquiposMedidaCalibraciones 
            WHERE IDEquipoMedida = {id_equipo}
            ORDER BY IDCalibracion DESC
            """
            result = local_brass_manager.db.execute_query(calibracion_query)
            
            # Debe devolver una lista (puede estar vacía)
            assert isinstance(result, list)
    
    def test_task_completion_check(self, local_brass_manager):
        """Test: Verificar consulta de finalización de tareas"""
        query = """
        SELECT Fecha
        FROM TbTareas 
        WHERE Tarea='BRASSDiario' AND Realizado='Sí'
        ORDER BY Fecha DESC
        """
        result = local_brass_manager.tareas_db.execute_query(query)
        
        # Debe devolver una lista (puede estar vacía)
        assert isinstance(result, list)
        
        # Si hay registros, verificar estructura
        if result:
            tarea = result[0]
            assert 'Fecha' in tarea
    
    def test_correos_enviados_structure(self, local_brass_manager):
        """Test: Verificar estructura de tabla TbCorreosEnviados"""
        query = """
        SELECT TOP 1 IDCorreo, Aplicacion, Asunto, Cuerpo, Destinatarios, FechaGrabacion
        FROM TbCorreosEnviados
        WHERE Aplicacion = 'BRASS'
        ORDER BY IDCorreo
        """
        result = local_brass_manager.tareas_db.execute_query(query)
        
        if result:
            correo = result[0]
            # Verificar campos esperados
            expected_fields = ['IDCorreo', 'Aplicacion', 'Asunto', 'Cuerpo', 'Destinatarios']
            for field in expected_fields:
                assert field in correo, f"Campo {field} no encontrado en TbCorreosEnviados"
    
    def test_max_id_correo_query(self, local_brass_manager):
        """Test: Consulta de máximo ID de correo"""
        query = """
        SELECT MAX(IDCorreo) AS Maximo
        FROM TbCorreosEnviados
        """
        result = local_brass_manager.tareas_db.execute_query(query)
        
        assert result is not None
        assert len(result) > 0
        assert 'Maximo' in result[0]
        
        # El máximo puede ser None si no hay registros
        maximo = result[0]['Maximo']
        if maximo is not None:
            assert isinstance(maximo, int)
    
    def test_usuarios_administradores_query(self, local_brass_manager):
        """Test: Consulta de usuarios administradores"""
        query = """
        SELECT TOP 5 CorreoUsuario
        FROM TbUsuariosAplicaciones 
        ORDER BY CorreoUsuario
        """
        result = local_brass_manager.tareas_db.execute_query(query)
        
        # Debe devolver una lista (puede estar vacía)
        assert isinstance(result, list)
        
        # Si hay usuarios, verificar estructura
        if result:
            usuario = result[0]
            assert 'CorreoUsuario' in usuario
    
    def test_sql_injection_protection(self, local_brass_manager):
        """Test: Protección contra inyección SQL"""
        # Intentar una consulta con caracteres potencialmente peligrosos
        malicious_input = "'; DROP TABLE TbEquiposMedida; --"
        
        # Esta consulta debe fallar de forma segura
        with pytest.raises(Exception):
            query = f"SELECT * FROM TbEquiposMedida WHERE NOMBRE = '{malicious_input}'"
            local_brass_manager.db.execute_query(query)
    
    def test_database_performance(self, local_brass_manager):
        """Test: Rendimiento básico de consultas"""
        import time
        
        queries = [
            "SELECT COUNT(*) as total FROM TbEquiposMedida",
            "SELECT COUNT(*) as total FROM TbEquiposMedidaCalibraciones",
            "SELECT COUNT(*) as total FROM TbTareas WHERE Tarea='BRASSDiario'"
        ]
        
        for query in queries:
            start_time = time.time()
            if 'TbTareas' in query:
                result = local_brass_manager.tareas_db.execute_query(query)
            else:
                result = local_brass_manager.db.execute_query(query)
            end_time = time.time()
            
            # Verificar que la consulta se ejecutó
            assert result is not None
            
            # Verificar que no tardó más de 5 segundos
            execution_time = end_time - start_time
            assert execution_time < 5.0, f"Consulta tardó {execution_time:.2f} segundos"
    
    def test_css_loading_real_file(self, local_brass_manager):
        """Test: Carga real del archivo CSS"""
        css_path = config.root_dir / 'herramientas' / 'CSS1.css'
        
        if css_path.exists():
            with open(css_path, 'r', encoding='utf-8') as f:
                css_content = f.read()
            
            assert len(css_content) > 0
            assert 'body' in css_content or 'table' in css_content
    
    def test_complete_brass_workflow_real_data(self, local_brass_manager):
        """Test: Flujo completo con datos reales"""
        # 1. Verificar equipos activos
        equipos_query = """
        SELECT IDEquipoMedida, NOMBRE
        FROM TbEquiposMedida 
        WHERE FechaFinServicio IS NULL
        """
        equipos = local_brass_manager.db.execute_query(equipos_query)
        assert isinstance(equipos, list)
        
        # 2. Si hay equipos, verificar calibraciones
        if equipos:
            id_equipo = equipos[0]['IDEquipoMedida']
            
            calibracion_query = f"""
            SELECT FechaFinCalibracion
            FROM TbEquiposMedidaCalibraciones 
            WHERE IDEquipoMedida = {id_equipo}
            ORDER BY IDCalibracion DESC
            """
            calibraciones = local_brass_manager.db.execute_query(calibracion_query)
            assert isinstance(calibraciones, list)
        
        # 3. Verificar estado de tareas
        tarea_query = """
        SELECT Fecha, Realizado
        FROM TbTareas 
        WHERE Tarea='BRASSDiario'
        ORDER BY Fecha DESC
        """
        tareas = local_brass_manager.tareas_db.execute_query(tarea_query)
        assert isinstance(tareas, list)
        
        # 4. Verificar estructura de correos
        correo_query = """
        SELECT COUNT(*) as total
        FROM TbCorreosEnviados
        WHERE Aplicacion = 'BRASS'
        """
        correos = local_brass_manager.tareas_db.execute_query(correo_query)
        assert isinstance(correos, list)
        assert 'total' in correos[0]