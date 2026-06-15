from django.contrib import admin

from .models import Game, PriceSnapshot, Store, Watchlist


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'itad_store_id']
    search_fields = ['name', 'slug']


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'steam_appid', 'historical_low', 'created_at']
    search_fields = ['title', 'itad_id']
    list_filter = ['created_at']


@admin.register(PriceSnapshot)
class PriceSnapshotAdmin(admin.ModelAdmin):
    list_display = ['game', 'store', 'price', 'regular_price', 'cut', 'recorded_at']
    search_fields = ['game__title', 'store__name']
    list_filter = ['store', 'recorded_at']


@admin.register(Watchlist)
class WatchlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'game', 'target_price', 'is_notified', 'created_at']
    search_fields = ['user__username', 'game__title']
    list_filter = ['is_notified']
