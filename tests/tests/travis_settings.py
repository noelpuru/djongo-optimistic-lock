from __future__ import absolute_import
import os

from tests.settings import *

if os.environ['DB'] == 'sqlite':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': '',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'djongo',
            'NAME': 'test_ool',
            'USER': 'postgres'
        }
    }
