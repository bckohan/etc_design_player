import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'etc_player.settings')
os.environ.setdefault('PLAYER_DIR', '/var/www/player')

application = get_wsgi_application()
