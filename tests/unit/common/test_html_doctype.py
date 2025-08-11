import os
import sys

sys.path.append(os.path.abspath("src"))
from common.config import Config
from common.db.database import AccessDatabase

# Simple smoke test: latest 5 registros por cada app relevante empiezan con <!DOCTYPE html>
# (Asume tablas ya pobladas en entorno local.)


def fetch_latest_htmls(app, limit=5):
    cfg = Config()
    db = AccessDatabase(cfg.get_db_tareas_connection_string())
    htmls = []
    with db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            f"SELECT TOP {limit} Cuerpo FROM TbCorreosEnviados WHERE Aplicacion=? ORDER BY IDCorreo DESC",
            app,
        )
        rows = cur.fetchall()
        for r in rows:
            htmls.append(r.Cuerpo)
    return htmls


def test_latest_emails_start_with_doctype():
    apps = ["AGEDYS", "RIESGOS", "NC", "EXPEDIENTES"]
    for app in apps:
        htmls = fetch_latest_htmls(app)
        for cuerpo in htmls:
            assert cuerpo.lstrip().startswith(
                "<!DOCTYPE html>"
            ), f"Registro {app} no empieza con <!DOCTYPE html>"
