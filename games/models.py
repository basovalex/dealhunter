from django.conf import settings
from django.db import models
from django.urls import reverse


class Store(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    itad_store_id = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Game(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    itad_id = models.CharField(max_length=64, unique=True)
    steam_appid = models.IntegerField(null=True, blank=True)
    historical_low = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('game_detail', kwargs={'slug': self.slug})


class PriceSnapshot(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='snapshots')
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='snapshots')
    price = models.DecimalField(max_digits=8, decimal_places=2)
    regular_price = models.DecimalField(max_digits=8, decimal_places=2)
    cut = models.IntegerField()
    recorded_at = models.DateTimeField()
    url = models.URLField(max_length=500, blank=True)

    class Meta:
        ordering = ['-recorded_at']
        indexes = [models.Index(fields=['game', 'store', 'recorded_at'])]

    def __str__(self):
        return f'{self.game.title} @ {self.store.name}: {self.price}'


class Watchlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='watchlist')
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='watchers')
    target_price = models.DecimalField(max_digits=8, decimal_places=2)
    is_notified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['user', 'game'], name='unique_watchlist_entry'),
        ]

    def __str__(self):
        return f'{self.user.username} -> {self.game.title} ({self.target_price})'
