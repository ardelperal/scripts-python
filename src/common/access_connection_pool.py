"""Pool de conexiones para Access que maneja concurrencia de forma segura.

Este módulo implementa un pool de conexiones thread-safe para bases de datos Access,
resolviendo los problemas de concurrencia que ocurren cuando múltiples hilos
intentan acceder a la misma base de datos simultáneamente.

Características:
- Pool de conexiones thread-safe
- Manejo de locks para operaciones críticas
- Reutilización de conexiones
- Timeout configurable
- Logging detallado para debugging

Autor: Sistema de Automatización
Fecha: 2025
"""

import logging
import threading
from contextlib import contextmanager
from queue import Empty, Queue
from typing import Any, Optional

try:
    import pyodbc

    PYODBC_AVAILABLE = True
except ImportError:
    PYODBC_AVAILABLE = False

logger = logging.getLogger(__name__)


class AccessConnectionPool:
    """
    Pool de conexiones thread-safe para bases de datos Access.

    Maneja múltiples conexiones a la misma base de datos de forma segura,
    evitando conflictos de concurrencia típicos de Access.
    """

    def __init__(
        self, connection_string: str, max_connections: int = 3, timeout: int = 30
    ):
        """
        Inicializa el pool de conexiones.

        Args:
            connection_string: Cadena de conexión a Access
            max_connections: Número máximo de conexiones simultáneas
            timeout: Timeout en segundos para obtener una conexión
        """
        self.connection_string = connection_string
        self.max_connections = max_connections
        self.timeout = timeout

        # Pool de conexiones disponibles
        self._pool = Queue(maxsize=max_connections)
        self._all_connections = []
        self._lock = threading.RLock()  # Lock reentrante para operaciones críticas
        self._created_connections = 0

        # Estadísticas
        self._stats = {
            "connections_created": 0,
            "connections_reused": 0,
            "operations_completed": 0,
            "operations_failed": 0,
            "concurrent_operations": 0,
            "max_concurrent": 0,
        }

        logger.info(
            f"AccessConnectionPool inicializado - Max conexiones: {max_connections}, "
            f"Timeout: {timeout}s"
        )

    def _create_connection(self):
        """Crea una nueva conexión a Access"""
        if not PYODBC_AVAILABLE:
            raise ImportError("pyodbc es requerido para conexiones Access")

        try:
            connection = pyodbc.connect(self.connection_string)
            connection.autocommit = False  # Manejo manual de transacciones
            self._created_connections += 1
            self._stats["connections_created"] += 1
            self._all_connections.append(connection)

            logger.debug(
                f"Nueva conexión Access creada (Total: {self._created_connections})"
            )
            return connection

        except Exception as e:
            logger.error(f"Error creando conexión Access: {e}")
            raise

    def _get_connection(self):
        """Obtiene una conexión del pool o crea una nueva si es necesario"""
        try:
            # Intentar obtener una conexión existente del pool
            connection = self._pool.get_nowait()
            self._stats["connections_reused"] += 1
            logger.debug("Conexión reutilizada del pool")
            return connection

        except Empty:
            # No hay conexiones disponibles en el pool
            with self._lock:
                if self._created_connections < self.max_connections:
                    # Crear nueva conexión
                    return self._create_connection()
                else:
                    # Esperar por una conexión disponible
                    logger.debug(
                        f"Pool lleno, esperando conexión disponible (timeout: {self.timeout}s)"
                    )
                    try:
                        connection = self._pool.get(timeout=self.timeout)
                        self._stats["connections_reused"] += 1
                        return connection
                    except Empty:
                        raise TimeoutError(
                            f"Timeout esperando conexión después de {self.timeout}s"
                        )

    def _return_connection(self, connection):
        """Devuelve una conexión al pool"""
        try:
            # Verificar que la conexión sigue siendo válida
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            cursor.close()

            # Devolver al pool
            self._pool.put_nowait(connection)
            logger.debug("Conexión devuelta al pool")

        except Exception as e:
            logger.warning(f"Conexión inválida descartada: {e}")
            # Remover de la lista de conexiones
            with self._lock:
                if connection in self._all_connections:
                    self._all_connections.remove(connection)
                    self._created_connections -= 1
                try:
                    connection.close()
                except Exception:
                    pass

    @contextmanager
    def get_connection(self):
        """
        Context manager para obtener una conexión de forma segura.

        Usage:
            with pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM tabla")
                results = cursor.fetchall()
        """
        connection = None
        try:
            # Actualizar estadísticas de concurrencia
            with self._lock:
                self._stats["concurrent_operations"] += 1
                if self._stats["concurrent_operations"] > self._stats["max_concurrent"]:
                    self._stats["max_concurrent"] = self._stats["concurrent_operations"]

            connection = self._get_connection()
            logger.debug(
                f"Conexión obtenida - Operaciones concurrentes: {self._stats['concurrent_operations']}"
            )

            yield connection

            # Commit automático si no hubo errores
            connection.commit()
            self._stats["operations_completed"] += 1

        except Exception as e:
            # Rollback en caso de error
            if connection:
                try:
                    connection.rollback()
                except Exception:
                    pass

            self._stats["operations_failed"] += 1
            logger.error(f"Error en operación de base de datos: {e}")
            raise

        finally:
            # Devolver conexión al pool y actualizar estadísticas
            if connection:
                self._return_connection(connection)

            with self._lock:
                self._stats["concurrent_operations"] -= 1

    def execute_query(
        self, query: str, params: Optional[tuple] = None
    ) -> list[dict[str, Any]]:
        """Ejecuta una consulta SELECT de forma thread-safe"""
        with self.get_connection() as connection:
            cursor = connection.cursor()

            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            # Convertir resultados a lista de diccionarios
            columns = [column[0] for column in cursor.description]
            result = [dict(zip(columns, row)) for row in cursor.fetchall()]

            logger.debug(f"Consulta ejecutada: {len(result)} filas retornadas")
            return result

    def execute_non_query(self, query: str, params: Optional[tuple] = None) -> int:
        """Ejecuta una consulta INSERT, UPDATE o DELETE de forma thread-safe"""
        with self.get_connection() as connection:
            cursor = connection.cursor()

            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            rows_affected = cursor.rowcount
            logger.debug(f"Consulta ejecutada: {rows_affected} filas afectadas")
            return rows_affected

    def insert_record(self, table: str, data: dict[str, Any]) -> bool:
        """Inserta un registro usando el pool (thread-safe)."""
        try:
            fields = list(data.keys())
            placeholders = ", ".join(["?"] * len(fields))
            columns = ", ".join(fields)
            query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
            values = tuple(data.values())
            rows = self.execute_non_query(query, values)
            return rows > 0
        except Exception as e:  # pragma: no cover - defensivo
            logger.error(f"Error insert_record pool {table}: {e}")
            return False

    def get_max_id(self, table: str, id_field: str) -> int:
        """Obtiene MAX(id_field) de forma thread-safe usando el pool."""
        try:
            query = f"SELECT MAX({id_field}) as MaxID FROM {table}"
            rows = self.execute_query(query)
            if rows and rows[0].get("MaxID") is not None:
                return rows[0]["MaxID"]
            return 0
        except Exception as e:  # pragma: no cover
            logger.error(f"Error get_max_id pool {table}.{id_field}: {e}")
            return 0

    def update_record(
        self,
        table: str,
        data: dict[str, Any],
        where_condition: str,
        where_params: Optional[list] = None,
    ) -> bool:
        """Actualiza registros de forma thread-safe con lock adicional para operaciones críticas"""
        # Lock adicional para operaciones de escritura críticas
        with self._lock:
            try:
                set_clauses = [f"{field} = ?" for field in data.keys()]
                values = list(data.values())

                query = f"UPDATE {table} SET {', '.join(set_clauses)} WHERE {where_condition}"

                params = tuple(values)
                if where_params:
                    params = params + tuple(where_params)

                rows_affected = self.execute_non_query(query, params)
                logger.info(
                    f"Actualizado {rows_affected} registros en {table} (Thread-safe)"
                )
                return rows_affected > 0

            except Exception as e:
                logger.error(f"Error actualizando registro en {table}: {e}")
                return False

    def get_stats(self) -> dict[str, Any]:
        """Obtiene estadísticas del pool de conexiones"""
        with self._lock:
            return {
                **self._stats,
                "pool_size": self._pool.qsize(),
                "total_connections": self._created_connections,
                "max_connections": self.max_connections,
            }

    def close_all(self):
        """Cierra todas las conexiones del pool"""
        with self._lock:
            logger.info("Cerrando todas las conexiones del pool")

            # Cerrar conexiones en el pool
            while not self._pool.empty():
                try:
                    connection = self._pool.get_nowait()
                    connection.close()
                except Exception:
                    pass

            # Cerrar conexiones restantes
            for connection in self._all_connections:
                try:
                    connection.close()
                except Exception:
                    pass

            self._all_connections.clear()
            self._created_connections = 0

            logger.info("Todas las conexiones cerradas")


