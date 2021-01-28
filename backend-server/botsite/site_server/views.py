from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.

def home(request):
    return render(request, 'home.html')

def about(request):
    return HttpResponse('<h1>Hello About</h1>')

def dashboard(request):
    return HttpResponse('<h1>Hello Dashboard</h1>')

def build(request):
    return HttpResponse('<h1>Hello build</h1>')