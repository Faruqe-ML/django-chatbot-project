from django.contrib import admin
from django.urls import path
from ChatBot import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.homepage, name="homepage"),
    path("chat/", views.chat, name="chat"),
]