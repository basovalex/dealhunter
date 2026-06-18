from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from .analytics import best_current_price, compute_deal_score, latest_snapshots, score_label
from .forms import AddGameForm, WatchlistForm
from .models import Game, PriceSnapshot, Store, Watchlist


class DealAnalyticsTests(TestCase):
    def setUp(self):
        self.store = Store.objects.create(name='Steam', slug='steam', itad_store_id='61')
        self.game = Game.objects.create(
            title='Hades',
            slug='hades',
            itad_id='018d937f-4752-7157-b839-0a54a430a0e5',
            historical_low=Decimal('5.00'),
        )
        old_recorded_at = timezone.now() - timezone.timedelta(days=30)
        current_recorded_at = timezone.now()
        PriceSnapshot.objects.create(
            game=self.game,
            store=self.store,
            price=Decimal('20.00'),
            regular_price=Decimal('25.00'),
            cut=20,
            recorded_at=old_recorded_at,
            url='https://store.steampowered.com/app/1145360/Hades/',
        )
        self.current_snapshot = PriceSnapshot.objects.create(
            game=self.game,
            store=self.store,
            price=Decimal('10.00'),
            regular_price=Decimal('25.00'),
            cut=60,
            recorded_at=current_recorded_at,
            url='https://store.steampowered.com/app/1145360/Hades/',
        )

    def test_best_current_price_uses_latest_snapshot_batch(self):
        self.assertEqual(list(latest_snapshots(self.game)), [self.current_snapshot])
        self.assertEqual(best_current_price(self.game), self.current_snapshot)

    def test_deal_score_uses_current_price_history_and_historical_low(self):
        self.assertEqual(compute_deal_score(self.game), 50)
        self.assertEqual(score_label(50), 'хорошая цена')


class WatchlistFormTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='alex', password='pass12345')
        self.game = Game.objects.create(title='Celeste', slug='celeste', itad_id='celeste-id')

    def test_form_creates_watchlist_entry_for_user_and_game(self):
        form = WatchlistForm(data={'target_price': '399.00'}, user=self.user, game=self.game)

        self.assertTrue(form.is_valid(), form.errors)
        entry = form.save()

        self.assertEqual(entry.user, self.user)
        self.assertEqual(entry.game, self.game)
        self.assertEqual(entry.target_price, Decimal('399.00'))

    def test_form_rejects_duplicate_game_for_same_user(self):
        Watchlist.objects.create(user=self.user, game=self.game, target_price=Decimal('399.00'))
        form = WatchlistForm(data={'target_price': '299.00'}, user=self.user, game=self.game)

        self.assertFalse(form.is_valid())
        self.assertIn('Эта игра уже в списке отслеживания.', form.non_field_errors())


class AddGameFormTests(TestCase):
    def test_add_game_form_validates_hidden_result_payload(self):
        form = AddGameForm(data={
            'itad_id': '018d937f-4752-7157-b839-0a54a430a0e5',
            'title': 'Hades',
            'slug': 'hades',
        })

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['title'], 'Hades')

    def test_add_game_form_requires_external_id_and_title(self):
        form = AddGameForm(data={'itad_id': '', 'title': ''})

        self.assertFalse(form.is_valid())
        self.assertIn('itad_id', form.errors)
        self.assertIn('title', form.errors)
