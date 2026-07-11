from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def create_albums_for_existing_images(apps, schema_editor):
    Album = apps.get_model('images', 'Album')
    AlbumImage = apps.get_model('images', 'AlbumImage')
    for image in AlbumImage.objects.filter(album__isnull=True).order_by('created', 'id'):
        album = Album.objects.create(
            title=image.title,
            description=image.description,
            uploaded_by=image.uploaded_by,
            created=image.created,
            updated=image.updated,
        )
        image.album = album
        image.save(update_fields=['album'])


class Migration(migrations.Migration):

    dependencies = [
        ('images', '0003_albumimage'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Album',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('uploaded_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='albums', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-created']},
        ),
        migrations.AddField(
            model_name='albumimage',
            name='album',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='images', to='images.album'),
        ),
        migrations.AddIndex(
            model_name='album',
            index=models.Index(fields=['created'], name='images_albu_created_8f0a4d_idx'),
        ),
        migrations.RunPython(create_albums_for_existing_images, migrations.RunPython.noop),
    ]
