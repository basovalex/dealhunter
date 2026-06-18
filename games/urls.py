from django.urls import path

from . import views

urlpatterns = [
    path('', views.CatalogListView.as_view(), name='catalog'),
    path('game/<slug:slug>/', views.GameDetailView.as_view(), name='game_detail'),
    path('game/<slug:slug>/watch/', views.WatchlistAddView.as_view(), name='watchlist_add'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('add-game/', views.AddGameView.as_view(), name='add_game'),
]
