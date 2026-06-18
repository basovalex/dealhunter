"""Pandas-based Deal Score calculation and Plotly chart building (TZ.md section 6)."""
import pandas as pd
import plotly.express as px
from django.db.models import Avg, Count, Min

from .models import Game, PriceSnapshot


def _snapshots_dataframe(game):
    rows = list(game.snapshots.select_related('store').values('price', 'recorded_at', 'store__name'))
    if not rows:
        return pd.DataFrame(columns=['price', 'recorded_at', 'store'])
    df = pd.DataFrame.from_records(rows).rename(columns={'store__name': 'store'})
    df['recorded_at'] = pd.to_datetime(df['recorded_at'])
    df['price'] = df['price'].astype(float)
    return df


def latest_snapshots(game):
    """Snapshots from the most recent recorded_at batch for a game (the "current" prices)."""
    latest_ts = game.snapshots.order_by('-recorded_at').values_list('recorded_at', flat=True).first()
    if latest_ts is None:
        return game.snapshots.none()
    return game.snapshots.filter(recorded_at=latest_ts).select_related('store')


def best_current_price(game):
    return latest_snapshots(game).order_by('price').first()


def compute_deal_score(game):
    """score = clamp(0, 100, round((year_avg - current) / (year_avg - hist_low) * 100))"""
    df = _snapshots_dataframe(game)
    if df.empty:
        return None

    hist_low = float(game.historical_low) if game.historical_low is not None else df['price'].min()
    one_year_ago = df['recorded_at'].max() - pd.Timedelta(days=365)
    year_avg = df.loc[df['recorded_at'] >= one_year_ago, 'price'].mean()
    if pd.isna(year_avg):
        year_avg = df['price'].mean()

    latest_ts = df['recorded_at'].max()
    current = df.loc[df['recorded_at'] == latest_ts, 'price'].min()

    if year_avg == hist_low:
        score = 100 if current <= hist_low else 0
    else:
        score = round((year_avg - current) / (year_avg - hist_low) * 100)
    return max(0, min(100, int(score)))


def score_label(score):
    if score is None:
        return 'нет данных'
    if score >= 80:
        return 'отличная цена'
    if score >= 50:
        return 'хорошая цена'
    if score >= 20:
        return 'средняя цена'
    return 'бывало дешевле'


def store_aggregates():
    """Average/min price and number of distinct games tracked per store, for the catalog overview."""
    return (
        PriceSnapshot.objects.values('store__name')
        .annotate(avg_price=Avg('price'), min_price=Min('price'), games_count=Count('game', distinct=True))
        .order_by('store__name')
    )


def top_deals(limit=10):
    """Best current Deal Score across the whole catalog."""
    scored = [(game, score) for game in Game.objects.all() if (score := compute_deal_score(game)) is not None]
    scored.sort(key=lambda pair: pair[1], reverse=True)
    return scored[:limit]


def price_history_chart(game):
    """Возвращает HTML-фрагмент с графиком, либо None, если снимков цен ещё нет."""
    df = _snapshots_dataframe(game)
    if df.empty:
        return None
    df = df.sort_values('recorded_at')

    if df['recorded_at'].nunique() <= 1:
        # Собран только один снимок цен — линия по одной точке выглядит как сломанный график,
        # поэтому показываем точки и расширяем ось X, чтобы её было видно.
        fig = px.scatter(
            df, x='recorded_at', y='price', color='store',
            labels={'recorded_at': 'Дата', 'price': 'Цена ($)', 'store': 'Магазин'},
            title=f'История цен: {game.title} (накоплен только один снимок)',
        )
        point = df['recorded_at'].iloc[0]
        fig.update_xaxes(range=[point - pd.Timedelta(days=1), point + pd.Timedelta(days=1)])
    else:
        fig = px.line(
            df, x='recorded_at', y='price', color='store', markers=True,
            labels={'recorded_at': 'Дата', 'price': 'Цена ($)', 'store': 'Магазин'},
            title=f'История цен: {game.title}',
        )
    fig.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=400)
    return fig.to_html(full_html=False, include_plotlyjs='cdn')
