"""
Script para probar específicamente la actualización de FechaEnvio en la base de tareas
"""
import logging
from datetime import datetime
from common.config import config
from common.database import AccessDatabase

# Configurar logging detallado
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def probar_actualizacion_tareas():
    """Probar actualización específica en base de tareas"""
    print("\n🔧 PROBANDO ACTUALIZACIÓN EN BASE DE TAREAS")
    print("=" * 50)
    
    try:
        # Conectar a base de tareas
        db_tareas = AccessDatabase(config.get_db_connection_string('tareas'))
        print("✅ Conexión establecida con base de tareas")
        
        # Obtener correos pendientes
        query_pendientes = """
            SELECT IDCorreo, Asunto, FechaGrabacion, FechaEnvio
            FROM TbCorreosEnviados 
            WHERE FechaEnvio Is Null
            ORDER BY IDCorreo DESC
        """
        
        correos_pendientes = db_tareas.execute_query(query_pendientes)
        print(f"📧 Correos pendientes encontrados: {len(correos_pendientes)}")
        
        if not correos_pendientes:
            print("❌ No hay correos pendientes para probar")
            return
        
        # Tomar el primer correo pendiente
        correo_test = correos_pendientes[0]
        id_correo = correo_test['IDCorreo']
        
        print(f"\n🎯 Probando con correo ID: {id_correo}")
        print(f"   Asunto: {correo_test['Asunto'][:50]}...")
        print(f"   FechaEnvio actual: {correo_test['FechaEnvio']}")
        
        # Intentar actualización directa
        fecha_actual = datetime.now()
        print(f"\n⏰ Intentando actualizar con fecha: {fecha_actual}")
        
        # Método 1: Usando update_record
        print("\n📝 Método 1: Usando update_record")
        update_data = {"FechaEnvio": fecha_actual}
        where_clause = f"IDCorreo = {id_correo}"
        
        try:
            success = db_tareas.update_record("TbCorreosEnviados", update_data, where_clause)
            print(f"   Resultado update_record: {success}")
        except Exception as e:
            print(f"   ❌ Error en update_record: {e}")
            logger.exception("Detalles del error update_record:")
        
        # Verificar si se actualizó
        print("\n🔍 Verificando actualización...")
        verify_query = f"SELECT FechaEnvio FROM TbCorreosEnviados WHERE IDCorreo = {id_correo}"
        verify_result = db_tareas.execute_query(verify_query)
        
        if verify_result:
            fecha_verificada = verify_result[0]['FechaEnvio']
            print(f"   FechaEnvio después de actualización: {fecha_verificada}")
            
            if fecha_verificada is not None:
                print("   ✅ Actualización EXITOSA")
            else:
                print("   ❌ Actualización FALLÓ - FechaEnvio sigue siendo NULL")
        else:
            print("   ❌ No se pudo verificar - registro no encontrado")
        
        # Método 2: Usando execute_non_query directamente
        print("\n📝 Método 2: Usando execute_non_query directamente")
        try:
            # Resetear para segunda prueba
            reset_query = f"UPDATE TbCorreosEnviados SET FechaEnvio = NULL WHERE IDCorreo = {id_correo}"
            db_tareas.execute_non_query(reset_query)
            print("   🔄 Campo reseteado a NULL")
            
            # Actualización directa con SQL
            fecha_str = fecha_actual.strftime('%Y-%m-%d %H:%M:%S')
            direct_query = f"UPDATE TbCorreosEnviados SET FechaEnvio = #{fecha_str}# WHERE IDCorreo = {id_correo}"
            
            rows_affected = db_tareas.execute_non_query(direct_query)
            print(f"   Filas afectadas: {rows_affected}")
            
            # Verificar segunda actualización
            verify_result2 = db_tareas.execute_query(verify_query)
            if verify_result2:
                fecha_verificada2 = verify_result2[0]['FechaEnvio']
                print(f"   FechaEnvio después de SQL directo: {fecha_verificada2}")
                
                if fecha_verificada2 is not None:
                    print("   ✅ Actualización SQL directa EXITOSA")
                else:
                    print("   ❌ Actualización SQL directa FALLÓ")
            
        except Exception as e:
            print(f"   ❌ Error en execute_non_query: {e}")
            logger.exception("Detalles del error execute_non_query:")
        
    except Exception as e:
        print(f"❌ Error general: {e}")
        logger.exception("Detalles del error general:")

if __name__ == "__main__":
    probar_actualizacion_tareas()