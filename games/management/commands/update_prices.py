import time
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from games.itad_client import ITADClient, ITADError
from games.models import Game, PriceSnapshot, Store, Watchlist

BATCH_SIZE = 20


class Command(BaseCommand):
    help = 'Fetch current prices and historical lows from ITAD, store snapshots, update watchlist flags (UC-3)'

    def handle(self, *args, **options):
        try:
            client = ITADClient()
        except ITADError as exc:
            raise CommandError(str(exc))

        games = list(Game.objects.all())
        if not games:
            self.stdout.write(self.style.WARNING('No games in catalog. Run seed_catalog first.'))
            return

        stores_by_itad_id = {s.itad_store_id: s for s in Store.objects.all()}
        games_by_itad_id = {g.itad_id: g for g in games}

        for batch_start in range(0, len(games), BATCH_SIZE):
            batch = games[batch_start:batch_start + BATCH_SIZE]
            ids = [g.itad_id for g in batch]

            prices = client.get_prices(ids)

            now = timezone.now()
            for entry in prices:
                game = games_by_itad_id.get(entry['id'])
                if game is None:
                    continue
                for deal in entry.get('deals', []):
                    store = stores_by_itad_id.get(str(deal['shop']['id']))
                    if store is None:
                        continue
                    PriceSnapshot.objects.create(
                        game=game,
                        store=store,
                        price=Decimal(str(deal['price']['amount'])),
                        regular_price=Decimal(str(deal['regular']['amount'])),
                        cut=deal.get('cut', 0),
                        recorded_at=now,
                    )

                history_low = entry.get('historyLow', {}).get('all', {}).get('amount')
                if history_low is not None:
                    game.historical_low = Decimal(str(history_low))
                    game.save(update_fields=['historical_low'])

            self.stdout.write(f'Updated {len(batch)} games ({batch_start + len(batch)}/{len(games)})')
            time.sleep(1)

        self._update_watchlist_notifications()
        self.stdout.write(self.style.SUCCESS('Price update complete.'))

    def _update_watchlist_notifications(self):
        for entry in Watchlist.objects.select_related('game'):
            latest = PriceSnapshot.objects.filter(game=entry.game).order_by('-recorded_at').first()
            if latest is None:
                continue
            best_price = (
                PriceSnapshot.objects.filter(game=entry.game, recorded_at=latest.recorded_at)
                .order_by('price')
                .values_list('price', flat=True)
                .first()
            )
            should_notify = best_price is not None and best_price <= entry.target_price
            if should_notify != entry.is_notified:
                entry.is_notified = should_notify
                entry.save(update_fields=['is_notified'])
