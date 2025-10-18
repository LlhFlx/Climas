"""
URL configuration for climas project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('calls/', include('calls.urls')),
    path('proposals/', include('proposals.urls', namespace='proposals')),
    path('evaluations/', include('evaluations.urls', namespace='evaluations')),
    path('proponent_forms/', include('proponent_forms.urls', namespace='proponent_forms')),
    path('', RedirectView.as_view(pattern_name='accounts:login', permanent=False), name='home'),
    path('captcha/', include('captcha.urls')),

    #path('institutions/', include('institutions.urls'))
    #path('screening/', include('screening.urls'))
]
