from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0003_profile_last_avatar_change"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="last_token_generated_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
