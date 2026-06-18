from django.core.management.base import BaseCommand, CommandError

from games.currency import usd_to_rub
from games.itad_client import ITADClient, ITADError
from games.models import Game, PriceSnapshot, Watchlist
from games.services import sync_prices_for_games


class Command(BaseCommand):
    help = 'Загружает текущие цены и исторический минимум из ITAD, создаёт снимки цен, обновляет флаги в watchlist (UC-3)'

    def handle(self, *args, **options):
        try:
            client = ITADClient()
        except ITADError as exc:
            raise CommandError(str(exc))

        games = list(Game.objects.all())
        if not games:
            self.stdout.write(self.style.WARNING('В каталоге нет игр. Сначала запустите seed_catalog.'))
            return

        created = sync_prices_for_games(client, games)
        self.stdout.write(f'Создано снимков цен: {created} (игр: {len(games)})')

        self._update_watchlist_notifications()
        self.stdout.write(self.style.SUCCESS('Обновление цен завершено.'))

    def _update_watchlist_notifications(self):
        for entry in Watchlist.objects.select_related('game'):
            latest = PriceSnapshot.objects.filter(game=entry.game).order_by('-recorded_at').first()
            if latest is None:
                continue
            best_price_usd = (
                PriceSnapshot.objects.filter(game=entry.game, recorded_at=latest.recorded_at)
                .order_by('price')
                .values_list('price', flat=True)
                .first()
            )
            best_price_rub = usd_to_rub(best_price_usd) if best_price_usd is not None else None
            should_notify = best_price_rub is not None and best_price_rub <= entry.target_price
            if should_notify != entry.is_notified:
                entry.is_notified = should_notify
                entry.save(update_fields=['is_notified'])
