from django.urls import path

from . import views

urlpatterns = [
    path('', views.CatalogListView.as_view(), name='catalog'),
    path('game/<slug:slug>/', views.GameDetailView.as_view(), name='game_detail'),
]
