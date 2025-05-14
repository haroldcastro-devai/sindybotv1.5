# settings_aws.py
from .settings import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'sindybot_dev',
        'USER': 'dev_user',
        'PASSWORD': 'DevPassword123!',
        'HOST': '34.229.113.3',
        'PORT': '3306',
    }
}