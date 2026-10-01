# src/infrastructure/shared/pysus_compat.py
"""
Correções do pysus 1.x aplicadas no momento do import de pysus.ftp.

1. Windows: o módulo monta os caminhos do FTP com os.path. No Windows,
   os.path.normpath("/") retorna "\\", então a checagem da raiz nunca é
   satisfeita e Directory(...) entra em recursão infinita já no `import pysus`.
   Caminhos de FTP são sempre POSIX, então o pysus.ftp passa a enxergar posixpath.

2. Concorrência: listagens e downloads usam uma única conexão FTP compartilhada
   (FTPSingleton), sem trava. Duas requisições simultâneas na API (ex.: variáveis
   do SINAN e do SIM) corrompem a conexão uma da outra ("200 Type set to A.",
   "'NoneType' object has no attribute 'readline'"). As operações passam a ser
   serializadas por um lock e repetidas em caso de erro transitório do FTP.

Deve ser aplicado antes de qualquer import do pysus.
"""
import ftplib
import functools
import importlib.abc
import importlib.util
import os
import posixpath
import sys
import threading
import time
import types

_TARGET_MODULE = "pysus.ftp"
_FTP_LOCK = threading.RLock()
_MAX_ATTEMPTS = 3
_RETRY_DELAY_SECONDS = 1.0
_TRANSIENT_ERRORS = (ftplib.Error, EOFError, OSError, AttributeError)


def _posix_os_module() -> types.ModuleType:
    shim = types.ModuleType("os")
    shim.__dict__.update(os.__dict__)
    shim.path = posixpath
    return shim


def _serialized_with_retry(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        for attempt in range(1, _MAX_ATTEMPTS + 1):
            with _FTP_LOCK:
                try:
                    return func(*args, **kwargs)
                except _TRANSIENT_ERRORS as exc:
                    if attempt == _MAX_ATTEMPTS:
                        raise
                    print(f"[pysus] Erro de FTP ({exc!r}); tentativa {attempt + 1}/{_MAX_ATTEMPTS}...")
            time.sleep(_RETRY_DELAY_SECONDS)
    return wrapper


def _patch_module(module: types.ModuleType) -> None:
    if getattr(module, "_spatial_patched", False):
        return

    if os.name == "nt":
        module.os = _posix_os_module()

    # Directory.load chama load_directory_content pelo nome global do módulo
    module.load_directory_content = _serialized_with_retry(module.load_directory_content)
    module.File.download = _serialized_with_retry(module.File.download)
    module._spatial_patched = True


class _PysusFtpPatchFinder(importlib.abc.MetaPathFinder):

    def find_spec(self, fullname, path, target=None):
        if fullname != _TARGET_MODULE:
            return None

        # Sai do meta_path para deixar os finders padrão localizarem o módulo
        sys.meta_path.remove(self)
        spec = importlib.util.find_spec(fullname)
        if spec is None or spec.loader is None:
            return spec

        original_exec_module = spec.loader.exec_module

        def exec_module(module):
            original_exec_module(module)
            _patch_module(module)

        spec.loader.exec_module = exec_module
        return spec


def apply_pysus_patches() -> None:
    if _TARGET_MODULE in sys.modules:
        # Já importado: só a parte de concorrência ainda pode ser aplicada
        _patch_module(sys.modules[_TARGET_MODULE])
        return
    if any(isinstance(finder, _PysusFtpPatchFinder) for finder in sys.meta_path):
        return
    sys.meta_path.insert(0, _PysusFtpPatchFinder())
