from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def permiso_requerido(codigo):
    """Exige autenticación y el permiso dado. Responde 403 si el usuario no lo tiene."""

    def decorador(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped(request, *args, **kwargs):
            if not request.user.has_permission(codigo):
                raise PermissionDenied(f'Requiere el permiso "{codigo}".')
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorador
