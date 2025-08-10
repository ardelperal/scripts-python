"""Herramienta para inspeccionar la última entrada AGEDYS en TbCorreosEnviados.
Muestra IDCorreo, asunto y cabeceras de las primeras tablas HTML.
"""
from common.config import Config
from common.database import AccessDatabase
import re

def main():
    cfg=Config()
    db=AccessDatabase(cfg.get_db_tareas_connection_string())
    with db.get_connection() as conn:
        cur=conn.cursor()
        cur.execute("SELECT IDCorreo, Asunto, Cuerpo FROM TbCorreosEnviados WHERE Aplicacion='AGEDYS' ORDER BY IDCorreo DESC")
        row=cur.fetchone()
        if not row:
            print('No hay correos AGEDYS')
            return
        print('IDCorreo:', row.IDCorreo)
        print('Asunto :', row.Asunto)
        cuerpo=row.Cuerpo
        tablas=list(re.finditer(r'<table[^>]*>.*?</table>', cuerpo, re.S))
        print('Tablas encontradas:', len(tablas))
        for i,m in enumerate(tablas[:6]):
            heads=re.findall(r'<th>(.*?)</th>', m.group(0))
            print(f'Tabla {i+1} headers ({len(heads)}):', ', '.join(heads))
        print('Longitud HTML:', len(cuerpo))

if __name__ == '__main__':
    main()
