from django.contrib.auth.decorators import login_required
from django.shortcuts import render


def home(request):
    return render(request, 'core/home.html')


@login_required
def app_home(request):
    contexto = {
        'empresa': request.user.empresa,
        'puede_ver_clientes': request.user.has_permission('clientes.ver'),
        'puede_ver_productos': request.user.has_permission('productos.ver'),
    }
    return render(request, 'core/app.html', contexto)
