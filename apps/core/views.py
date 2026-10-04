from django.contrib.auth.decorators import login_required
from django.shortcuts import render


def home(request):
    return render(request, 'core/home.html')


@login_required
def app_home(request):
    return render(request, 'core/app.html', {'empresa': request.user.empresa})
