from django.shortcuts import render

# Create your views here.
from django.shortcuts import render

def home(request):
    # Nota que incluimos 'core/' en la ruta del template
    return render(request, 'core/home.html')