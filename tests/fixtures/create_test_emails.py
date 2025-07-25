#!/usr/bin/env python3
"""
Script simple para crear correos de prueba
"""
import sqlite3
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_test_emails():
    """Crear correos de prueba en la base de datos SQLite"""
    db_path = "dbs-sqlite/correos_datos.sqlite"
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Datos de prueba para correos
        correos_prueba = [
            {
                'Aplicacion': 'BRASS',
                'Originador': 'Sistema',
                'Destinatarios': 'test1@empresa.com',
                'DestinatariosConCopia': '',
                'DestinatariosConCopiaOculta': 'admin@empresa.com',
                'Asunto': '🔧 BRASS - Equipos pendientes de calibración',
                'Cuerpo': '''<h2>Reporte de Calibraciones BRASS</h2>
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
<small>Este es un correo de prueba del sistema BRASS automatizado.</small>''',
                'URLAdjunto': '',
                'Observaciones': 'Test BRASS',
                'NDPD': '',
                'NPEDIDO': '',
                'NFACTURA': '',
                'CuerpoHTML': 'True',
                'IDEdicion': 1
            },
            {
                'Aplicacion': 'Tareas',
                'Originador': 'Sistema',
                'Destinatarios': 'test2@empresa.com;test3@empresa.com',
                'DestinatariosConCopia': 'supervisor@empresa.com',
                'DestinatariosConCopiaOculta': 'admin@empresa.com',
                'Asunto': '📋 Tareas pendientes - Resumen semanal',
                'Cuerpo': '''<h2>📊 Resumen de Tareas Pendientes</h2>
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
<small>Sistema automático de gestión de tareas</small>''',
                'URLAdjunto': '',
                'Observaciones': 'Test Tareas',
                'NDPD': '',
                'NPEDIDO': '',
                'NFACTURA': '',
                'CuerpoHTML': 'True',
                'IDEdicion': 1
            },
            {
                'Aplicacion': 'Sistema',
                'Originador': 'Admin',
                'Destinatarios': 'admin@empresa.com',
                'DestinatariosConCopia': '',
                'DestinatariosConCopiaOculta': '',
                'Asunto': '🤖 Prueba del sistema de correos - Docker SMTP',
                'Cuerpo': f'''<h2>✅ Prueba del Sistema de Correos</h2>
<p>Este es un correo de prueba para verificar que el sistema funciona correctamente.</p>

<h3>📊 Información del Sistema</h3>
<ul>
    <li><strong>Entorno:</strong> Desarrollo (Docker)</li>
    <li><strong>SMTP:</strong> MailHog (Puerto 1025)</li>
    <li><strong>Fecha:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
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
<small>Correo generado automáticamente por el sistema de scripts continuos</small>''',
                'URLAdjunto': '',
                'Observaciones': 'Test Sistema',
                'NDPD': '',
                'NPEDIDO': '',
                'NFACTURA': '',
                'CuerpoHTML': 'True',
                'IDEdicion': 1
            }
        ]
        
        # Insertar correos de prueba
        for correo in correos_prueba:
            cursor.execute('''
                INSERT INTO TbCorreosEnviados 
                (URLAdjunto, Aplicacion, Originador, Destinatarios, DestinatariosConCopia, 
                 DestinatariosConCopiaOculta, Asunto, Cuerpo, FechaEnvio, Observaciones, 
                 NDPD, NPEDIDO, NFACTURA, FechaGrabacion, CuerpoHTML, IDEdicion)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                correo['URLAdjunto'],
                correo['Aplicacion'],
                correo['Originador'],
                correo['Destinatarios'],
                correo['DestinatariosConCopia'],
                correo['DestinatariosConCopiaOculta'],
                correo['Asunto'],
                correo['Cuerpo'],
                correo['Observaciones'],
                correo['NDPD'],
                correo['NPEDIDO'],
                correo['NFACTURA'],
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                correo['CuerpoHTML'],
                correo['IDEdicion']
            ))
        
        conn.commit()
        
        # Verificar inserción
        cursor.execute("SELECT COUNT(*) FROM TbCorreosEnviados WHERE FechaEnvio IS NULL")
        count = cursor.fetchone()[0]
        
        logger.info(f"Correos de prueba creados exitosamente")
        logger.info(f"Total correos pendientes: {count}")
        
        return True

def show_pending_emails():
    """Mostrar correos pendientes de envío"""
    db_path = "dbs-sqlite/correos_datos.sqlite"
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT IDCorreo, Aplicacion, Asunto, Destinatarios, FechaGrabacion
            FROM TbCorreosEnviados 
            WHERE FechaEnvio IS NULL
            ORDER BY IDCorreo
        ''')
        
        correos = cursor.fetchall()
        
        print(f"\nCorreos pendientes de envío ({len(correos)}):")
        print("=" * 70)
        
        for correo in correos:
            id_correo, aplicacion, asunto, destinatarios, fecha_grabacion = correo
            print(f"ID: {id_correo}")
            print(f"   App: {aplicacion}")
            print(f"   Asunto: {asunto}")
            print(f"   Para: {destinatarios}")
            print(f"   Creado: {fecha_grabacion}")
            print("-" * 50)

if __name__ == "__main__":
    logger.info("Creando correos de prueba...")
    create_test_emails()
    show_pending_emails()