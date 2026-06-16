from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import DetailView, ListView

from . import analytics
from .forms import WatchlistForm
from .models import Game, Store, Watchlist


class CatalogListView(ListView):
    model = Game
    template_name = 'games/catalog_list.html'
    context_object_name = 'rows'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset().prefetch_related('snapshots__store')
        store_slug = self.request.GET.get('store')
        if store_slug:
            qs = qs.filter(snapshots__store__slug=store_slug)
        games = list(qs.distinct())

        rows = []
        for game in games:
            rows.append({
                'game': game,
                'snapshot': analytics.best_current_price(game),
                'score': analytics.compute_deal_score(game),
            })

        sort = self.request.GET.get('sort')
        if sort == 'cut':
            rows.sort(key=lambda row: row['snapshot'].cut if row['snapshot'] else -1, reverse=True)
        elif sort == 'score':
            rows.sort(key=lambda row: row['score'] if row['score'] is not None else -1, reverse=True)
        return rows

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stores'] = Store.objects.all()
        context['selected_store'] = self.request.GET.get('store', '')
        context['sort'] = self.request.GET.get('sort', '')
        context['store_aggregates'] = analytics.store_aggregates()
        context['top_deals'] = analytics.top_deals(5)
        return context


class GameDetailView(DetailView):
    model = Game
    template_name = 'games/game_detail.html'
    context_object_name = 'game'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        game = self.object
        context['latest_snapshots'] = analytics.latest_snapshots(game)
        context['score'] = analytics.compute_deal_score(game)
        context['score_label'] = analytics.score_label(context['score'])
        context['chart'] = analytics.price_history_chart(game)
        if self.request.user.is_authenticated:
            context['already_watching'] = Watchlist.objects.filter(user=self.request.user, game=game).exists()
            context['watchlist_form'] = WatchlistForm()
        return context


class WatchlistAddView(LoginRequiredMixin, View):
    def post(self, request, slug):
        game = get_object_or_404(Game, slug=slug)
        form = WatchlistForm(request.POST, user=request.user, game=game)
        if form.is_valid():
            form.save()
            messages.success(request, f'«{game.title}» добавлена в список отслеживания.')
        else:
            for errors in form.errors.values():
                for error in errors:
                    messages.error(request, error)
        return redirect('game_detail', slug=slug)


class ProfileView(LoginRequiredMixin, ListView):
    template_name = 'games/profile.html'
    context_object_name = 'rows'

    def get_queryset(self):
        entries = Watchlist.objects.filter(user=self.request.user).select_related('game')
        return [{'entry': entry, 'snapshot': analytics.best_current_price(entry.game)} for entry in entries]
