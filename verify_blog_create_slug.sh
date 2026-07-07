
set -e
docker exec my_site_prod_repo-web-1 python manage.py shell -c "from django.db import transaction; from django.contrib.auth import get_user_model; from blog.models import Post
User=get_user_model(); user=User.objects.first()
try:
    with transaction.atomic():
        post=Post(title='中文创建验证', body='test', author=user, status=Post.Status.PUBLISHED)
        post.save()
        url=post.get_absolute_url()
        print('created_slug=', post.slug)
        print('created_url=', url)
        raise RuntimeError('rollback verification')
except RuntimeError as exc:
    if str(exc) != 'rollback verification':
        raise
print('rollback_ok=True')"
