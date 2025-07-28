#!/usr/bin/env python3
"""
Script de prueba para verificar el envío de correos del sistema de riesgos.
"""

import sys
import os
from datetime import datetime
from unittest.mock import Mock, patch

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.common.config import config
from src.riesgos.riesgos_manager import RiesgosManager
from src.common.notifications import send_notification_email

def test_smtp_connection():
    """Prueba la conexión SMTP enviando un correo de prueba."""
    print("=== Prueba de Conexión SMTP ===")
    
    try:
        # Datos de prueba
        test_email = "test@example.com"
        subject = "Prueba SMTP - Sistema de Riesgos"
        content = """
        <html>
        <body>
            <h1>Prueba de Correo</h1>
            <p>Este es un correo de prueba del sistema de gestión de riesgos.</p>
            <p>Fecha: {}</p>
            <p>Si recibes este correo, la configuración SMTP está funcionando correctamente.</p>
        </body>
        </html>
        """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        print(f"Enviando correo de prueba a: {test_email}")
        print(f"Servidor SMTP: {config.smtp_server}")
        print(f"Puerto SMTP: {config.smtp_port}")
        
        send_notification_email(
            test_email,
            subject,
            content,
            is_html=True
        )
        
        print("✅ Correo enviado exitosamente")
        return True
        
    except Exception as e:
        print(f"❌ Error enviando correo: {e}")
        return False

def test_riesgos_with_mock_data():
    """Prueba el sistema de riesgos con datos simulados."""
    print("\n=== Prueba de Sistema de Riesgos con Datos Simulados ===")
    
    try:
        # Crear manager
        manager = RiesgosManager(config.get_db_riesgos_connection_string())
        
        # Simular usuarios
        mock_users = {
            'user1': ('Juan Pérez', 'juan.perez@test.com'),
            'user2': ('María García', 'maria.garcia@test.com'),
            'admin': ('Administrador', 'admin@test.com')
        }
        
        print(f"Usuarios simulados: {len(mock_users)}")
        
        # Mockear el método get_distinct_users
        with patch.object(manager, 'get_distinct_users', return_value=mock_users):
            # Mockear el método _generate_technical_report_html para evitar consultas a BD
            def mock_generate_report(user_id, user_name):
                return f"""
                <html>
                <body>
                    <h1>Informe Técnico de Riesgos - {user_name}</h1>
                    <p>Usuario: {user_id}</p>
                    <p>Fecha: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                    <p>Este es un informe simulado para pruebas del sistema SMTP.</p>
                    <h2>Resumen</h2>
                    <ul>
                        <li>Proyectos pendientes: 5</li>
                        <li>Riesgos identificados: 3</li>
                        <li>Acciones requeridas: 2</li>
                    </ul>
                </body>
                </html>
                """
            
            with patch.object(manager, '_generate_technical_report_html', side_effect=mock_generate_report):
                print("Ejecutando tarea técnica con datos simulados...")
                
                result = manager.execute_technical_task()
                
                if result:
                    print("✅ Tarea técnica ejecutada exitosamente")
                    print(f"Se enviaron correos a {len(mock_users)} usuarios")
                    return True
                else:
                    print("❌ Error ejecutando tarea técnica")
                    return False
                    
    except Exception as e:
        print(f"❌ Error en prueba de riesgos: {e}")
        return False

def main():
    """Función principal."""
    print("Iniciando pruebas del sistema de correos de riesgos...")
    print(f"Configuración actual:")
    print(f"  - SMTP Server: {config.smtp_server}")
    print(f"  - SMTP Port: {config.smtp_port}")
    print(f"  - SMTP User: {config.smtp_user}")
    print()
    
    # Prueba 1: Conexión SMTP básica
    smtp_ok = test_smtp_connection()
    
    # Prueba 2: Sistema de riesgos con datos simulados
    riesgos_ok = test_riesgos_with_mock_data()
    
    print("\n=== Resumen de Pruebas ===")
    print(f"Conexión SMTP: {'✅ OK' if smtp_ok else '❌ FALLO'}")
    print(f"Sistema Riesgos: {'✅ OK' if riesgos_ok else '❌ FALLO'}")
    
    if smtp_ok and riesgos_ok:
        print("\n🎉 Todas las pruebas pasaron exitosamente!")
        return 0
    else:
        print("\n⚠️  Algunas pruebas fallaron. Revisa la configuración.")
        return 1

if __name__ == "__main__":
    sys.exit(main())