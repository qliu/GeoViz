"""
WSGI config for geoviz project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/howto/deployment/wsgi/
"""

import os, sys
sys.path.append('/django-apps/geoviz/geoviz/')
os.environ.setdefault("PYTHON_EGG_CACHE", "/django-apps/geoviz/geoviz/egg_cache")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "geoviz.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
