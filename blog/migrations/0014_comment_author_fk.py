from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def populate_comment_authors(apps, schema_editor):
    Comment = apps.get_model("blog", "Comment")
    User = apps.get_model("auth", "User")

    for comment in Comment.objects.filter(author__isnull=True):
        if not hasattr(comment, "name"):
            continue
        username = (comment.name or "").strip()
        if not username:
            continue
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            continue
        comment.author = user
        comment.save(update_fields=["author"])


class Migration(migrations.Migration):

    dependencies = [
        ("blog", "0013_alter_audiopost_updated_alter_comment_body_auditlog"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="comment",
            name="author",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="blog_comments",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.RunPython(populate_comment_authors, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="comment",
            name="name",
        ),
        migrations.AlterField(
            model_name="comment",
            name="author",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="blog_comments",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
