from django.views.generic import DetailView, ListView

from . import analytics
from .models import Game, Store


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
        return context
