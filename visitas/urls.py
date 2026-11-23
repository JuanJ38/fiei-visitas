from django.urls import path

from visitas import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("registrar/", views.registrar, name="registrar"),
    path("historial/", views.historial, name="historial"),
    path("afluencia/", views.afluencia, name="afluencia"),
    path("modelo/", views.modelo, name="modelo"),
]
