import os
import sqlite3
import pyodbc
import pytest
from datetime import datetime

DB_SQLITE = 'dbs-sqlite/correos_datos.sqlite'
DB_ACCESS = 'dbs-locales/correos_datos.accdb'
DB_PASSWORD = os.getenv('DB_PASSWORD', 'dpddpd')

# 1. Test de conexión
def test_conexion_sqlite():
    conn = sqlite3.connect(DB_SQLITE)
    conn.execute('SELECT 1')
    conn.close()

def test_conexion_access():
    conn_str = f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={DB_ACCESS};PWD={DB_PASSWORD};"
    conn = pyodbc.connect(conn_str)
    conn.close()

# 2. Test de estructura (comparar columnas)
def test_estructura_tabla():
    # Obtener columnas de SQLite
    conn = sqlite3.connect(DB_SQLITE)
    cursor = conn.execute('PRAGMA table_info(TbCorreosEnviados)')
    cols_sqlite = [row[1] for row in cursor.fetchall()]
    conn.close()
    # Obtener columnas de Access
    conn_str = f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={DB_ACCESS};PWD={DB_PASSWORD};"
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    cursor.execute('SELECT TOP 1 * FROM TbCorreosEnviados')
    cols_access = [desc[0] for desc in cursor.description]
    conn.close()
    # Deben ser iguales (orden y nombre)
    assert cols_sqlite == cols_access, f"Columnas distintas: SQLite={cols_sqlite}, Access={cols_access}"

# 3. Test de inserción y sincronización
def test_insercion_y_sincronizacion():
    # Insertar en Access con todos los campos obligatorios
    conn_str = f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={DB_ACCESS};PWD={DB_PASSWORD};"
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    asunto = 'TEST_INSERT_SYNC'
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute("""
        INSERT INTO TbCorreosEnviados (
            URLAdjunto, Aplicacion, Originador, Destinatarios, DestinatariosConCopia, DestinatariosConCopiaOculta, Asunto, Cuerpo, FechaEnvio, Observaciones, NDPD, NPEDIDO, NFACTURA, FechaGrabacion, CuerpoHTML, IDEdicion
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        '', 'TEST', 'ORIG', 'test@correo.com', '', '', asunto, 'CUERPO', None, '', '', '', '', None, False, 1
    ))
    conn.commit()
    cursor.execute("SELECT @@IDENTITY")
    id_insert = int(cursor.fetchone()[0])
    conn.close()
    os.system('python src/scripts/enviar_correo_no_enviado.py')
    conn = sqlite3.connect(DB_SQLITE)
    cursor = conn.cursor()
    cursor.execute("SELECT IDCorreo FROM TbCorreosEnviados WHERE IDCorreo=?", (id_insert,))
    found = cursor.fetchone()
    conn.close()
    assert found is not None, f"No se sincronizó el correo ID {id_insert} de Access a SQLite"
    # Limpiar
    conn = sqlite3.connect(DB_SQLITE)
    conn.execute("DELETE FROM TbCorreosEnviados WHERE IDCorreo=?", (id_insert,))
    conn.commit()
    conn.close()
    conn = pyodbc.connect(conn_str)
    conn.execute("DELETE FROM TbCorreosEnviados WHERE IDCorreo=?", (id_insert,))
    conn.commit()
    conn.close()

# 4. Test de envío y sincronización
def test_envio_y_sincronizacion():
    # Insertar pendiente en SQLite con todos los campos obligatorios
    conn = sqlite3.connect(DB_SQLITE)
    asunto = 'TEST_ENVIO_SYNC'
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn.execute("""
        INSERT INTO TbCorreosEnviados (
            URLAdjunto, Aplicacion, Originador, Destinatarios, DestinatariosConCopia, DestinatariosConCopiaOculta, Asunto, Cuerpo, FechaEnvio, Observaciones, NDPD, NPEDIDO, NFACTURA, FechaGrabacion, CuerpoHTML, IDEdicion
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        '', 'TEST', 'ORIG', 'test@correo.com', '', '', asunto, 'CUERPO', None, '', '', '', '', None, False, 1
    ))
    conn.commit()
    cursor = conn.execute("SELECT MAX(IDCorreo) FROM TbCorreosEnviados WHERE Asunto=? AND IDCorreo > 0", (asunto,))
    id_insert = cursor.fetchone()[0]
    conn.close()
    # Simular envío (poner FechaEnvio)
    fecha_envio = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = sqlite3.connect(DB_SQLITE)
    conn.execute("UPDATE TbCorreosEnviados SET FechaEnvio=? WHERE IDCorreo=?", (fecha_envio, id_insert))
    conn.commit()
    conn.close()
    os.system('python src/scripts/enviar_correo_no_enviado.py')
    conn_str = f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={DB_ACCESS};PWD={DB_PASSWORD};"
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    cursor.execute("SELECT FechaEnvio FROM TbCorreosEnviados WHERE IDCorreo=?", (id_insert,))
    row = cursor.fetchone()
    conn.close()
    assert row is not None and row[0] is not None, f"No se sincronizó FechaEnvio del correo ID {id_insert} a Access"
    # Limpiar
    conn = sqlite3.connect(DB_SQLITE)
    conn.execute("DELETE FROM TbCorreosEnviados WHERE IDCorreo=?", (id_insert,))
    conn.commit()
    conn.close()
    conn = pyodbc.connect(conn_str)
    conn.execute("DELETE FROM TbCorreosEnviados WHERE IDCorreo=?", (id_insert,))
    conn.commit()
    conn.close()

# 5. Test de integridad final
def test_integridad_final():
    # Comprobar que los ID de pendientes y enviados coinciden
    def get_ids(sql, dbtype='sqlite'):
        if dbtype == 'sqlite':
            conn = sqlite3.connect(DB_SQLITE)
        else:
            conn_str = f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={DB_ACCESS};PWD={DB_PASSWORD};"
            conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute(sql)
        ids = set(row[0] for row in cursor.fetchall())
        conn.close()
        return ids
    sql = "SELECT IDCorreo FROM TbCorreosEnviados WHERE FechaEnvio IS NULL"
    ids_sqlite = get_ids(sql, 'sqlite')
    ids_access = get_ids(sql, 'access')
    assert ids_sqlite == ids_access, f"Pendientes distintos: SQLite={ids_sqlite}, Access={ids_access}"
    sql = "SELECT IDCorreo FROM TbCorreosEnviados WHERE FechaEnvio IS NOT NULL"
    ids_sqlite = get_ids(sql, 'sqlite')
    ids_access = get_ids(sql, 'access')
    assert ids_sqlite == ids_access, f"Enviados distintos: SQLite={ids_sqlite}, Access={ids_access}"

# 6. Test de casos límite (esqueleto)
def test_casos_limite():
    pass  # TODO: probar nulos, adjuntos inexistentes, etc.

# 7. Test de error (esqueleto)
def test_errores():
    pass  # TODO: forzar errores y comprobar manejo 