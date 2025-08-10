"""
Tests unitarios para utilidades específicas del módulo BRASS
"""
import pytest
import sys
from pathlib import Path
from datetime import datetime, date
from unittest.mock import patch, mock_open

# Añadir src al path
src_path = Path(__file__).parent.parent.parent.parent / "src"
sys.path.insert(0, str(src_path))


class TestBrassUtils:
    """Tests para utilidades específicas del módulo BRASS"""
    
    def test_brass_safe_str_with_none(self):
        """Test BRASS: conversión segura de None para equipos"""
        from common.utils import safe_str
        
        # Simular datos de equipo con valores None
        equipo_nombre = None
        equipo_modelo = None
        
        assert safe_str(equipo_nombre) == "&nbsp;"
        assert safe_str(equipo_modelo) == "&nbsp;"
    
    def test_brass_safe_str_with_equipment_data(self):
        """Test BRASS: conversión segura de datos reales de equipos"""
        from common.utils import safe_str
        
        # Simular datos reales de equipos BRASS
        equipo_nombre = "FLUKE 175 TRUE RMS MULTIMETER"
        equipo_ns = "NS123456"
        equipo_marca = "FLUKE"
        
        assert safe_str(equipo_nombre) == "FLUKE 175 TRUE RMS MULTIMETER"
        assert safe_str(equipo_ns) == "NS123456"
        assert safe_str(equipo_marca) == "FLUKE"
    
    # Eliminado test de wrapper HTML legacy
    
    def test_brass_workday_calculation(self):
        """Test BRASS: cálculo de días laborables para ejecución de tareas"""
        from common.utils import is_workday
        
        # Test días de la semana (lunes a viernes son laborables)
        # Usando fechas conocidas de 2024
        monday = date(2024, 1, 1)  # Lunes
        saturday = date(2024, 1, 6)  # Sábado
        
        assert is_workday(monday) == True
        assert is_workday(saturday) == False
    
    def test_brass_holiday_check(self):
        """Test BRASS: verificación de días festivos para programación de tareas"""
        from common.utils import is_workday
        
        # Test básico sin archivo de festivos
        monday = date(2024, 1, 1)  # Lunes
        saturday = date(2024, 1, 6)  # Sábado
        
        # Sin archivo de festivos, solo verifica día de la semana
        assert is_workday(monday, None) == True
        assert is_workday(saturday, None) == False
