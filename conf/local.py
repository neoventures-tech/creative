import os
from creative.settings import *

SECURE = True
SITE_ID = None
ADMINS = (
    ('Allan', 'allan.charlys@gmail.com'),
)

CORS_ORIGIN_WHITELIST = [ #URLs específicas autorizadas para comunicação cross-origin.
    'http://localhost:3000',
]

CORS_ALLOWED_ORIGIN_REGEXES = [ #Origens autorizadas com base em padrões (expressões regulares).
    "https://2e811d9ff57d.ngrok-free.app",
    "http://orbi.evt7.com.br",
]

CSRF_TRUSTED_ORIGINS = [ #Domínios confiáveis para validação de requisições com CSRF.
    'https://2e811d9ff57d.ngrok-free.app',
]

CORS_ALLOW_CREDENTIALS = True

DEFAULT_PASSWORD_USER = 'Admin@123'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'creative',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': '127.0.0.1',
        'PORT': '5432',  # Porta padrão do PostgreSQL é 5432
    },
}

DATA_UPLOAD_MAX_NUMBER_FIELDS = 10240
