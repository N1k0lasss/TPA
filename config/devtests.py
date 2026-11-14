"""Endpoint temporal para ejecutar la suite de pruebas sin acceso a shell."""

import io
import sys
import traceback
import unittest

from django.conf import settings
from django.core.management import call_command
from django.http import JsonResponse


def ejecutar_tests(request):
    if not settings.DEBUG:
        return JsonResponse({"error": "solo disponible en DEBUG"}, status=404)

    salida, errores = io.StringIO(), io.StringIO()
    codigo = 0
    # unittest intenta instalar un handler de SIGINT, imposible fuera del hilo principal.
    instalar, quitar = unittest.installHandler, unittest.removeHandler
    unittest.installHandler = lambda: None
    unittest.removeHandler = lambda: None
    try:
        with contextlib_redirect(salida, errores):
            call_command("test", verbosity=1, interactive=False)
    except SystemExit as exc:
        codigo = exc.code if isinstance(exc.code, int) else 1
    except Exception:
        codigo = 1
        errores.write(traceback.format_exc())
    finally:
        unittest.installHandler = instalar
        unittest.removeHandler = quitar

    return JsonResponse(
        {
            "exit_code": codigo,
            "stdout": salida.getvalue()[-30000:],
            "stderr": errores.getvalue()[-10000:],
        }
    )


class contextlib_redirect:
    """Redirige stdout/stderr durante la ejecución."""

    def __init__(self, stdout, stderr):
        self.stdout = stdout
        self.stderr = stderr
        self._original = None

    def __enter__(self):
        self._original = (sys.stdout, sys.stderr)
        sys.stdout, sys.stderr = self.stdout, self.stderr
        return self

    def __exit__(self, *args):
        sys.stdout, sys.stderr = self._original
        return False
