# src/infrastructure/shared/pysus_compat.py
"""
Correção do pysus 1.x no Windows.

O módulo pysus.ftp monta os caminhos do FTP com os.path. No Windows,
os.path.normpath("/") retorna "\\", então a checagem da raiz nunca é
satisfeita e Directory(...) entra em recursão infinita já no `import pysus`.

Caminhos de FTP são sempre POSIX, então fazemos o pysus.ftp enxergar
posixpath no lugar de ntpath. Deve ser aplicado antes de qualquer import do pysus.
"""
import importlib.abc
import importlib.util
import os
import posixpath
import sys
import types

_TARGET_MODULE = "pysus.ftp"


def _posix_os_module() -> types.ModuleType:
    shim = types.ModuleType("os")
    shim.__dict__.update(os.__dict__)
    shim.path = posixpath
    return shim


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
            module.os = _posix_os_module()

        spec.loader.exec_module = exec_module
        return spec


def apply_pysus_windows_patch() -> None:
    if os.name != "nt" or _TARGET_MODULE in sys.modules:
        return
    if any(isinstance(finder, _PysusFtpPatchFinder) for finder in sys.meta_path):
        return
    sys.meta_path.insert(0, _PysusFtpPatchFinder())
