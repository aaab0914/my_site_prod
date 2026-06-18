# my_site/__init__.py
"""
My Site Package
A Django blog project with advanced features.
"""

__version__ = '1.0.0'
__author__ = 'Your Name'
__email__ = 'your@email.com'
__description__ = 'My Blog Project'

# 未来为 Celery 做准备
# from .celery import app as celery_app
# __all__ = ('celery_app',)