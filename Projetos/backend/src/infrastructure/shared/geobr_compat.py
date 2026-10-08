# src/infrastructure/shared/geobr_compat.py
"""
Correção de concorrência do geobr 2.x.

O geobr lê as geometrias por uma única conexão DuckDB global (_duckdb_backend.duckdb_connection),
sem trava. A API roda as rotas em threads, então dois mapas gerados ao mesmo tempo usam a mesma
conexão e um corrompe o outro ("Current transaction is aborted (please ROLLBACK)", "The object was
created by another Connection"). Pior: a conexão fica no estado abortado e TODAS as buscas seguintes
falham até reiniciar a API.

As funções geobr.read_* passam a ser serializadas por um lock. Se ainda assim ocorrer erro do DuckDB,
a conexão global é descartada (o geobr cria outra na próxima chamada) e a leitura é repetida.
"""
import functools
import threading

import duckdb
import geobr
from geobr import _duckdb_backend

_GEOBR_LOCK = threading.RLock()
_MAX_ATTEMPTS = 2
_PATCHED_FLAG = "_geobr_compat_patched"


def _with_lock_and_reconnect(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        with _GEOBR_LOCK:
            for attempt in range(1, _MAX_ATTEMPTS + 1):
                try:
                    return func(*args, **kwargs)
                except duckdb.Error as e:
                    if attempt == _MAX_ATTEMPTS:
                        raise
                    print(f" -> [geobr] Erro na conexão DuckDB ({e}); recriando a conexão e tentando de novo...")
                    _duckdb_backend._reset_shared_connection()
    setattr(wrapper, _PATCHED_FLAG, True)
    return wrapper


def apply_geobr_patches() -> None:
    for name in dir(geobr):
        func = getattr(geobr, name)
        if name.startswith("read_") and callable(func) and not getattr(func, _PATCHED_FLAG, False):
            setattr(geobr, name, _with_lock_and_reconnect(func))
