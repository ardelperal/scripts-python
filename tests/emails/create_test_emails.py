#!/usr/bin/env python3
"""
Script para crear correos de prueba en la base de datos
Para probar el sistema de envío sin usar datos reales
"""
import sqlite3
import logging
from pathlib import Path
from datetime import datetime, timedelta
import random

logger = logging.getLogger(__name__)

def create_test_emails():
    """Crear correos de prueba en la base de datos SQLite"""
    db_path = Path("dbs-sqlite/correos_datos.sqlite")
    
    if not db_path.exists():
        logger.error(f"Base de datos no encontrada: {db_path}")
        logger.info("Ejecuta primero: python create_demo_databases.py")
        return False
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Crear tabla de correos si no existe
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS TbCorreosEnviados (
                IDCorreo INTEGER PRIMARY KEY AUTOINCREMENT,
                Aplicacion TEXT NOT NULL,
                Destinatarios TEXT,
                DestinatariosConCopia TEXT,
                DestinatariosConCopiaOculta TEXT,
                Asunto TEXT NOT NULL,
                Cuerpo TEXT,
                URLAdjunto TEXT,
                FechaEnvio DATETIME,
                FechaCreacion DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Datos de prueba para correos
        correos_prueba = [
            {
                'Aplicacion': 'BRASS',
                'Destinatarios': 'test1@empresa.com',
                'DestinatariosConCopia': '',
                'DestinatariosConCopiaOculta': 'admin@empresa.com',
                'Asunto': '🔧 BRASS - Equipos pendientes de calibración',
                'Cuerpo': '''
                    <h2>Reporte de Calibraciones BRASS</h2>
                    <p>Los siguientes equipos requieren calibración:</p>
                    <ul>
                        <li><strong>EQ001 - Multímetro Digital Fluke</strong><br>
                            📍 Ubicación: Lab A<br>
                            📅 Vencimiento: Próximos 30 días</li>
                        <li><strong>EQ002 - Balanza Analítica</strong><br>
                            📍 Ubicación: Lab B<br>
                            🚨 Estado: VENCIDO</li>
                    </ul>
                    <p>Por favor, programa las calibraciones correspondientes.</p>
                    <hr>
                    <small>Este es un correo de prueba del sistema BRASS automatizado.</small>
                ''',
                'URLAdjunto': None
            },
            {
                'Aplicacion': 'Tareas',
                'Destinatarios': 'test2@empresa.com;test3@empresa.com',
                'DestinatariosConCopia': 'supervisor@empresa.com',
                'DestinatariosConCopiaOculta': 'admin@empresa.com',
                'Asunto': '📋 Tareas pendientes - Resumen semanal',
                'Cuerpo': '''
                    <h2>📊 Resumen de Tareas Pendientes</h2>
                    <p>Estimado equipo,</p>
                    <p>Las siguientes tareas están pendientes de completar:</p>
                    
                    <h3>🚨 Alta Prioridad</h3>
                    <ul>
                        <li>Revisar calibraciones pendientes - <em>Vence en 1 día</em></li>
                        <li>Mantenimiento preventivo - <em>Vence mañana</em></li>
                    </ul>
                    
                    <h3>⚠️ Prioridad Media</h3>
                    <ul>
                        <li>Actualizar inventario - <em>Vence en 7 días</em></li>
                        <li>Revisar documentación - <em>En proceso</em></li>
                    </ul>
                    
                    <p>Gracias por su atención.</p>
                    <hr>
                    <small>Sistema automático de gestión de tareas</small>
                ''',
                'URLAdjunto': None
            },
            {
                'Aplicacion': 'Sistema',
                'Destinatarios': 'admin@empresa.com',
                'DestinatariosConCopia': '',
                'DestinatariosConCopiaOculta': '',
                'Asunto': '🤖 Prueba del sistema de correos - Docker SMTP',
                'Cuerpo': '''
                    <h2>✅ Prueba del Sistema de Correos</h2>
                    <p>Este es un correo de prueba para verificar que el sistema funciona correctamente.</p>
                    
                    <h3>📊 Información del Sistema</h3>
                    <ul>
                        <li><strong>Entorno:</strong> Desarrollo (Docker)</li>
                        <li><strong>SMTP:</strong> MailHog (Puerto 1025)</li>
                        <li><strong>Fecha:</strong> ''' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '''</li>
                        <li><strong>Base de Datos:</strong> SQLite</li>
                    </ul>
                    
                    <h3>🔧 Funcionalidades Probadas</h3>
                    <ul>
                        <li>✅ Conexión SMTP</li>
                        <li>✅ Lectura de base de datos</li>
                        <li>✅ Generación de HTML</li>
                        <li>✅ Gestión de destinatarios</li>
                    </ul>
                    
                    <p>Si recibes este correo, ¡el sistema está funcionando perfectamente! 🎉</p>
                    
                    <hr>
                    <small>Correo generado automáticamente por el sistema de scripts continuos</small>
                ''',
                'URLAdjunto': None
            }
        ]
        
        # Insertar correos de prueba
        for correo in correos_prueba:
            cursor.execute('''
                INSERT INTO TbCorreosEnviados 
                (Aplicacion, Destinatarios, DestinatariosConCopia, DestinatariosConCopiaOculta, 
                 Asunto, Cuerpo, URLAdjunto, FechaEnvio)
                VALUES (?, ?, ?, ?, ?, ?, ?, NULL)
            ''', (
                correo['Aplicacion'],
                correo['Destinatarios'],
                correo['DestinatariosConCopia'],
                correo['DestinatariosConCopiaOculta'],
                correo['Asunto'],
                correo['Cuerpo'],
                correo['URLAdjunto']
            ))
        
        conn.commit()
        
        # Verificar inserción
        cursor.execute("SELECT COUNT(*) FROM TbCorreosEnviados WHERE FechaEnvio IS NULL")
        count = cursor.fetchone()[0]
        
        logger.info(f"Correos de prueba creados")
        logger.info(f"Total correos pendientes: {count}")
        
        return True

def show_pending_emails():
    """Mostrar correos pendientes de envío"""
    db_path = Path("dbs-sqlite/correos_datos.sqlite")
    
    if not db_path.exists():
        print("Base de datos no encontrada")
        return
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT IDCorreo, Aplicacion, Asunto, Destinatarios, FechaCreacion
            FROM TbCorreosEnviados 
            WHERE FechaEnvio IS NULL
            ORDER BY IDCorreo
        ''')
        
        correos = cursor.fetchall()
        
        print(f"\nCorreos pendientes de envío ({len(correos)}):")
        print("=" * 70)
        
        for correo in correos:
            id_correo, aplicacion, asunto, destinatarios, fecha_creacion = correo
            print(f"ID: {id_correo}")
            print(f"   App: {aplicacion}")
            print(f"   Asunto: {asunto}")
            print(f"   Para: {destinatarios}")
            print(f"   Creado: {fecha_creacion}")
            print("-" * 50)

def clear_sent_emails():
    """Limpiar correos ya enviados (para pruebas)"""
    db_path = Path("dbs-sqlite/correos_datos.sqlite")
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        cursor.execute("UPDATE TbCorreosEnviados SET FechaEnvio = NULL")
        affected = cursor.rowcount
        conn.commit()
        
        logger.info(f"Correos marcados como no enviados: {affected}")

def main():
    """Función principal"""
    import argparse
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    parser = argparse.ArgumentParser(description='Gestión de correos de prueba')
    parser.add_argument('--create', action='store_true', help='Crear correos de prueba')
    parser.add_argument('--show', action='store_true', help='Mostrar correos pendientes')
    parser.add_argument('--reset', action='store_true', help='Marcar todos como no enviados')
    
    args = parser.parse_args()
    
    if args.create:
        print("Creando correos de prueba...")
        create_test_emails()
        show_pending_emails()
        
    elif args.show:
        show_pending_emails()
        
    elif args.reset:
        print("Reiniciando estado de correos...")
        clear_sent_emails()
        show_pending_emails()
        
    else:
        # Por defecto, crear y mostrar
        print("Creando correos de prueba...")
        create_test_emails()
        show_pending_emails()
        
        print("\nInstrucciones:")
        print("1. Ejecuta el sistema de correos:")
        print("   python src/scripts/enviar_correo_no_enviado.py")
        print("\n2. O inicia el sistema completo:")
        print("   docker-compose -f docker-compose.yml --profile local up")
        print("\n3. Ver correos enviados en MailHog:")
        print("   http://localhost:8025")

if __name__ == "__main__":
    main()
