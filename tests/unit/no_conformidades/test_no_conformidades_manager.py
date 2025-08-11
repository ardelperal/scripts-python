"""
Tests unitarios para NoConformidadesManager
"""
import os
import sys
import unittest
from datetime import date, datetime
from unittest.mock import Mock, patch

# Agregar el directorio src al path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(current_dir))), "src"
)
sys.path.insert(0, src_dir)

from no_conformidades.no_conformidades_manager import NoConformidadesManager


class TestNoConformidadesManager(unittest.TestCase):
    """Tests para NoConformidadesManager"""

    def setUp(self):
        """Configuración inicial para cada test"""
        # Mock de las dependencias externas
        with patch(
            "no_conformidades.no_conformidades_manager.config"
        ) as mock_config, patch(
            "no_conformidades.no_conformidades_manager.AccessDatabase"
        ) as mock_db:
            # Configurar mocks
            mock_config.get_nc_css_content.return_value = "/* test css */"
            mock_config.get_db_no_conformidades_connection_string.return_value = (
                "test_connection"
            )

            self.manager = NoConformidadesManager()
            self.mock_db = mock_db

    def test_init(self):
        """Test de inicialización del manager"""
        self.assertEqual(self.manager.name, "NoConformidades")
        self.assertEqual(self.manager.script_filename, "run_no_conformidades.py")
        self.assertEqual(self.manager.task_names, ["NCTecnico", "NCCalidad"])
        self.assertEqual(self.manager.frequency_days, 1)
        self.assertIsNotNone(self.manager.css_content)

    def test_load_css_content_success(self):
        """Test de carga exitosa del contenido CSS"""
        with patch("no_conformidades.no_conformidades_manager.config") as mock_config:
            mock_config.get_nc_css_content.return_value = "body { color: red; }"
            manager = NoConformidadesManager()
            self.assertEqual(manager.css_content, "body { color: red; }")

    def test_load_css_content_error(self):
        """Test de manejo de error al cargar CSS"""
        with patch("no_conformidades.no_conformidades_manager.config") as mock_config:
            mock_config.get_nc_css_content.side_effect = Exception("CSS error")
            manager = NoConformidadesManager()
            self.assertEqual(manager.css_content, "/* CSS no disponible */")

    def test_get_nc_connection(self):
        """Test de obtención de conexión a base de datos NC"""
        with patch(
            "no_conformidades.no_conformidades_manager.config"
        ) as mock_config, patch(
            "no_conformidades.no_conformidades_manager.AccessDatabase"
        ) as mock_db:
            mock_config.get_db_no_conformidades_connection_string.return_value = (
                "test_connection"
            )
            mock_db_instance = Mock()
            mock_db.return_value = mock_db_instance

            manager = NoConformidadesManager()
            connection = manager._get_nc_connection()

            self.assertEqual(connection, mock_db_instance)
            mock_db.assert_called_with("test_connection")

    def test_ejecutar_consulta_success(self):
        """Test de ejecución exitosa de consulta"""
        mock_db_instance = Mock()
        mock_db_instance.execute_query.return_value = [{"id": 1, "name": "test"}]

        with patch.object(
            self.manager, "_get_nc_connection", return_value=mock_db_instance
        ):
            result = self.manager.ejecutar_consulta("SELECT * FROM test")

            self.assertEqual(result, [{"id": 1, "name": "test"}])
            mock_db_instance.execute_query.assert_called_once_with(
                "SELECT * FROM test", None
            )

    def test_ejecutar_consulta_error(self):
        """Test de manejo de error en consulta"""
        mock_db_instance = Mock()
        mock_db_instance.execute_query.side_effect = Exception("DB error")

        with patch.object(
            self.manager, "_get_nc_connection", return_value=mock_db_instance
        ):
            result = self.manager.ejecutar_consulta("SELECT * FROM test")

            self.assertEqual(result, [])

    def test_ejecutar_insercion_success(self):
        """Test de ejecución exitosa de inserción"""
        mock_db_instance = Mock()
        mock_db_instance.execute_non_query.return_value = 1

        with patch.object(
            self.manager, "_get_nc_connection", return_value=mock_db_instance
        ):
            result = self.manager.ejecutar_insercion("INSERT INTO test VALUES (1)")

            self.assertTrue(result)
            mock_db_instance.execute_non_query.assert_called_once_with(
                "INSERT INTO test VALUES (1)", None
            )

    def test_ejecutar_insercion_error(self):
        """Test de manejo de error en inserción"""
        mock_db_instance = Mock()
        mock_db_instance.execute_non_query.side_effect = Exception("DB error")

        with patch.object(
            self.manager, "_get_nc_connection", return_value=mock_db_instance
        ):
            result = self.manager.ejecutar_insercion("INSERT INTO test VALUES (1)")

            self.assertFalse(result)

    def test_format_date_for_access_string_date(self):
        """Test de formateo de fecha string para Access"""
        result = self.manager._format_date_for_access("2024-01-15")
        self.assertEqual(result, "#01/15/2024#")

    def test_format_date_for_access_datetime(self):
        """Test de formateo de datetime para Access"""
        test_date = datetime(2024, 1, 15)
        result = self.manager._format_date_for_access(test_date)
        self.assertEqual(result, "#01/15/2024#")

    def test_format_date_for_access_date(self):
        """Test de formateo de date para Access"""
        test_date = date(2024, 1, 15)
        result = self.manager._format_date_for_access(test_date)
        self.assertEqual(result, "#01/15/2024#")

    def test_format_date_for_access_invalid(self):
        """Test de formateo de fecha inválida para Access"""
        result = self.manager._format_date_for_access("invalid_date")
        self.assertEqual(result, "#01/01/1900#")

    def test_get_ars_proximas_vencer_calidad_success(self):
        """Test de obtención exitosa de ARs próximas a vencer"""
        mock_data = [
            {
                "DiasParaCierre": 5,
                "CodigoNoConformidad": "NC001",
                "Nemotecnico": "TEST",
                "DESCRIPCION": "Test description",
                "RESPONSABLECALIDAD": "user1",
                "FECHAAPERTURA": date(2024, 1, 1),
                "FPREVCIERRE": date(2024, 1, 15),
            }
        ]

        mock_db_instance = Mock()
        mock_db_instance.execute_query.return_value = mock_data

        with patch.object(
            self.manager, "_get_nc_connection", return_value=mock_db_instance
        ):
            result = self.manager.get_ars_proximas_vencer_calidad()

            self.assertEqual(result, mock_data)
            mock_db_instance.execute_query.assert_called_once()

    def test_get_ars_proximas_vencer_calidad_error(self):
        """Test de manejo de error al obtener ARs próximas a vencer"""
        mock_db_instance = Mock()
        mock_db_instance.execute_query.side_effect = Exception("DB error")

        with patch.object(
            self.manager, "_get_nc_connection", return_value=mock_db_instance
        ):
            result = self.manager.get_ars_proximas_vencer_calidad()

            self.assertEqual(result, [])

    # === Nuevas pruebas adaptadas al generador HTML unificado ===
    def test_generar_reporte_calidad_moderno_vacio(self):
        """El reporte moderno de calidad con datos vacíos debe contener header y footer."""
        html = self.manager.html_generator.generar_reporte_calidad_moderno(
            [], [], [], []
        )
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("Informe de No Conformidades - Calidad", html)
        self.assertIn("</html>", html)

    def test_generar_reporte_tecnico_moderno_con_datos(self):
        """Reporte técnico moderno con datos mínimos."""
        sample = [
            {
                "CodigoNoConformidad": "NC001",
                "Nemotecnico": "NEMO",
                "AccionCorrectiva": "Acción X",
                "AccionRealizada": "Tarea Y",
                "FechaInicio": date(2024, 1, 1),
                "FechaFinPrevista": date(2024, 1, 10),
                "Nombre": "Tecnico 1",
                "DiasParaCaducar": 5,
                "CorreoCalidad": "calidad@test",
            }
        ]
        html = self.manager.html_generator.generar_reporte_tecnico_moderno(
            sample, [], []
        )
        self.assertIn("Acciones Correctivas con fecha fin prevista a 8-15 días", html)
        self.assertIn("NC001", html)
        self.assertIn("Tecnico 1", html)

    def test_get_ars_tecnico_por_vencer_queries(self):
        """Verifica que la consulta generada para rangos correctos contiene el BETWEEN esperado."""
        captured = {}

        class FakeDB:
            def execute_query(self_inner, query, params):
                captured["query"] = query
                return [{"CodigoNoConformidad": "NCX"}]

        with patch.object(self.manager, "_get_nc_connection", return_value=FakeDB()):
            res = self.manager.get_ars_tecnico_por_vencer(
                "TECNICO1", 8, 15, "IDCorreo15"
            )
            self.assertEqual(res[0]["CodigoNoConformidad"], "NCX")
            self.assertIn("BETWEEN 8 AND 15", captured["query"])

    def test_get_ars_tecnico_por_vencer_rango_1_7_query(self):
        """Verifica condición especial 1-7 días (>0 AND <=7)."""
        captured = {}

        class FakeDB:
            def execute_query(self_inner, query, params):
                captured["query"] = query
                return []

        with patch.object(self.manager, "_get_nc_connection", return_value=FakeDB()):
            self.manager.get_ars_tecnico_por_vencer("TECNICO2", 1, 7, "IDCorreo7")
            self.assertIn("> 0 AND DateDiff", captured["query"])
            self.assertIn("<= 7", captured["query"])

    def test_get_ars_tecnico_vencidas_query(self):
        """Verifica condición de vencidas (<= 0)."""
        captured = {}

        class FakeDB:
            def execute_query(self_inner, query, params):
                captured["query"] = query
                return []

        with patch.object(self.manager, "_get_nc_connection", return_value=FakeDB()):
            self.manager.get_ars_tecnico_vencidas("TECNICO3")
            self.assertIn("<= 0", captured["query"])

    def test_registrar_aviso_ar_insert(self):
        """Inserta un aviso nuevo cuando no existe registro previo."""

        class FakeDB:
            def __init__(self):
                self.query_calls = []
                self.non_query_calls = []
                self.stage = 0

            def execute_query(self, query, params=None):
                self.query_calls.append(query)
                # Primera llamada: check -> vacío; Segunda: max id
                if "FROM TbNCARAvisos WHERE" in query:
                    return []
                if "Max(TbNCARAvisos.ID)" in query:
                    return [{"Maximo": 7}]
                return []

            def execute_non_query(self, query, params=None):
                self.non_query_calls.append((query, params))
                return 1

        fake = FakeDB()
        with patch.object(self.manager, "_get_nc_connection", return_value=fake):
            self.manager.registrar_aviso_ar(123, 55, "IDCorreo7")
            self.assertEqual(len(fake.non_query_calls), 1)
            q, params = fake.non_query_calls[0]
            self.assertIn("INSERT INTO TbNCARAvisos", q)
            self.assertEqual(params[1], 123)

    def test_registrar_aviso_ar_update(self):
        """Actualiza aviso existente si ya hay registro."""

        class FakeDB:
            def __init__(self):
                self.query_calls = []
                self.non_query_calls = []

            def execute_query(self, query, params=None):
                self.query_calls.append(query)
                if "FROM TbNCARAvisos WHERE" in query:
                    return [{"IDAR": 123}]
                return []

            def execute_non_query(self, query, params=None):
                self.non_query_calls.append((query, params))
                return 1

        fake = FakeDB()
        with patch.object(self.manager, "_get_nc_connection", return_value=fake):
            self.manager.registrar_aviso_ar(123, 88, "IDCorreo15")
            self.assertEqual(len(fake.non_query_calls), 1)
            q, params = fake.non_query_calls[0]
            self.assertIn("UPDATE TbNCARAvisos SET", q)
            self.assertEqual(params[1], 123)

    def test_close_connections(self):
        """Test de cierre de conexiones"""
        mock_db_nc = Mock()
        self.manager.db_nc = mock_db_nc

        with patch(
            "no_conformidades.no_conformidades_manager.TareaDiaria.close_connections"
        ) as mock_super:
            self.manager.close_connections()

            mock_super.assert_called_once()
            mock_db_nc.disconnect.assert_called_once()
            self.assertIsNone(self.manager.db_nc)

    def test_close_connections_error(self):
        """Test de manejo de error al cerrar conexiones"""
        mock_db_nc = Mock()
        mock_db_nc.disconnect.side_effect = Exception("Close error")
        self.manager.db_nc = mock_db_nc

        with patch(
            "no_conformidades.no_conformidades_manager.TareaDiaria.close_connections"
        ):
            # No debe lanzar excepción
            self.manager.close_connections()
            self.assertIsNone(self.manager.db_nc)


if __name__ == "__main__":
    unittest.main()
