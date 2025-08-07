"""
Esquemas de bases de datos para regeneración offline
Este archivo contiene las estructuras completas de las tablas necesarias
para crear bases de datos locales sin acceso a la red de oficina.
"""

# Esquema completo de la base de datos de correos
CORREOS_DATABASE_SCHEMA = {
    "TbCorreos": {
        "fields": [
            ("IDCorreo", "AUTOINCREMENT PRIMARY KEY"),
            ("Aplicacion", "TEXT(50)"),
            ("Asunto", "TEXT(255)"),
            ("Cuerpo", "MEMO"),
            ("Destinatarios", "TEXT(255)"),
            ("DestinatariosConCopia", "TEXT(255)"),
            ("DestinatariosConCopiaOculta", "TEXT(255)"),
            ("URLAdjunto", "TEXT(255)"),
            ("FechaGrabacion", "DATETIME"),
            ("FechaEnvio", "DATETIME")
        ],
        "description": "Tabla principal de correos registrados"
    },
    
    "TbCorreosEnviados": {
        "fields": [
            ("IDCorreo", "LONG PRIMARY KEY"),
            ("Aplicacion", "TEXT(50)"),
            ("Asunto", "TEXT(255)"),
            ("Cuerpo", "MEMO"),
            ("Destinatarios", "TEXT(255)"),
            ("DestinatariosConCopia", "TEXT(255)"),
            ("DestinatariosConCopiaOculta", "TEXT(255)"),
            ("URLAdjunto", "TEXT(255)"),
            ("FechaGrabacion", "DATETIME"),
            ("FechaEnvio", "DATETIME")
        ],
        "description": "Tabla de correos pendientes de envío y enviados"
    },
    
    "TbConfigCorreos": {
        "fields": [
            ("ID", "AUTOINCREMENT PRIMARY KEY"),
            ("ServidorSMTP", "TEXT(100)"),
            ("Puerto", "INTEGER"),
            ("Usuario", "TEXT(100)"),
            ("Password", "TEXT(100)"),
            ("SSL", "YESNO"),
            ("Timeout", "INTEGER"),
            ("Activo", "YESNO")
        ],
        "description": "Configuración del servidor SMTP"
    },
    
    "TbPlantillasCorreo": {
        "fields": [
            ("ID", "AUTOINCREMENT PRIMARY KEY"),
            ("Aplicacion", "TEXT(50)"),
            ("Nombre", "TEXT(100)"),
            ("Asunto", "TEXT(255)"),
            ("Cuerpo", "MEMO"),
            ("Activa", "YESNO")
        ],
        "description": "Plantillas de correos por aplicación"
    }
}

# Datos iniciales para la configuración de correos
CORREOS_INITIAL_DATA = {
    "TbConfigCorreos": [
        {
            "ServidorSMTP": "10.73.54.85",
            "Puerto": 25,
            "Usuario": "",
            "Password": "",
            "SSL": False,
            "Timeout": 5,
            "Activo": True
        }
    ]
}

# Esquema para la base de datos de No Conformidades (tabla de avisos)
NC_DATABASE_SCHEMA = {
    "TbNCARAvisos": {
        "fields": [
            ("ID", "LONG PRIMARY KEY"),
            ("IDAR", "LONG"),
            ("IDCorreo15", "LONG"),
            ("IDCorreo7", "LONG"),
            ("IDCorreo0", "LONG"),
            ("Fecha", "DATETIME")
        ],
        "description": "Tabla de avisos de Acciones Realizadas en No Conformidades"
    }
}

# Esquema para la base de datos de tareas
TAREAS_DATABASE_SCHEMA = {
    "TbTareas": {
        "fields": [
            ("ID", "AUTOINCREMENT PRIMARY KEY"),
            ("Tarea", "TEXT(50)"),
            ("Fecha", "DATETIME"),
            ("Realizado", "TEXT(2)")
        ],
        "description": "Tabla de control de tareas ejecutadas"
    }
}

def get_create_table_sql(table_name: str, schema: dict) -> str:
    """
    Genera el SQL para crear una tabla basado en su esquema
    
    Args:
        table_name: Nombre de la tabla
        schema: Diccionario con la definición de campos
        
    Returns:
        String con el comando CREATE TABLE
    """
    fields_sql = []
    
    for field_name, field_type in schema["fields"]:
        fields_sql.append(f"[{field_name}] {field_type}")
    
    sql = f"CREATE TABLE [{table_name}] (\n"
    sql += ",\n".join(f"    {field}" for field in fields_sql)
    sql += "\n);"
    
    return sql

def get_all_correos_tables_sql() -> list:
    """
    Retorna una lista con todos los comandos SQL para crear las tablas de correos
    """
    sql_commands = []
    
    for table_name, schema in CORREOS_DATABASE_SCHEMA.items():
        sql_commands.append(get_create_table_sql(table_name, schema))
    
    return sql_commands

def get_correos_initial_data_sql() -> list:
    """
    Retorna una lista con los comandos SQL para insertar datos iniciales en correos
    """
    sql_commands = []
    
    for table_name, records in CORREOS_INITIAL_DATA.items():
        for record in records:
            fields = list(record.keys())
            values = []
            
            for field in fields:
                value = record[field]
                if isinstance(value, str):
                    values.append(f"'{value}'")
                elif isinstance(value, bool):
                    values.append("True" if value else "False")
                elif value is None:
                    values.append("NULL")
                else:
                    values.append(str(value))
            
            fields_str = ", ".join(f"[{field}]" for field in fields)
            values_str = ", ".join(values)
            
            sql = f"INSERT INTO [{table_name}] ({fields_str}) VALUES ({values_str});"
            sql_commands.append(sql)
    
    return sql_commands

# Información adicional sobre las aplicaciones que usan correos
APLICACIONES_CORREOS = {
    "EXPEDIENTES": {
        "descripcion": "Sistema de gestión de expedientes",
        "from_email": "EXPEDIENTES.DySN@telefonica.com"
    },
    "NC": {
        "descripcion": "Sistema de No Conformidades", 
        "from_email": "NC.DySN@telefonica.com"
    },
    "BRASS": {
        "descripcion": "Sistema de gestión de equipos BRASS",
        "from_email": "BRASS.DySN@telefonica.com"
    },
    "RIESGOS": {
        "descripcion": "Sistema de gestión de riesgos",
        "from_email": "RIESGOS.DySN@telefonica.com"
    },
    "AGEDYS": {
        "descripcion": "Sistema AGEDYS",
        "from_email": "AGEDYS.DySN@telefonica.com"
    }
}

# Configuración de destinatarios por defecto
DEFAULT_EMAIL_CONFIG = {
    "admin_bcc": "Andres.RomandelPeral@telefonica.com",
    "smtp_server": "10.73.54.85",
    "smtp_port": 25,
    "smtp_timeout": 5
}