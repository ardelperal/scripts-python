#!/usr/bin/env python3
"""
Ejemplo de uso del módulo de gestión de riesgos.

Este ejemplo demuestra cómo usar el RiesgosManager para:
- Ejecutar tareas diarias automáticas
- Generar reportes específicos
- Verificar el estado de las tareas
"""

import sys
from pathlib import Path

# Agregar el directorio src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.common.config import Config
from src.riesgos.riesgos_manager import RiesgosManager


def ejemplo_ejecucion_diaria():
    """Ejemplo de ejecución diaria de tareas."""
    print("=== Ejemplo: Ejecución Diaria de Tareas ===")

    # Cargar configuración
    config = Config.from_file("config/config.json")

    # Crear manager
    manager = RiesgosManager(config)

    # Ejecutar tareas diarias
    print("Ejecutando tareas diarias...")
    if manager.execute_daily_task():
        print("✓ Tareas diarias ejecutadas exitosamente")
    else:
        print("✗ Error ejecutando tareas diarias")


def ejemplo_verificacion_tareas():
    """Ejemplo de verificación del estado de las tareas."""
    print("\n=== Ejemplo: Verificación de Estado de Tareas ===")

    # Cargar configuración
    config = Config.from_file("config/config.json")

    # Crear manager
    manager = RiesgosManager(config)

    if not manager.connect():
        print("✗ Error conectando a la base de datos")
        return

    try:
        # Verificar última ejecución de cada tipo de tarea
        tipos_tarea = ["TECNICA", "CALIDAD", "CALIDADMENSUAL"]

        for tipo in tipos_tarea:
            ultima_ejecucion = manager.get_last_execution(tipo)
            if ultima_ejecucion:
                print(f"Tarea {tipo}: Última ejecución {ultima_ejecucion}")
            else:
                print(f"Tarea {tipo}: Nunca ejecutada")

        # Verificar qué tareas deben ejecutarse
        print("\nTareas pendientes:")
        if manager.should_execute_technical_task():
            print("- Tarea técnica debe ejecutarse")
        else:
            print("- Tarea técnica no requiere ejecución")

        if manager.should_execute_quality_task():
            print("- Tarea de calidad debe ejecutarse")
        else:
            print("- Tarea de calidad no requiere ejecución")

        if manager.should_execute_monthly_quality_task():
            print("- Tarea de calidad mensual debe ejecutarse")
        else:
            print("- Tarea de calidad mensual no requiere ejecución")

    finally:
        manager.disconnect()


def ejemplo_ejecucion_forzada():
    """Ejemplo de ejecución forzada de tareas específicas."""
    print("\n=== Ejemplo: Ejecución Forzada de Tareas ===")

    # Cargar configuración
    config = Config.from_file("config/config.json")

    # Crear manager
    manager = RiesgosManager(config)

    if not manager.connect():
        print("✗ Error conectando a la base de datos")
        return

    try:
        # Ejecutar tarea técnica forzada
        print("Ejecutando tarea técnica forzada...")
        if manager.execute_technical_task():
            print("✓ Tarea técnica ejecutada")
            manager.record_task_execution("TECNICA")
        else:
            print("✗ Error ejecutando tarea técnica")

        # Ejecutar tarea de calidad forzada
        print("Ejecutando tarea de calidad forzada...")
        if manager.execute_quality_task():
            print("✓ Tarea de calidad ejecutada")
            manager.record_task_execution("CALIDAD")
        else:
            print("✗ Error ejecutando tarea de calidad")

    finally:
        manager.disconnect()


def ejemplo_obtencion_usuarios():
    """Ejemplo de obtención de usuarios para notificaciones."""
    print("\n=== Ejemplo: Obtención de Usuarios ===")

    # Cargar configuración
    config = Config.from_file("config/config.json")

    # Crear manager
    manager = RiesgosManager(config)

    if not manager.connect():
        print("✗ Error conectando a la base de datos")
        return

    try:
        # Obtener usuarios distintos
        usuarios = manager.get_distinct_users()

        print(f"Usuarios encontrados: {len(usuarios)}")
        for user_id, (nombre, correo) in usuarios.items():
            print(f"- {user_id}: {nombre} ({correo})")

    finally:
        manager.disconnect()


def ejemplo_generacion_reportes():
    """Ejemplo de generación de reportes HTML."""
    print("\n=== Ejemplo: Generación de Reportes ===")

    # Cargar configuración
    config = Config.from_file("config/config.json")

    # Crear manager
    manager = RiesgosManager(config)

    # Generar reporte técnico para un usuario
    print("Generando reporte técnico...")
    html_tecnico = manager._generate_technical_report_html(
        "usuario_test", "Usuario de Prueba"
    )

    # Guardar reporte en archivo
    with open("examples/reporte_tecnico_ejemplo.html", "w", encoding="utf-8") as f:
        f.write(html_tecnico)
    print("✓ Reporte técnico guardado en examples/reporte_tecnico_ejemplo.html")

    # Generar reporte de calidad
    print("Generando reporte de calidad...")
    html_calidad = manager._generate_quality_report_html()

    # Guardar reporte en archivo
    with open("examples/reporte_calidad_ejemplo.html", "w", encoding="utf-8") as f:
        f.write(html_calidad)
    print("✓ Reporte de calidad guardado en examples/reporte_calidad_ejemplo.html")

    # Generar reporte mensual
    print("Generando reporte mensual...")
    html_mensual = manager._generate_monthly_quality_report_html()

    # Guardar reporte en archivo
    with open("examples/reporte_mensual_ejemplo.html", "w", encoding="utf-8") as f:
        f.write(html_mensual)
    print("✓ Reporte mensual guardado en examples/reporte_mensual_ejemplo.html")


def ejemplo_configuracion_personalizada():
    """Ejemplo de uso con configuración personalizada."""
    print("\n=== Ejemplo: Configuración Personalizada ===")

    # Crear configuración personalizada
    config = Config()
    config.database_path = "ruta/personalizada/base_datos.accdb"
    config.smtp_server = "smtp.empresa.com"
    config.smtp_port = 587
    config.smtp_username = "usuario@empresa.com"
    config.smtp_password = "password"
    config.admin_emails = ["admin1@empresa.com", "admin2@empresa.com"]

    print(f"Base de datos: {config.database_path}")
    print(f"Servidor SMTP: {config.smtp_server}:{config.smtp_port}")
    print(f"Emails admin: {config.admin_emails}")

    # Crear manager con configuración personalizada
    RiesgosManager(config)

    print("✓ Manager creado con configuración personalizada")


def main():
    """Función principal que ejecuta todos los ejemplos."""
    print("Ejemplos de uso del módulo de gestión de riesgos")
    print("=" * 50)

    try:
        # Crear directorio de ejemplos si no existe
        Path("examples").mkdir(exist_ok=True)

        # Ejecutar ejemplos
        ejemplo_ejecucion_diaria()
        ejemplo_verificacion_tareas()
        ejemplo_ejecucion_forzada()
        ejemplo_obtencion_usuarios()
        ejemplo_generacion_reportes()
        ejemplo_configuracion_personalizada()

        print("\n" + "=" * 50)
        print("Todos los ejemplos ejecutados correctamente")

    except FileNotFoundError as e:
        print(f"Error: Archivo de configuración no encontrado - {e}")
        print("Asegúrate de tener el archivo config/config.json")
    except Exception as e:
        print(f"Error ejecutando ejemplos: {e}")


if __name__ == "__main__":
    main()
