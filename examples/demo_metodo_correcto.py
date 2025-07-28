#!/usr/bin/env python3
"""
Script para limpiar correos con IDCorreo NULL y demostrar el uso correcto
del método insertar_correo con la regla del máximo + 1
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from common.database_adapter import AccessAdapter
from common.config import config
from correos.correos_manager import CorreosManager

def limpiar_correos_problematicos():
    """Eliminar correos con IDCorreo NULL"""
    print("🧹 Limpiando correos con IDCorreo NULL...")
    
    with AccessAdapter(Path(config.db_correos_path), config.db_password) as db:
        # Eliminar correos con IDCorreo NULL
        delete_query = "DELETE FROM TbCorreosEnviados WHERE IDCorreo IS NULL"
        rows_deleted = db.execute_non_query(delete_query)
        print(f"   Eliminados {rows_deleted} correos con IDCorreo NULL")

def demostrar_metodo_correcto():
    """Demostrar el uso correcto del método insertar_correo"""
    print("\n📧 Demostrando el método correcto para insertar correos...")
    
    correos_manager = CorreosManager()
    
    # Insertar correo usando el método correcto
    id_correo = correos_manager.insertar_correo(
        aplicacion="DemoApp",
        asunto="Demostración - Método Correcto",
        cuerpo="<h2>✅ Método Correcto</h2><p>Este correo fue insertado usando el método <code>insertar_correo()</code> que implementa la regla del <strong>máximo + 1</strong> para obtener el IDCorreo.</p>",
        destinatarios="demo@example.com",
        destinatarios_bcc="admin@example.com"
    )
    
    if id_correo > 0:
        print(f"   ✅ Correo insertado con ID: {id_correo}")
        return id_correo
    else:
        print("   ❌ Error insertando correo")
        return None

def enviar_correos_pendientes():
    """Enviar correos pendientes"""
    print("\n📤 Enviando correos pendientes...")
    
    correos_manager = CorreosManager()
    enviados = correos_manager.enviar_correos_no_enviados()
    print(f"   📧 Correos enviados: {enviados}")
    
    return enviados

def verificar_estado_final():
    """Verificar el estado final de los correos"""
    print("\n🔍 Verificando estado final...")
    
    with AccessAdapter(Path(config.db_correos_path), config.db_password) as db:
        # Contar correos pendientes
        query_pendientes = "SELECT COUNT(*) as Total FROM TbCorreosEnviados WHERE FechaEnvio IS NULL"
        result = db.execute_query(query_pendientes)
        pendientes = result[0]['Total'] if result else 0
        
        # Contar correos enviados hoy (usando sintaxis de Access)
        query_enviados = "SELECT COUNT(*) as Total FROM TbCorreosEnviados WHERE DateValue(FechaEnvio) = Date()"
        try:
            result = db.execute_query(query_enviados)
            enviados_hoy = result[0]['Total'] if result else 0
        except:
            # Si falla, contar todos los enviados
            query_enviados_alt = "SELECT COUNT(*) as Total FROM TbCorreosEnviados WHERE FechaEnvio IS NOT NULL"
            result = db.execute_query(query_enviados_alt)
            enviados_hoy = result[0]['Total'] if result else 0
        
        print(f"   📋 Correos pendientes: {pendientes}")
        print(f"   ✅ Correos enviados: {enviados_hoy}")

def main():
    print("=" * 60)
    print("🎯 DEMOSTRACIÓN: Método Correcto para Obtener ID de Correo")
    print("   Regla: Máximo + 1")
    print("=" * 60)
    
    # 1. Limpiar correos problemáticos
    limpiar_correos_problematicos()
    
    # 2. Demostrar método correcto
    id_correo = demostrar_metodo_correcto()
    
    if id_correo:
        # 3. Enviar correos pendientes
        enviados = enviar_correos_pendientes()
        
        # 4. Verificar estado final
        verificar_estado_final()
        
        print("\n" + "=" * 60)
        print("✅ DEMOSTRACIÓN COMPLETADA EXITOSAMENTE")
        print(f"   📧 Correo insertado con ID: {id_correo}")
        print(f"   📤 Total de correos enviados: {enviados}")
        print("   🎯 El método insertar_correo() funciona correctamente")
        print("=" * 60)
    else:
        print("\n❌ Error en la demostración")

if __name__ == "__main__":
    main()