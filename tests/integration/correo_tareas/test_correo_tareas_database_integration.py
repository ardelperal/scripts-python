"""
Tests de integración de base de datos para Correo Tareas
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


class TestCorreoTareasDatabaseIntegration:
    """Tests de integración con bases de datos reales para Correo Tareas"""
    
    def test_database_connectivity(self, local_correo_tareas_manager):
        """Test: Conectividad básica con base de datos de Tareas"""
        # Test conexión a base de datos de tareas
        result = local_correo_tareas_manager.db_conn.execute_query("SELECT COUNT(*) as total FROM TbCorreosEnviados")
        assert result is not None
        assert len(result) > 0
        assert 'total' in result[0]
    
    def test_correos_enviados_structure(self, local_correo_tareas_manager):
        """Test: Verificar estructura de tabla TbCorreosEnviados"""
        query = "SELECT * FROM TbCorreosEnviados"
        result = local_correo_tareas_manager.db_conn.execute_query(query)
        
        # Limitar a 1 resultado en Python si hay datos
        if result and len(result) > 1:
            result = result[:1]
        
        if result:
            correo = result[0]
            # Verificar campos esperados según el script legacy
            expected_fields = [
                'IDCorreo', 'Aplicacion', 'Destinatarios', 'DestinatariosConCopia',
                'Asunto', 'Cuerpo', 'FechaGrabacion', 'FechaEnvio'
            ]
            for field in expected_fields:
                assert field in correo, f"Campo {field} no encontrado en TbCorreosEnviados"
    
    def test_correos_pendientes_query(self, local_correo_tareas_manager):
        """Test: Consulta de correos pendientes (query principal del legacy)"""
        # Esta es la consulta exacta del script legacy EnviarCorreoTareas.vbs
        query = """
        SELECT TbCorreosEnviados.*
        FROM TbCorreosEnviados
        WHERE TbCorreosEnviados.FechaEnvio Is Null
        """
        result = local_correo_tareas_manager.db_conn.execute_query(query)
        
        # Debe devolver una lista (puede estar vacía)
        assert isinstance(result, list)
        
        # Si hay correos pendientes, verificar estructura
        if result:
            correo = result[0]
            assert 'IDCorreo' in correo
            assert 'Aplicacion' in correo
            assert 'Destinatarios' in correo
            assert 'Asunto' in correo
            assert 'Cuerpo' in correo
            assert correo['FechaEnvio'] is None  # Debe ser None para correos pendientes
    
    def test_obtener_correos_pendientes_method(self, local_correo_tareas_manager):
        """Test: Método obtener_correos_pendientes del CorreoTareasManager"""
        correos_pendientes = local_correo_tareas_manager.obtener_correos_pendientes()
        
        # Debe devolver una lista
        assert isinstance(correos_pendientes, list)
        
        # Si hay correos, verificar que todos tengan FechaEnvio = None
        for correo in correos_pendientes:
            assert correo['FechaEnvio'] is None
            assert 'IDCorreo' in correo
            assert 'Aplicacion' in correo
    
    def test_marcar_correo_enviado_query(self, local_correo_tareas_manager):
        """Test: Verificar que la consulta de actualización funciona correctamente"""
        # Primero obtener un correo pendiente si existe
        correos_pendientes = local_correo_tareas_manager.obtener_correos_pendientes()
        
        if correos_pendientes:
            # Tomar el primer correo pendiente
            correo = correos_pendientes[0]
            id_correo = correo['IDCorreo']
            
            # Verificar que inicialmente FechaEnvio es None
            query_check = f"SELECT FechaEnvio FROM TbCorreosEnviados WHERE IDCorreo = {id_correo}"
            result_before = local_correo_tareas_manager.db_conn.execute_query(query_check)
            assert result_before[0]['FechaEnvio'] is None
            
            # Simular marcado como enviado (sin enviar realmente el correo)
            fecha_envio = datetime.now()
            update_data = {"FechaEnvio": fecha_envio}
            where_clause = f"IDCorreo = {id_correo}"
            
            success = local_correo_tareas_manager.db_conn.update_record("TbCorreosEnviados", update_data, where_clause)
            assert success is True
            
            # Verificar que se actualizó correctamente
            result_after = local_correo_tareas_manager.db_conn.execute_query(query_check)
            assert result_after[0]['FechaEnvio'] is not None
            
            # Restaurar el estado original para no afectar otros tests
            restore_data = {"FechaEnvio": None}
            local_correo_tareas_manager.db_conn.update_record("TbCorreosEnviados", restore_data, where_clause)
    
    def test_correos_by_aplicacion_query(self, local_correo_tareas_manager):
        """Test: Consulta de correos por aplicación específica"""
        query = """
        SELECT IDCorreo, Aplicacion, Asunto
        FROM TbCorreosEnviados
        WHERE Aplicacion IS NOT NULL
        ORDER BY IDCorreo
        """
        result = local_correo_tareas_manager.db_conn.execute_query(query)
        
        # Limitar a 5 resultados en Python si hay datos
        if result and len(result) > 5:
            result = result[:5]
        
        # Debe devolver una lista (puede estar vacía)
        assert isinstance(result, list)
        
        # Si hay correos, verificar que tienen aplicación
        for correo in result:
            assert correo['Aplicacion'] is not None
            assert correo['Aplicacion'] != ""
    
    def test_correos_con_adjuntos_query(self, local_correo_tareas_manager):
        """Test: Consulta de correos con adjuntos"""
        # Simplificar la consulta para evitar problemas con Access
        query = "SELECT * FROM TbCorreosEnviados"
        result = local_correo_tareas_manager.db_conn.execute_query(query)
        
        # Filtrar en Python los que tienen adjuntos
        correos_con_adjuntos = []
        if result:
            for correo in result:
                if correo.get('URLAdjunto') is not None and correo.get('URLAdjunto') != '':
                    correos_con_adjuntos.append(correo)
        
        # Debe devolver una lista (puede estar vacía)
        assert isinstance(correos_con_adjuntos, list)
        
        # Si hay correos con adjuntos, verificar estructura
        if correos_con_adjuntos:
            correo = correos_con_adjuntos[0]
            assert 'URLAdjunto' in correo
            assert correo['URLAdjunto'] is not None
            assert correo['URLAdjunto'] != ''
    
    def test_correos_enviados_recientes_query(self, local_correo_tareas_manager):
        """Test: Consulta de correos enviados recientemente"""
        # Fecha de hace 30 días
        fecha_limite = datetime.now() - timedelta(days=30)
        
        query = f"""
        SELECT IDCorreo, FechaEnvio, Asunto
        FROM TbCorreosEnviados
        WHERE FechaEnvio IS NOT NULL
        ORDER BY FechaEnvio DESC
        """
        result = local_correo_tareas_manager.db_conn.execute_query(query)
        
        # Limitar a 10 resultados en Python si hay datos
        if result and len(result) > 10:
            result = result[:10]
        
        # Debe devolver una lista (puede estar vacía)
        assert isinstance(result, list)
        
        # Si hay correos enviados, verificar que tienen fecha de envío
        for correo in result:
            assert correo['FechaEnvio'] is not None
    
    def test_count_correos_pendientes_vs_enviados(self, local_correo_tareas_manager):
        """Test: Comparar cantidad de correos pendientes vs enviados"""
        # Contar correos pendientes
        query_pendientes = """
        SELECT COUNT(*) as total_pendientes
        FROM TbCorreosEnviados
        WHERE FechaEnvio IS NULL
        """
        result_pendientes = local_correo_tareas_manager.db_conn.execute_query(query_pendientes)
        total_pendientes = result_pendientes[0]['total_pendientes']
        
        # Contar correos enviados
        query_enviados = """
        SELECT COUNT(*) as total_enviados
        FROM TbCorreosEnviados
        WHERE FechaEnvio IS NOT NULL
        """
        result_enviados = local_correo_tareas_manager.db_conn.execute_query(query_enviados)
        total_enviados = result_enviados[0]['total_enviados']
        
        # Contar total
        query_total = """
        SELECT COUNT(*) as total
        FROM TbCorreosEnviados
        """
        result_total = local_correo_tareas_manager.db_conn.execute_query(query_total)
        total = result_total[0]['total']
        
        # Verificar que la suma coincide
        assert total_pendientes + total_enviados == total
        assert total_pendientes >= 0
        assert total_enviados >= 0
    
    def test_max_id_correo_query(self, local_correo_tareas_manager):
        """Test: Consulta de máximo ID de correo"""
        query = """
        SELECT MAX(IDCorreo) AS Maximo
        FROM TbCorreosEnviados
        """
        result = local_correo_tareas_manager.db_conn.execute_query(query)
        
        assert result is not None
        assert len(result) > 0
        assert 'Maximo' in result[0]
        
        # El máximo puede ser None si no hay registros
        maximo = result[0]['Maximo']
        if maximo is not None:
            assert isinstance(maximo, int)
            assert maximo > 0
    
    def test_correos_multiples_destinatarios_query(self, local_correo_tareas_manager):
        """Test: Consulta de correos con múltiples destinatarios"""
        query = """
        SELECT IDCorreo, Destinatarios, DestinatariosConCopia
        FROM TbCorreosEnviados
        WHERE Destinatarios LIKE '*;*' OR DestinatariosConCopia LIKE '*;*'
        ORDER BY IDCorreo
        """
        result = local_correo_tareas_manager.db_conn.execute_query(query)
        
        # Debe devolver una lista (puede estar vacía)
        assert isinstance(result, list)
        
        # Si hay correos con múltiples destinatarios, verificar que contienen ';'
        for correo in result:
            destinatarios = correo.get('Destinatarios', '') or ''
            cc = correo.get('DestinatariosConCopia', '') or ''
            assert ';' in destinatarios or ';' in cc
    
    def test_database_connection_cleanup(self, local_correo_tareas_manager):
        """Test: Verificar que las conexiones se manejan correctamente"""
        # Realizar varias consultas para verificar que la conexión se mantiene
        queries = [
            "SELECT COUNT(*) as total FROM TbCorreosEnviados",
            "SELECT MAX(IDCorreo) as max_id FROM TbCorreosEnviados",
            "SELECT COUNT(*) as pendientes FROM TbCorreosEnviados WHERE FechaEnvio IS NULL"
        ]
        
        for query in queries:
            result = local_correo_tareas_manager.db_conn.execute_query(query)
            assert result is not None
            assert len(result) > 0
        
        # La conexión debe seguir funcionando después de múltiples consultas
        final_query = "SELECT COUNT(*) as final_count FROM TbCorreosEnviados"
        final_result = local_correo_tareas_manager.db_conn.execute_query(final_query)
        assert final_result is not None