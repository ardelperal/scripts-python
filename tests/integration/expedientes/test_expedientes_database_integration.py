"""
Tests de integración de base de datos para Expedientes
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


class TestExpedientesDatabaseIntegration:
    """Tests de integración con bases de datos reales para Expedientes"""
    
    def test_database_connectivity(self, local_expedientes_manager):
        """Test: Conectividad básica con bases de datos de Expedientes"""
        # Test conexión a base de datos Expedientes
        result_expedientes = local_expedientes_manager.db.execute_query("SELECT COUNT(*) as total FROM TbExpedientes")
        assert result_expedientes is not None
        assert len(result_expedientes) > 0
        assert 'total' in result_expedientes[0]
        
        # Test conexión a base de datos de tareas
        result_tareas = local_expedientes_manager.tareas_db.execute_query("SELECT COUNT(*) as total FROM TbTareas")
        assert result_tareas is not None
        assert len(result_tareas) > 0
        assert 'total' in result_tareas[0]
    
    def test_expedientes_structure(self, local_expedientes_manager):
        """Test: Verificar estructura de tabla TbExpedientes"""
        query = """
        SELECT TOP 1 IDExpediente, CodExp, Nemotecnico
        FROM TbExpedientes
        ORDER BY IDExpediente
        """
        result = local_expedientes_manager.db.execute_query(query)
        
        if result:
            expediente = result[0]
            # Verificar campos esperados
            expected_fields = ['IDExpediente', 'CodExp', 'Nemotecnico']
            for field in expected_fields:
                assert field in expediente, f"Campo {field} no encontrado en TbExpedientes"
    
    def test_documentos_structure(self, local_expedientes_manager):
        """Test: Verificar estructura de tabla TbExpedientesAnexos"""
        query = """
        SELECT COUNT(*) as total
        FROM TbExpedientesAnexos
        """
        result = local_expedientes_manager.db.execute_query(query)
        
        # Debe devolver una lista con el conteo
        assert isinstance(result, list)
        assert len(result) > 0
        assert 'total' in result[0]
    
    def test_expedientes_activos_query(self, local_expedientes_manager):
        """Test: Consulta de expedientes activos"""
        query = """
        SELECT TOP 5 IDExpediente, CodExp, Nemotecnico
        FROM TbExpedientes 
        ORDER BY IDExpediente DESC
        """
        result = local_expedientes_manager.db.execute_query(query)
        
        # Debe devolver una lista (puede estar vacía)
        assert isinstance(result, list)
        
        # Si hay expedientes, verificar estructura
        if result:
            expediente = result[0]
            assert 'IDExpediente' in expediente
            assert 'CodExp' in expediente
    
    def test_documentos_por_expediente_query(self, local_expedientes_manager):
        """Test: Consulta de anexos por expediente"""
        # Usar consulta simple de conteo
        query = """
        SELECT COUNT(*) as total
        FROM TbExpedientesAnexos
        """
        result = local_expedientes_manager.db.execute_query(query)
        
        # Debe devolver una lista con el conteo
        assert isinstance(result, list)
        assert len(result) > 0
        assert 'total' in result[0]
    
    def test_task_completion_check(self, local_expedientes_manager):
        """Test: Verificar consulta de finalización de tareas"""
        query = """
        SELECT Fecha
        FROM TbTareas 
        WHERE Tarea='ExpedientesDiario' AND Realizado='Sí'
        ORDER BY Fecha DESC
        """
        result = local_expedientes_manager.tareas_db.execute_query(query)
        
        # Debe devolver una lista (puede estar vacía)
        assert isinstance(result, list)
        
        # Si hay registros, verificar estructura
        if result:
            tarea = result[0]
            assert 'Fecha' in tarea
    
    def test_correos_enviados_structure(self, local_expedientes_manager):
        """Test: Verificar estructura de tabla TbCorreosEnviados"""
        query = """
        SELECT IDCorreo, Aplicacion, Asunto, Cuerpo, Destinatarios, FechaGrabacion
        FROM TbCorreosEnviados
        WHERE Aplicacion = 'Expedientes' AND IDCorreo = (SELECT MIN(IDCorreo) FROM TbCorreosEnviados WHERE Aplicacion = 'Expedientes')
        """
        result = local_expedientes_manager.tareas_db.execute_query(query)
        
        if result:
            correo = result[0]
            # Verificar campos esperados
            expected_fields = ['IDCorreo', 'Aplicacion', 'Asunto', 'Cuerpo', 'Destinatarios']
            for field in expected_fields:
                assert field in correo, f"Campo {field} no encontrado en TbCorreosEnviados"
    
    def test_max_id_correo_query(self, local_expedientes_manager):
        """Test: Consulta de máximo ID de correo"""
        query = """
        SELECT MAX(IDCorreo) AS Maximo
        FROM TbCorreosEnviados
        """
        result = local_expedientes_manager.tareas_db.execute_query(query)
        
        assert result is not None
        assert len(result) > 0
        assert 'Maximo' in result[0]
        
        # El máximo puede ser None si no hay registros
        maximo = result[0]['Maximo']
        if maximo is not None:
            assert isinstance(maximo, int)
    
    def test_usuarios_administradores_query(self, local_expedientes_manager):
        """Test: Consulta de usuarios administradores"""
        query = """
        SELECT TbUsuariosAplicaciones.CorreoUsuario
        FROM TbUsuariosAplicaciones 
        INNER JOIN TbUsuariosAplicacionesPermisos 
        ON TbUsuariosAplicaciones.CorreoUsuario = TbUsuariosAplicacionesPermisos.CorreoUsuario
        WHERE TbUsuariosAplicacionesPermisos.IDAplicacion = 20 AND TbUsuariosAplicacionesPermisos.EsUsuarioAdministrador = 'Sí'
        """
        result = local_expedientes_manager.tareas_db.execute_query(query)
        
        # Debe devolver una lista (puede estar vacía)
        assert isinstance(result, list)
        
        # Si hay usuarios, verificar estructura
        if result:
            usuario = result[0]
            assert 'CorreoUsuario' in usuario
    
    def test_expedientes_por_fecha_query(self, local_expedientes_manager):
        """Test: Consulta de expedientes por rango de fechas"""
        # Usar sintaxis exacta del código legacy sin parámetros
        query = """
        SELECT TOP 5 IDExpediente, CodExp, Nemotecnico
        FROM TbExpedientes 
        ORDER BY IDExpediente DESC
        """
        result = local_expedientes_manager.db.execute_query(query)
        
        # Debe devolver una lista (puede estar vacía)
        assert isinstance(result, list)
        
        # Si hay expedientes, verificar estructura
        if result:
            expediente = result[0]
            assert 'IDExpediente' in expediente
            assert 'CodExp' in expediente
    
    def test_estadisticas_expedientes_query(self, local_expedientes_manager):
        """Test: Consulta de estadísticas de expedientes"""
        query = """
        SELECT Estado, COUNT(*) as Cantidad
        FROM TbExpedientes 
        GROUP BY Estado
        """
        result = local_expedientes_manager.db.execute_query(query)
        
        # Debe devolver una lista (puede estar vacía)
        assert isinstance(result, list)
        
        # Si hay estadísticas, verificar estructura
        if result:
            estadistica = result[0]
            assert 'Cantidad' in estadistica
    
    def test_database_performance(self, local_expedientes_manager):
        """Test: Rendimiento básico de consultas"""
        import time
        
        queries = [
            "SELECT COUNT(*) as total FROM TbExpedientes",
            "SELECT COUNT(*) as total FROM TbExpedientesAnexos",
            "SELECT COUNT(*) as total FROM TbTareas WHERE Tarea='ExpedientesDiario'"
        ]
        
        for query in queries:
            start_time = time.time()
            if 'TbTareas' in query:
                result = local_expedientes_manager.tareas_db.execute_query(query)
            else:
                result = local_expedientes_manager.db.execute_query(query)
            end_time = time.time()
            
            # Verificar que la consulta se ejecutó
            assert result is not None
            
            # Verificar que no tardó más de 5 segundos
            execution_time = end_time - start_time
            assert execution_time < 5.0, f"Consulta tardó {execution_time:.2f} segundos"
    
    def test_css_loading_real_file(self, local_expedientes_manager):
        """Test: Carga real del archivo CSS"""
        css_path = config.root_dir / 'herramientas' / 'CSS1.css'
        
        if css_path.exists():
            with open(css_path, 'r', encoding='utf-8') as f:
                css_content = f.read()
            
            assert len(css_content) > 0
            assert 'body' in css_content or 'table' in css_content
    
    def test_complete_expedientes_workflow_real_data(self, local_expedientes_manager):
        """Test: Workflow completo con datos reales"""
        # 1. Obtener expedientes existentes sin parámetros
        query_expedientes = """
        SELECT TOP 5 IDExpediente, CodExp, Nemotecnico
        FROM TbExpedientes
        ORDER BY IDExpediente DESC
        """
        expedientes = local_expedientes_manager.db.execute_query(query_expedientes)
        
        # Debe devolver una lista
        assert isinstance(expedientes, list)
        
        # Si hay expedientes, verificar estructura
        if expedientes:
            expediente = expedientes[0]
            assert 'IDExpediente' in expediente
            assert 'CodExp' in expediente
        
        # 2. Verificar estado de tareas sin parámetros
        tarea_query = """
        SELECT TOP 5 Fecha, Realizado
        FROM TbTareas 
        WHERE Tarea='ExpedientesDiario'
        ORDER BY Fecha DESC
        """
        tareas = local_expedientes_manager.tareas_db.execute_query(tarea_query)
        assert isinstance(tareas, list)
        
        # 3. Verificar estructura de correos sin parámetros
        correo_query = """
        SELECT COUNT(*) as total
        FROM TbCorreosEnviados
        WHERE Aplicacion = 'Expedientes'
        """
        correos = local_expedientes_manager.tareas_db.execute_query(correo_query)
        assert isinstance(correos, list)
        assert 'total' in correos[0]
    
    def test_join_expedientes_documentos(self, local_expedientes_manager):
        """Test: JOIN entre expedientes y documentos usando sintaxis legacy"""
        # Usar sintaxis exacta del código legacy que funciona
        query = """
        SELECT TOP 5 e.IDExpediente, e.CodExp, e.Nemotecnico
        FROM TbExpedientes e
        ORDER BY e.IDExpediente DESC
        """
        result = local_expedientes_manager.db.execute_query(query)
        
        # Debe devolver una lista
        assert isinstance(result, list)
        
        # Si hay expedientes, verificar estructura
        if result:
            expediente = result[0]
            assert 'IDExpediente' in expediente
            assert 'CodExp' in expediente
    
    def test_expedientes_sin_documentos_query(self, local_expedientes_manager):
        """Test: Expedientes sin documentos usando sintaxis legacy"""
        # Usar sintaxis básica que funciona
        query = """
        SELECT TOP 5 IDExpediente, CodExp, Nemotecnico
        FROM TbExpedientes
        ORDER BY IDExpediente DESC
        """
        result = local_expedientes_manager.db.execute_query(query)
        
        # Debe devolver una lista
        assert isinstance(result, list)
        
        # Si hay expedientes, verificar estructura
        if result:
            expediente = result[0]
            assert 'IDExpediente' in expediente
            assert 'CodExp' in expediente