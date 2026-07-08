"""
WSGI config for my_site project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "my_site.settings.prod")

application = get_wsgi_application()
