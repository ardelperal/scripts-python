"""Tests de integración para el módulo de No Conformidades
"""
import os
import sys
import unittest
from unittest.mock import patch

from no_conformidades.no_conformidades_manager import NoConformidadesManager

# Agregar el directorio src al path para imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
src_dir = os.path.join(project_root, "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)


class TestNoConformidadesIntegration(unittest.TestCase):
    """Tests de integración para el módulo de No Conformidades"""

    @classmethod
    def setUpClass(cls):
        """Configuración inicial para todos los tests"""
        # Forzar uso de bases de datos locales
        os.environ["ENVIRONMENT"] = "local"
        from common.config import Config

        cls.config = Config()

        # Verificar que las bases de datos locales existen
        cls.db_nc_path = cls.config.db_no_conformidades_path
        cls.db_tareas_path = cls.config.db_tareas_path

        if not os.path.exists(cls.db_nc_path):
            cls.skipTest(
                f"Base de datos No Conformidades local no encontrada: {cls.db_nc_path}"
            )

        if not os.path.exists(cls.db_tareas_path):
            cls.skipTest(
                f"Base de datos Tareas local no encontrada: {cls.db_tareas_path}"
            )

    def setUp(self):
        """Configuración para cada test"""
        cfg = self.__class__.config
        from common.database import AccessDatabase

        self.db_nc = AccessDatabase(cfg.db_no_conformidades_path)
        self.db_tareas = AccessDatabase(cfg.db_tareas_path)
        self.manager = NoConformidadesManager()
        self.manager.db_nc = self.db_nc  # Inyectar mock de conexión
        self.manager.db_tareas = self.db_tareas  # Inyectar mock de conexión

    def tearDown(self):
        """Limpieza después de cada test"""
        if hasattr(self, "manager"):
            if hasattr(self.manager, "close_connections"):
                self.manager.close_connections()

    def test_database_connectivity(self):
        """Test: Conectividad básica con bases de datos de No Conformidades"""
        # Test conexión a base de datos NC
        result_nc = self.db_nc.execute_query("SELECT COUNT(*) as total FROM TbNoConformidades")
        self.assertIsNotNone(result_nc)
        self.assertGreater(len(result_nc), 0)
        self.assertIn("total", result_nc[0])

        # Test conexión a base de datos de tareas
        result_tareas = self.db_tareas.execute_query("SELECT COUNT(*) as total FROM TbTareas")
        self.assertIsNotNone(result_tareas)
        self.assertGreater(len(result_tareas), 0)
        self.assertIn("total", result_tareas[0])

    def test_get_ars_proximas_vencer_calidad_real(self):
        """Test de obtención real de ARs próximas a vencer para Calidad"""
        result = self.manager.get_ars_proximas_vencer_calidad()
        self.assertIsInstance(result, list)
        if result:
            self.assertIn("CodigoNoConformidad", result[0])

    def test_get_ncs_pendientes_eficacia_real(self):
        """Test de obtención real de NCs pendientes de control de eficacia"""
        result = self.manager.get_ncs_pendientes_eficacia()
        self.assertIsInstance(result, list)
        if result:
            self.assertIn("CodigoNoConformidad", result[0])

    def test_get_ncs_sin_acciones_real(self):
        """Test de obtención real de NCs sin acciones"""
        result = self.manager.get_ncs_sin_acciones()
        self.assertIsInstance(result, list)
        if result:
            self.assertIn("CodigoNoConformidad", result[0])

    def test_get_ars_para_replanificar_real(self):
        """Test de obtención real de ARs para replanificar"""
        result = self.manager.get_ars_para_replanificar()
        self.assertIsInstance(result, list)
        if result:
            self.assertIn("CodigoNoConformidad", result[0])

    def test_get_tecnicos_con_nc_activas_real(self):
        """Test de obtención real de técnicos con NCs activas"""
        result = self.manager.get_tecnicos_con_nc_activas()
        self.assertIsInstance(result, list)
        if result:
            self.assertIsInstance(result[0], str)

    def test_get_ars_tecnico_por_vencer_real(self):
        """Test de obtención real de ARs de técnico por vencer"""
        tecnicos = self.manager.get_tecnicos_con_nc_activas()
        if tecnicos:
            result = self.manager.get_ars_tecnico_por_vencer(tecnicos[0], 8, 15, "IDCorreo15")
            self.assertIsInstance(result, list)
            if result:
                self.assertIn("CodigoNoConformidad", result[0])

    def test_get_ars_tecnico_vencidas_real(self):
        """Test de obtención real de ARs de técnico vencidas"""
        tecnicos = self.manager.get_tecnicos_con_nc_activas()
        if tecnicos:
            result = self.manager.get_ars_tecnico_vencidas(tecnicos[0], "IDCorreo0")
            self.assertIsInstance(result, list)
            if result:
                self.assertIn("CodigoNoConformidad", result[0])

    def test_get_technical_report_data_for_user_real(self):
        """Test de obtención real de datos de reporte técnico para un usuario"""
        tecnicos = self.manager.get_tecnicos_con_nc_activas()
        if tecnicos:
            result = self.manager.get_technical_report_data_for_user(tecnicos[0])
            self.assertIsInstance(result, dict)
            self.assertIn("ars_15_dias", result)
            self.assertIn("ars_7_dias", result)
            self.assertIn("ars_vencidas", result)
            self.assertIsInstance(result["ars_15_dias"], list)

    def test_generar_correo_calidad_real(self):
        """Test de generación de correo de calidad con datos reales"""
        with patch.object(self.manager, "enviar_notificacion_calidad") as mock_enviar:
            self.manager._generar_correo_calidad()
            mock_enviar.assert_called_once()

    def test_generar_correos_tecnicos_real(self):
        """Test de generación de correos de técnicos con datos reales"""
        with patch.object(self.manager, "enviar_notificacion_tecnico_individual") as mock_enviar:
            self.manager._generar_correos_tecnicos()
            tecnicos = self.manager.get_tecnicos_con_nc_activas()
            if tecnicos:
                mock_enviar.assert_called()
            else:
                mock_enviar.assert_not_called()

    def test_ejecutar_logica_especifica_real(self):
        """Test de ejecución de lógica específica con datos reales"""
        # Mockear los generadores de correo para evitar envíos reales
        with patch(
            "no_conformidades.no_conformidades_manager.NoConformidadesManager._generar_correo_calidad"
        ) as mock_cal:
            with patch(
                "no_conformidades.no_conformidades_manager.NoConformidadesManager._generar_correos_tecnicos"
            ) as mock_tec:
                ok = self.manager.ejecutar_logica_especifica()
                self.assertTrue(ok)
                mock_cal.assert_called_once()
                mock_tec.assert_called_once()

    def test_ejecutar_logica_especifica_error_handling(self):
        """Test de manejo de errores en la lógica específica"""
        with patch(
            "no_conformidades.no_conformidades_manager.NoConformidadesManager._generar_correo_calidad"
        ) as mock_cal:
            with patch(
                "no_conformidades.no_conformidades_manager.NoConformidadesManager._generar_correos_tecnicos"
            ) as mock_tec:
                mock_cal.side_effect = Exception("Error de prueba")
                ok = self.manager.ejecutar_logica_especifica()
                self.assertFalse(ok)
                mock_cal.assert_called_once()
                mock_tec.assert_not_called() # No debería llamarse si el primero falla

    def test_ejecutar_logica_especifica_partial_error(self):
        """Test de manejo de errores parciales en la lógica específica"""
        with patch(
            "no_conformidades.no_conformidades_manager.NoConformidadesManager._generar_correo_calidad"
        ) as mock_cal:
            with patch(
                "no_conformidades.no_conformidades_manager.NoConformidadesManager._generar_correos_tecnicos"
            ) as mock_tec:
                mock_tec.side_effect = Exception("Error de prueba")
                ok = self.manager.ejecutar_logica_especifica()
                self.assertFalse(ok)
                mock_cal.assert_called_once()
                mock_tec.assert_called_once()


if __name__ == "__main__":
    # Configurar logging para tests
    import logging

    logging.basicConfig(level=logging.INFO)

    unittest.main()
