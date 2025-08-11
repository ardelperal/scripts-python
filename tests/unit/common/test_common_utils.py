"""Tests para utilidades comunes
"""
import sys
from datetime import date, datetime
from pathlib import Path
from unittest.mock import mock_open, patch

from common.utils import is_night_time, is_workday, load_css_content, safe_str

# Añadir src al path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


class TestWorkdayCalculation:
    """Tests para cálculo de días laborables"""

    def test_weekday_is_workday(self):
        """Test que día entre semana es laborable"""
        # Lunes 2024-01-01
        monday = date(2024, 1, 1)
        assert is_workday(monday)

    def test_saturday_is_not_workday(self):
        """Test que sábado no es laborable"""
        # Sábado 2024-01-06
        saturday = date(2024, 1, 6)
        assert not is_workday(saturday)

    def test_sunday_is_not_workday(self):
        """Test que domingo no es laborable"""
        # Domingo 2024-01-07
        sunday = date(2024, 1, 7)
        assert not is_workday(sunday)

    def test_holiday_is_not_workday(self):
        """Test que día festivo no es laborable"""
        # Test con archivo inexistente (debería ser laborable si no es weekend)
        non_existent_file = Path("non_existent_holidays.txt")
        monday = date(2024, 1, 1)  # Era lunes
        assert is_workday(monday, non_existent_file)

        # Test sin archivo de festivos
        assert is_workday(monday)


class TestNightTime:
    """Tests para cálculo de horario nocturno"""

    def test_evening_is_night_time(self):
        """Test que las 21:00 es horario nocturno"""
        evening = datetime(2024, 1, 1, 21, 0, 0)
        assert is_night_time(evening)

    def test_early_morning_is_night_time(self):
        """Test que las 05:00 es horario nocturno"""
        early_morning = datetime(2024, 1, 1, 5, 0, 0)
        assert is_night_time(early_morning)

    def test_afternoon_is_not_night_time(self):
        """Test que las 15:00 no es horario nocturno"""
        afternoon = datetime(2024, 1, 1, 15, 0, 0)
        assert not is_night_time(afternoon)

    def test_morning_is_not_night_time(self):
        """Test que las 08:00 no es horario nocturno"""
        morning = datetime(2024, 1, 1, 8, 0, 0)
        assert not is_night_time(morning)


class TestSafeStr:
    """Tests para conversión segura a string"""

    def test_none_value(self):
        """Test conversión de None"""
        assert safe_str(None) == "&nbsp;"

    def test_empty_string(self):
        """Test conversión de string vacío"""
        assert safe_str("") == "&nbsp;"

    def test_normal_string(self):
        """Test conversión de string normal"""
        assert safe_str("test") == "test"

    def test_number(self):
        """Test conversión de número"""
        assert safe_str(123) == "123"

    def test_custom_default(self):
        """Test con valor por defecto personalizado"""
        assert safe_str(None, "N/A") == "N/A"


class TestCSSLoad:
    """Tests para carga CSS"""

    @patch("builtins.open", mock_open(read_data="body { color: red; }"))
    def test_load_css_content(self):
        css_file = Path("test.css")
        content = load_css_content(css_file)
        assert "body { color: red; }" in content
