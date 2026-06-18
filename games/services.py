"""Общая логика синхронизации цен с ITAD."""
import time
from decimal import Decimal

from django.utils import timezone

from .models import PriceSnapshot, Store

BATCH_SIZE = 20


def sync_prices_for_games(client, games):
    """Создаёт PriceSnapshot и обновляет Game.historical_low."""
    stores_by_itad_id = {s.itad_store_id: s for s in Store.objects.all()}
    game_list = list(games)
    games_by_itad_id = {g.itad_id: g for g in game_list}
    created = 0

    for batch_start in range(0, len(game_list), BATCH_SIZE):
        batch = game_list[batch_start:batch_start + BATCH_SIZE]
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
                    url=deal.get('url', ''),
                )
                created += 1

            history_low = entry.get('historyLow', {}).get('all', {}).get('amount')
            if history_low is not None:
                game.historical_low = Decimal(str(history_low))
                game.save(update_fields=['historical_low'])

        if batch_start + BATCH_SIZE < len(game_list):
            time.sleep(1)

    return created
