
set -e
cd /var/www/my_site_prod_repo_new
python3 - <<'PY'
from pathlib import Path

path = Path('blog/models.py')
text = path.read_text(encoding='utf-8')

if 'from itertools import count' not in text:
    text = text.replace('from django.utils import timezone\n', 'from django.utils import timezone\nfrom itertools import count\n', 1)

old_block = """
    def clean(self):
        if self.pk and self.status == self.Status.PUBLISHED and not self.tags.exists():
            from django.core.exceptions import ValidationError
            raise ValidationError('发布的文章必须包含至少一个标签(tag)。')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        self.clean()
        super().save(*args, **kwargs)
"""

new_block = """
    def build_slug(self):
        base_slug = slugify(self.title)
        if not base_slug:
            timestamp = timezone.localtime(self.publish or timezone.now()).strftime('%Y%m%d%H%M%S')
            base_slug = f'post-{timestamp}'

        base_slug = base_slug[:250]
        publish_date = timezone.localtime(self.publish or timezone.now()).date()
        existing = Post.objects.filter(publish__date=publish_date)
        if self.pk:
            existing = existing.exclude(pk=self.pk)

        for index in count(1):
            suffix = '' if index == 1 else f'-{index}'
            candidate = f'{base_slug[:250 - len(suffix)]}{suffix}'
            if candidate and not existing.filter(slug=candidate).exists():
                return candidate

        raise ValueError('Unable to generate a unique slug for the post.')

    def clean(self):
        if self.pk and self.status == self.Status.PUBLISHED and not self.tags.exists():
            from django.core.exceptions import ValidationError
            raise ValidationError('发布的文章必须包含至少一个标签(tag)。')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.build_slug()
        self.clean()
        super().save(*args, **kwargs)
"""

if 'def build_slug(self):' not in text:
    if old_block not in text:
        raise SystemExit('Expected model block was not found; aborting patch.')
    text = text.replace(old_block, new_block, 1)
    path.write_text(text, encoding='utf-8')
PY
cp blog/models.py blog/models.py.last_applied
python3 -m py_compile blog/models.py
docker compose up -d --build web
sleep 10
docker exec my_site_prod_repo-web-1 python manage.py shell -c "from blog.models import Post; fixed=[]
for post in Post.objects.filter(slug='').order_by('id'):
    post.slug = post.build_slug()
    post.save(update_fields=['slug','updated'])
    fixed.append((post.id, post.slug))
print('fixed_blank_slugs=', fixed)
print('remaining_blank=', Post.objects.filter(slug='').count())"
echo '---HTTP---'
curl -k -I -sS https://rgavanp.kdns.fr/blog/
echo '---BODY---'
curl -k -sS https://rgavanp.kdns.fr/blog/ | head -n 20
