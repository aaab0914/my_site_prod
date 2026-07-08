# Source Structure

This document summarizes the current Python source layout after the package-based reorganization.

Project root:

```text
G:\Projests\Python_Projects\my_site_prod-master
```

## Main Application Packages

### `blog/`

Core blog application code.

Current layout:

```text
blog/
  admin/
    __init__.py
    actions.py
    posts.py
    comments.py
    audio.py
    audit.py
  api_views/
    __init__.py
    permissions.py
    posts.py
    comments.py
    tags.py
  forms/
    __init__.py
    posts.py
    comments.py
    audio.py
  models/
    __init__.py
    posts.py
    comments.py
    audio.py
    audit.py
  tests/
    test_blog/
      test_tags_and_feeds.py
      test_posts_and_comments.py
      test_audio.py
      test_api.py
      test_admin_and_docker.py
  urls/
    __init__.py
    posts.py
    comments.py
    audio.py
    api.py
    routes.py
  views/
    __init__.py
    common.py
    posts.py
    comments.py
    audio.py
  feeds.py
  serializers.py
  tasks.py
  signals.py
  documents.py
  sitemaps.py
  apps.py
```

Notes:

- `__init__.py` files keep compatibility for imports such as `from blog.models import Post`.
- URLs are grouped by feature, then merged in `blog/urls/routes.py`.

### `users/`

Authentication, profile, and account-management code.

Current layout:

```text
users/
  forms/
    __init__.py
    auth.py
    account.py
  models/
    __init__.py
    profile.py
    activity.py
    preferences.py
    validators.py
  tests/
    test_users/
      test_models.py
      test_auth.py
      test_profile.py
      test_account.py
  urls/
    __init__.py
    auth.py
    profile.py
    account.py
    routes.py
  views/
    __init__.py
    auth.py
    account.py
  admin.py
  apps.py
```

### `images/`

Image-post support code.

Current layout:

```text
images/
  admin/
    __init__.py
    image_posts.py
  forms/
    __init__.py
    image_posts.py
  tests/
    test_images.py
  views/
    __init__.py
    image_posts.py
  models.py
  apps.py
```

## Project Package

### `my_site/`

Project configuration, middleware, metrics, and infrastructure-level tests.

Current layout:

```text
my_site/
  settings/
    __init__.py
    base.py
    dev.py
    prod.py
  tests/
    test_celery_integration.py
    test_docker_compose.py
    test_grafana_integration.py
    test_nginx_config.py
    test_prometheus_integration.py
    test_sentry_integration.py
    test_settings.py
    test_infrastructure/
      common.py
      test_nginx.py
      test_gunicorn.py
      test_postgres.py
      test_monitoring.py
      test_runtime_probes.py
  urls.py
  wsgi.py
  asgi.py
  celery.py
  middleware.py
  audit_middleware.py
  logging_utils.py
  metrics.py
```

## Runtime And Non-Source Directories

These are not primary source-code directories:

- `data/`
- `media/`
- `staticfiles/`
- `logs/`
- `backups/`
- `Shell_Commands/`
- `Others/`

See also:

- `RUNTIME_ARTIFACTS.md`
- `TEST_INDEX.md`
- `DOC_INDEX.md`