# Instancias globales de pools por tipo de BD
_tareas_pool: Optional[AccessConnectionPool] = None
_brass_pool: Optional[AccessConnectionPool] = None
_expedientes_pool: Optional[AccessConnectionPool] = None
_agedys_pool: Optional[AccessConnectionPool] = None
_nc_pool: Optional[AccessConnectionPool] = None
_riesgos_pool: Optional[AccessConnectionPool] = None
_correos_pool: Optional[AccessConnectionPool] = None
_pool_lock = threading.Lock()


def get_tareas_connection_pool(connection_string: str = None) -> AccessConnectionPool:
    """
    Obtiene o crea el pool de conexiones global para la base de datos de tareas.

    Args:
        connection_string: Cadena de conexión (solo necesaria en la primera llamada)

    Returns:
        Instancia del pool de conexiones
    """
    global _tareas_pool

    with _pool_lock:
        if _tareas_pool is None:
            if connection_string is None:
                raise ValueError(
                    "connection_string es requerido para inicializar el pool"
                )

            _tareas_pool = AccessConnectionPool(
                connection_string=connection_string,
                max_connections=2,  # Máximo 2 conexiones concurrentes para Access
                timeout=30,
            )
            logger.info("Pool de conexiones de tareas inicializado")

        return _tareas_pool


