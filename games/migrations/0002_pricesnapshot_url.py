from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='pricesnapshot',
            name='url',
            field=models.URLField(blank=True, max_length=500),
        ),
    ]
