"""Pruebas unitarias para el módulo de gestión de riesgos."""

import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

# Agregar el directorio src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from common.config import Config
from riesgos.riesgos_manager import RiesgosManager
from riesgos.riesgos_task import RiesgosTask


class TestRiesgosManager(unittest.TestCase):
    """Pruebas para la clase RiesgosManager."""

    def setUp(self):
        """Configuración inicial para cada prueba.

        NOTA: Esta sección se reescribió para asegurar que ninguna línea
        de inicialización quede fuera del método, evitando el NameError
        'self is not defined'.
        """
        self.config = Mock(spec=Config)
        self.config.database_path = "test.accdb"
        self.logger = Mock()
        self.manager = RiesgosManager(self.config, self.logger)
        self.manager.db = Mock()
        self.task = RiesgosTask(manager=self.manager)

    def test_init(self):
        """Prueba la inicialización del manager."""
        self.assertEqual(self.manager.config, self.config)
        self.assertIsNotNone(self.manager.logger)

    # Conexión/desconexión gestionadas ahora por RiesgosTask / inicialización explícita.
    def test_dummy_connection_interfaces_removed(self):
        self.assertFalse(hasattr(self.manager, "connect"))
        self.assertFalse(hasattr(self.manager, "disconnect"))

    # Métodos get_last_execution removidos: se validan ausencias
    def test_removed_legacy_execution_methods(self):
        for attr in [
            "get_last_execution",
            "record_task_execution",
            "should_execute_technical_task",
            "should_execute_quality_task",
            "should_execute_monthly_quality_task",
            "execute_daily_task",
        ]:
            self.assertFalse(hasattr(self.manager, attr))

    # Sustituir tests de decisión por verificación de interfaz de RiesgosTask (placeholder simplificado)
    def test_riesgos_task_run_tasks_empty(self):
        # Sin métodos de decisión en manager, task consultará y no ejecutará nada (db vacía)
        self.manager.execute_technical_task = Mock(return_value=True)
        self.manager.execute_quality_task = Mock(return_value=True)
        self.manager.execute_monthly_quality_task = Mock(return_value=True)
        # Forzamos banderas para simular ejecución
        results = self.task.run_tasks(force_technical=True, force_quality=True, force_monthly=True)
        self.assertTrue(all(results.values()))

    # Eliminados tests de should_execute_quality_task -> lógica ahora en Task (o futura frecuencia)

    # Eliminados tests de should_execute_monthly_quality_task -> responsabilidad movida

    def test_get_distinct_users(self):
        """Prueba obtener usuarios distintos."""
        # Mock de las consultas
        self.manager.db.execute_query.side_effect = [
            [
                {
                    "UsuarioRed": "user1",
                    "Nombre": "Usuario 1",
                    "CorreoUsuario": "user1@test.com",
                }
            ],
            [
                {
                    "UsuarioRed": "user2",
                    "Nombre": "Usuario 2",
                    "CorreoUsuario": "user2@test.com",
                }
            ],
            [],  # Consulta sin resultados
            [
                {
                    "UsuarioRed": "user1",
                    "Nombre": "Usuario 1",
                    "CorreoUsuario": "user1@test.com",
                }
            ],  # Usuario duplicado
            [],
            [],
            [],
            [],
        ]

        result = self.manager.get_distinct_users()

        # Verificar que se obtuvieron usuarios únicos
        self.assertEqual(len(result), 2)
        self.assertIn("user1", result)
        self.assertIn("user2", result)
        self.assertEqual(result["user1"], ("Usuario 1", "user1@test.com"))
        self.assertEqual(result["user2"], ("Usuario 2", "user2@test.com"))

    def test_get_css_styles(self):
        """Prueba obtener estilos CSS."""
        result = self.manager.get_css_styles()

        self.assertIn("<style", result)
        self.assertIn("body", result)
        self.assertIn("table", result)

    # Métodos record_task_execution quitados: verificado arriba en removed_legacy_execution_methods

    # Sustituido execute_daily_task por RiesgosTask.run_tasks (cubierto arriba)

    @patch("email_services.email_manager.EmailManager.register_email")
    def test_execute_technical_task_success(self, mock_register_email):
        """Prueba ejecución exitosa de tarea técnica."""
        # Configurar usuarios mock
        users = {
            "user1": ("Usuario 1", "user1@test.com"),
            "user2": ("Usuario 2", "user2@test.com"),
        }
        self.manager.get_distinct_users = Mock(return_value=users)
        self.manager._generate_technical_report_html = Mock(
            return_value="<html>Report</html>"
        )

        result = self.manager.execute_technical_task()

        self.assertTrue(result)
        self.assertEqual(mock_register_email.call_count, 2)

    def test_execute_technical_task_error(self):
        """Prueba error en ejecución de tarea técnica."""
        self.manager.get_distinct_users = Mock(side_effect=Exception("Error"))

        result = self.manager.execute_technical_task()

        self.assertFalse(result)

    @patch("riesgos.riesgos_manager.get_admin_emails_string")
    @patch("email_services.email_manager.EmailManager.register_email")
    def test_execute_quality_task_success(self, mock_register_email, mock_get_emails):
        """Prueba ejecución exitosa de tarea de calidad."""
        mock_get_emails.return_value = "admin@test.com"
        self.manager._generate_quality_report_html = Mock(
            return_value="<html>Quality Report</html>"
        )
        self.manager._generate_quality_metrics_html = Mock(
            return_value="<div>Quality Metrics</div>"
        )

        result = self.manager.execute_quality_task()

        self.assertTrue(result)
        mock_register_email.assert_called_once()

    def test_execute_quality_task_error(self):
        """Prueba error en ejecución de tarea de calidad."""
        self.manager._generate_quality_report_html = Mock(
            side_effect=Exception("Error")
        )

        result = self.manager.execute_quality_task()

        self.assertFalse(result)

    @patch("riesgos.riesgos_manager.get_admin_emails_string")
    @patch("email_services.email_manager.EmailManager.register_email")
    def test_execute_monthly_quality_task_success(
        self, mock_register_email, mock_get_emails
    ):
        """Prueba ejecución exitosa de tarea de calidad mensual."""
        mock_get_emails.return_value = "admin@test.com"
        self.manager._generate_monthly_quality_report_html = Mock(
            return_value="<html>Monthly Report</html>"
        )
        self.manager._generate_monthly_metrics_html = Mock(
            return_value="<div>Monthly Metrics</div>"
        )

        result = self.manager.execute_monthly_quality_task()

        self.assertTrue(result)
        mock_register_email.assert_called_once()

    def test_execute_monthly_quality_task_error(self):
        """Prueba error en ejecución de tarea de calidad mensual."""
        self.manager._generate_monthly_quality_report_html = Mock(
            side_effect=Exception("Error")
        )

        result = self.manager.execute_monthly_quality_task()

        self.assertFalse(result)

    def test_generate_technical_report_html(self):
        """Prueba generación de reporte HTML técnico."""
        # Mock de métodos de datos
        self.manager._get_editions_need_publication_data = Mock(return_value=[])
        self.manager._get_editions_with_rejected_proposals_data = Mock(return_value=[])
        self.manager._get_accepted_risks_unmotivated_data = Mock(return_value=[])
        self.manager._get_accepted_risks_rejected_data = Mock(return_value=[])
        self.manager._get_retired_risks_unmotivated_data = Mock(return_value=[])
        self.manager._get_retired_risks_rejected_data = Mock(return_value=[])
        self.manager._get_mitigation_actions_reschedule_data = Mock(return_value=[])
        self.manager._get_contingency_actions_reschedule_data = Mock(return_value=[])

        result = self.manager._generate_technical_report_html("user1", "Usuario 1")

        self.assertIn("<html>", result)
        self.assertIn("Usuario 1", result)
        self.assertIn("</html>", result)

    def test_generate_quality_report_html(self):
        """Prueba generación de reporte HTML de calidad."""
        self.manager._generate_quality_metrics_html = Mock(
            return_value="<div>Metrics</div>"
        )

        result = self.manager._generate_quality_report_html()

        self.assertIn("<html>", result)
        self.assertIn("Informe Semanal de Calidad", result)
        self.assertIn("</html>", result)

    def test_generate_monthly_quality_report_html(self):
        """Prueba generación de reporte HTML de calidad mensual."""
        self.manager._generate_monthly_metrics_html = Mock(
            return_value="<div>Monthly Metrics</div>"
        )

        result = self.manager._generate_monthly_quality_report_html()

        self.assertIn("<html>", result)
        self.assertIn("Informe Mensual de Calidad", result)
        self.assertIn("</html>", result)

    def test_generate_section_html_with_data(self):
        """Prueba generación de sección HTML con datos."""
        data = [
            {"Columna1": "Valor1", "Columna2": "Valor2"},
            {"Columna1": "Valor3", "Columna2": "Valor4"},
        ]

        result = self.manager._generate_section_html("Test Section", data)

        self.assertIn("Test Section", result)
        self.assertIn("Total: 2 elementos", result)
        self.assertIn("<table>", result)
        self.assertIn("Valor1", result)

    def test_generate_section_html_no_data(self):
        """Prueba generación de sección HTML sin datos."""
        result = self.manager._generate_section_html("Empty Section", [])

        self.assertIn("Empty Section", result)
        self.assertIn("Total: 0 elementos", result)
        self.assertIn("No hay elementos para mostrar", result)

    def test_data_methods_error_handling(self):
        """Prueba manejo de errores en métodos de datos."""
        self.manager.db.execute_query.side_effect = Exception("DB error")

        # Probar todos los métodos de datos
        methods = [
            "_get_editions_need_publication_data",
            "_get_editions_with_rejected_proposals_data",
            "_get_accepted_risks_unmotivated_data",
            "_get_accepted_risks_rejected_data",
            "_get_retired_risks_unmotivated_data",
            "_get_retired_risks_rejected_data",
            "_get_mitigation_actions_reschedule_data",
            "_get_contingency_actions_reschedule_data",
        ]

        for method_name in methods:
            method = getattr(self.manager, method_name)
            result = method("user1")
            self.assertEqual(result, [])

    def test_get_risks_to_reclassify_success(self):
        """Prueba obtener riesgos que necesitan retipificación exitosamente."""
        mock_data = [
            {
                "IDRiesgo": 1,
                "Nemotecnico": "TEST-001",
                "DescripcionRiesgo": "Riesgo de prueba",
                "TipoRiesgo": "Técnico",
                "UsuarioCalidad": "Usuario Calidad",
                "FechaRiesgoParaRetipificar": "2024-01-01",
            }
        ]
        self.manager.db.execute_query.return_value = mock_data

        result = self.manager._get_risks_to_reclassify()

        self.assertEqual(result, mock_data)
        self.manager.db.execute_query.assert_called_once()

    def test_get_risks_to_reclassify_error(self):
        """Prueba error al obtener riesgos que necesitan retipificación."""
        self.manager.db.execute_query.side_effect = Exception("DB error")

        result = self.manager._get_risks_to_reclassify()

        self.assertEqual(result, [])

    def test_get_editions_ready_for_publication_success(self):
        """Prueba obtener ediciones preparadas para publicar exitosamente."""
        mock_data = [
            {
                "Nemotecnico": "TEST-001",
                "NombreProyecto": "Proyecto Test",
                "Juridica": "Sí",
                "Edicion": "1.0",
                "FechaEdicion": "2024-01-01",
                "NombreUsuarioCalidad": "Usuario Calidad",
            }
        ]
        self.manager.db.execute_query.return_value = mock_data

        result = self.manager._get_editions_ready_for_publication()

        self.assertEqual(result, mock_data)
        self.manager.db.execute_query.assert_called_once()

    def test_get_editions_ready_for_publication_error(self):
        """Prueba error al obtener ediciones preparadas para publicar."""
        self.manager.db.execute_query.side_effect = Exception("DB error")

        result = self.manager._get_editions_ready_for_publication()

        self.assertEqual(result, [])

    def test_get_accepted_risks_pending_review_success(self):
        """Prueba obtener riesgos aceptados pendientes de visado exitosamente."""
        mock_data = [
            {
                "IDRiesgo": 1,
                "Nemotecnico": "TEST-001",
                "DescripcionRiesgo": "Riesgo aceptado",
                "JustificacionAceptacionRiesgo": "Justificación",
                "FechaJustificacionAceptacionRiesgo": "2024-01-01",
                "UsuarioCalidad": "Usuario Calidad",
            }
        ]
        self.manager.db.execute_query.return_value = mock_data

        result = self.manager._get_accepted_risks_pending_review()

        self.assertEqual(result, mock_data)
        self.manager.db.execute_query.assert_called_once()

    def test_get_accepted_risks_pending_review_error(self):
        """Prueba error al obtener riesgos aceptados pendientes de visado."""
        self.manager.db.execute_query.side_effect = Exception("DB error")

        result = self.manager._get_accepted_risks_pending_review()

        self.assertEqual(result, [])

    def test_get_retired_risks_pending_review_success(self):
        """Prueba obtener riesgos retirados pendientes de visado exitosamente."""
        mock_data = [
            {
                "IDRiesgo": 1,
                "Nemotecnico": "TEST-001",
                "DescripcionRiesgo": "Riesgo retirado",
                "CausaRaiz": "Causa raíz",
                "FechaJustificacionRetiroRiesgo": "2024-01-01",
                "UsuarioCalidad": "Usuario Calidad",
            }
        ]
        self.manager.db.execute_query.return_value = mock_data

        result = self.manager._get_retired_risks_pending_review()

        self.assertEqual(result, mock_data)
        self.manager.db.execute_query.assert_called_once()

    def test_get_retired_risks_pending_review_error(self):
        """Prueba error al obtener riesgos retirados pendientes de visado."""
        self.manager.db.execute_query.side_effect = Exception("DB error")

        result = self.manager._get_retired_risks_pending_review()

        self.assertEqual(result, [])

    def test_generate_editions_table_html_with_data(self):
        """Prueba generación de tabla HTML para ediciones con datos."""
        data = [
            {
                "Proyecto": "TEST-001",
                "NombreProyecto": "Proyecto Test",
                "Juridica": "Sí",
                "Edicion": "1.0",
                "FechaEdicion": "2024-01-01",
                "FechaPrevistaCierre": "2024-02-01",
                "FechaMaxProximaPublicacion": "2024-03-01",
                "Dias": "30",
                "NombreUsuarioCalidad": "Usuario Calidad",
            }
        ]

        result = self.manager._generate_editions_table_html("Test Title", data)

        self.assertIn("Test Title", result)
        self.assertIn("Total: 1 elementos", result)
        self.assertIn("<table>", result)
        self.assertIn("TEST-001", result)
        self.assertIn("Proyecto Test", result)

    def test_generate_editions_table_html_no_data(self):
        """Prueba generación de tabla HTML para ediciones sin datos."""
        result = self.manager._generate_editions_table_html("Empty Title", [])

        self.assertEqual(result, "")

    def test_generate_editions_ready_table_html_with_data(self):
        """Prueba generación de tabla HTML para ediciones preparadas con datos."""
        data = [
            {
                "Nemotecnico": "TEST-001",
                "NombreProyecto": "Proyecto Test",
                "Juridica": "Sí",
                "Edicion": "1.0",
                "FechaEdicion": "2024-01-01",
                "NombreUsuarioCalidad": "Usuario Calidad",
            }
        ]

        result = self.manager._generate_editions_ready_table_html("Ready Title", data)

        self.assertIn("Ready Title", result)
        self.assertIn("Total: 1 elementos", result)
        self.assertIn("<table>", result)
        self.assertIn("TEST-001", result)
        self.assertIn("Proyecto Test", result)

    def test_generate_editions_ready_table_html_no_data(self):
        """Prueba generación de tabla HTML para ediciones preparadas sin datos."""
        result = self.manager._generate_editions_ready_table_html("Empty Title", [])

        self.assertEqual(result, "")

    def test_generate_risks_table_html_with_data(self):
        """Prueba generación de tabla HTML para riesgos con datos."""
        data = [
            {
                "IDRiesgo": 1,
                "Nemotecnico": "TEST-001",
                "DescripcionRiesgo": "Riesgo de prueba",
                "UsuarioCalidad": "Usuario Calidad",
            }
        ]

        result = self.manager._generate_risks_table_html("Risks Title", data)

        self.assertIn("Risks Title", result)
        self.assertIn("Total: 1 elementos", result)
        self.assertIn("<table>", result)
        self.assertIn("1", result)
        self.assertIn("TEST-001", result)
        self.assertIn("Riesgo de prueba", result)

    def test_generate_risks_table_html_no_data(self):
        """Prueba generación de tabla HTML para riesgos sin datos."""
        result = self.manager._generate_risks_table_html("Empty Title", [])

        self.assertEqual(result, "")


if __name__ == "__main__":
    unittest.main()
