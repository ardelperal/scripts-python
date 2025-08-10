from src.agedys.agedys_manager import AgedysManager
from unittest.mock import Mock


class StubDB:
    def execute_query(self, sql, params=None):
        return []


def main():
    m = AgedysManager(StubDB(), None)
    m.get_dpds_sin_visado_calidad_agrupado = Mock(return_value=[{
        'CODPROYECTOS': 'D1', 'PETICIONARIO': 'Tec', 'FECHAPETICION': '2025-01-01',
        'CodExp': 'E1', 'DESCRIPCION': 'Desc', 'ResponsableCalidad': 'RC'
    }])
    html = m.generate_quality_report_html()
    print(html)


if __name__ == '__main__':
    main()
