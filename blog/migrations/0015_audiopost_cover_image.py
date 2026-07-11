from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("blog", "0014_comment_author_fk"),
    ]

    operations = [
        migrations.AddField(
            model_name="audiopost",
            name="cover_image",
            field=models.ImageField(blank=True, null=True, upload_to="audio/covers/%Y/%m/%d"),
        ),
    ]