def close_tareas_pool():
    """Cierra el pool de conexiones global de tareas"""
    global _tareas_pool

    with _pool_lock:
        if _tareas_pool:
            _tareas_pool.close_all()
            _tareas_pool = None
            logger.info("Pool de conexiones de tareas cerrado")


# ------------------------- Generic helpers por BD -------------------------
def _get_pool(
    existing_ref: Optional[AccessConnectionPool],
    set_attr_name: str,
    connection_string: str,
    max_conn: int = 2,
) -> AccessConnectionPool:
    global _tareas_pool, _brass_pool, _expedientes_pool, _agedys_pool, _nc_pool, _riesgos_pool, _correos_pool
    with _pool_lock:
        if existing_ref is None:
            pool = AccessConnectionPool(
                connection_string=connection_string,
                max_connections=max_conn,
                timeout=30,
            )
            # asignar en el diccionario global correctamente
            globals()[set_attr_name] = pool
            logger.info(f"Pool de conexiones {set_attr_name} inicializado")
            return pool
        return existing_ref


def get_brass_connection_pool(connection_string: str) -> AccessConnectionPool:
    return _get_pool(_brass_pool, "_brass_pool", connection_string)


def get_expedientes_connection_pool(connection_string: str) -> AccessConnectionPool:
    return _get_pool(_expedientes_pool, "_expedientes_pool", connection_string)


def get_agedys_connection_pool(connection_string: str) -> AccessConnectionPool:
    return _get_pool(_agedys_pool, "_agedys_pool", connection_string)


def get_nc_connection_pool(connection_string: str) -> AccessConnectionPool:
    return _get_pool(_nc_pool, "_nc_pool", connection_string)


def get_riesgos_connection_pool(connection_string: str) -> AccessConnectionPool:
    return _get_pool(_riesgos_pool, "_riesgos_pool", connection_string)


def get_correos_connection_pool(connection_string: str) -> AccessConnectionPool:
    return _get_pool(_correos_pool, "_correos_pool", connection_string)
