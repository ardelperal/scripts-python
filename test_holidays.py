# test_holidays.py
import holidays
from datetime import date

print("--- Iniciando prueba de la librería 'holidays' ---")

try:
    # Obtener el año actual
    current_year = date.today().year
    
    # Intentar inicializar los festivos para España (ES). 
    # Usamos 'MD' para la provincia de Madrid como ejemplo.
    es_holidays = holidays.Spain(years=current_year, prov='MD')
    
    # Verificar si la librería funciona buscando un festivo conocido
    if date(current_year, 1, 1) in es_holidays:
        print(f"✅ ÉXITO: La librería 'holidays' se ha cargado correctamente.")
        print(f"   Festivo de ejemplo encontrado: {es_holidays.get(date(current_year, 1, 1))}")
    else:
        # Esto sería muy raro, pero es una comprobación extra
        print(f"⚠️  ADVERTENCIA: La librería se cargó, pero no se encontró un festivo esperado (1 de Enero).")

except Exception as e:
    print(f"❌ ERROR: No se pudo inicializar o usar la librería 'holidays'.")
    print(f"   Detalle del error: {e}")

print("--- Prueba finalizada ---")
