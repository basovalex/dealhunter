import time

from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

from games.constants import TRUSTED_STORE_NAMES
from games.itad_client import ITADClient, ITADError
from games.models import Game, Store

# Fixed list of well-known titles used to populate a demo catalog (UC: admin fills the catalog).
DEMO_TITLES = [
    "The Witcher 3: Wild Hunt",
    "Cyberpunk 2077",
    "Stardew Valley",
    "Hades",
    "Hollow Knight",
    "Disco Elysium - The Final Cut",
    "Baldur's Gate 3",
    "Elden Ring",
    "Portal 2",
    "Celeste",
    "Dark Souls III",
    "Terraria",
    "Outer Wilds",
    "Slay the Spire",
    "Subnautica",
    "HITMAN World of Assassination",
    "Divinity: Original Sin 2 - Definitive Edition",
    "Sekiro: Shadows Die Twice - GOTY Edition",
    # Дополнительные игры — расширяем каталог тем, на что у ITAD есть реальные цены.
    "Grand Theft Auto V",
    "Red Dead Redemption 2",
    "It Takes Two",
    "Resident Evil 4 (2023)",
    "Persona 5 Royal",
    "DEATH STRANDING DIRECTOR'S CUT",
    "Cult of the Lamb",
    "Vampire Survivors",
]


class Command(BaseCommand):
    help = 'Наполняет каталог магазинами и играми из IsThereAnyDeal (демо-данные)'

    def handle(self, *args, **options):
        try:
            client = ITADClient()
        except ITADError as exc:
            raise CommandError(str(exc))

        shops = [shop for shop in client.get_shops() if (shop.get('title') or shop.get('name')) in TRUSTED_STORE_NAMES]
        created_stores = 0
        for shop in shops:
            shop_id = str(shop.get('id'))
            name = shop.get('title') or shop.get('name') or shop_id
            _, created = Store.objects.update_or_create(
                itad_store_id=shop_id,
                defaults={'name': name, 'slug': slugify(name)},
            )
            created_stores += int(created)
        self.stdout.write(self.style.SUCCESS(f'Магазины: {created_stores} создано, {len(shops)} официальных магазинов найдено'))

        created_games = 0
        for title in DEMO_TITLES:
            result = client.lookup_game(title=title)
            if not result.get('found'):
                self.stdout.write(self.style.WARNING(f'Не найдено в ITAD: {title}'))
                continue
            game_info = result['game']
            _, created = Game.objects.update_or_create(
                itad_id=game_info['id'],
                defaults={
                    'title': game_info.get('title', title),
                    'slug': slugify(game_info.get('slug') or game_info.get('title', title)),
                },
            )
            created_games += int(created)
            time.sleep(0.5)

        self.stdout.write(self.style.SUCCESS(f'Игры: {created_games} создано из {len(DEMO_TITLES)} названий'))
