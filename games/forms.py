from django import forms

from .models import Watchlist


class GameSearchForm(forms.Form):
    query = forms.CharField(
        label='Название игры',
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Например: Hades'}),
    )


class AddGameForm(forms.Form):
    itad_id = forms.CharField(max_length=64, widget=forms.HiddenInput)
    title = forms.CharField(max_length=200, widget=forms.HiddenInput)
    slug = forms.SlugField(max_length=220, required=False, widget=forms.HiddenInput)

    def clean_itad_id(self):
        return self.cleaned_data['itad_id'].strip()

    def clean_title(self):
        return self.cleaned_data['title'].strip()


class WatchlistForm(forms.ModelForm):
    class Meta:
        model = Watchlist
        fields = ['target_price']
        widgets = {
            'target_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'placeholder': 'Целевая цена',
            }),
        }

    def __init__(self, *args, user=None, game=None, **kwargs):
        self.user = user
        self.game = game
        super().__init__(*args, **kwargs)

    def clean_target_price(self):
        price = self.cleaned_data['target_price']
        if price <= 0:
            raise forms.ValidationError('Целевая цена должна быть больше нуля.')
        return price

    def clean(self):
        cleaned_data = super().clean()
        if self.user and self.game and Watchlist.objects.filter(user=self.user, game=self.game).exists():
            raise forms.ValidationError('Эта игра уже в списке отслеживания.')
        return cleaned_data

    def save(self, commit=True):
        self.instance.user = self.user
        self.instance.game = self.game
        return super().save(commit=commit)
