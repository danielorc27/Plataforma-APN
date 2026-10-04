from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render

from .models import Empresa


@login_required
def empresa_detalle(request, pk):
    """Muestra el detalle de una empresa.

    El tenant se determina siempre a partir de request.user.empresa;
    el pk de la URL solo se usa para detectar intentos de acceder a
    una empresa distinta a la del usuario autenticado.
    """
    empresa = get_object_or_404(Empresa, pk=pk)
    if request.user.empresa_id != empresa.pk:
        raise PermissionDenied('No tiene acceso a esta empresa.')
    return render(request, 'empresa/detalle.html', {'empresa': empresa})
