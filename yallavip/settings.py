"""
Django settings for yallavip project.

Generated by 'django-admin startproject' using Django 2.1.1.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""

import os
import  sys

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,os.path.join(BASE_DIR,'apps'))      #将应用包加入系统变量，便于模块导入
sys.path.insert(0,os.path.join(BASE_DIR,'extra_apps'))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'l4&l5iiqw7y&@t$&#*uzf+c5v(0-6(owwi%s%_+62(u7h$np^+'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',



    #'rules',
    'users',      #注册app
    #'goods',
    #'trade',
    #'user_operation',
    'performance',
    'customer',
    'distributor',
    'commodity',
    'operation',
    'fb',
    'conversations',
    'orders',
    'logistic',
    'purchase',
    'product',

    'sysadmin',
    'prs',
    'shop',
    'mytest',
    'tomtop',
    'funmart',


    # 添加drf应用
    'rest_framework',
    'rest_framework.authtoken',
    'django_filters',
    # Django跨域解决
    'corsheaders',

    'coreschema',


    'import_export',
    #'DjangoUeditor',
    'crispy_forms',
    'xadmin',   #注册xadmin
    'django_celery_results',
    'django_celery_beat',
    'django_extensions',


]
AUTHENTICATION_BACKENDS = [
    #'rules.permissions.ObjectPermissionBackend',
    'django.contrib.auth.backends.ModelBackend',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # corsheaders跨域
    'django.middleware.common.CommonMiddleware',  # corsheaders跨域
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

]

ROOT_URLCONF = 'yallavip.urls'


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


WSGI_APPLICATION = 'yallavip.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'yallavip',
        'USER': 'niger',
        'PASSWORD': 'Niger@2018',
        'HOST': 'localhost',

        'OPTIONS':{
            'charset': 'utf8mb4',
            "init_command": "SET foreign_key_checks = 0;",
        },
    },


    'primary': {
            # 'ENGINE': 'django.db.backends.sqlite3',
            # 'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'yallavip',
            'USER': 'niger',
            'PASSWORD': 'Niger@2018',
            'HOST': 'localhost',
            'OPTIONS': {
                'charset': 'utf8mb4',
                "init_command": "SET foreign_key_checks = 0;",
            },
        },
        'replica1': {
            'NAME': 'yallavip',
            'ENGINE': 'django.db.backends.mysql',
            'USER': 'niger',
            'PASSWORD': 'Niger@2018',
            'HOST': '140.82.27.238',
            'OPTIONS':{
                'charset': 'utf8mb4',
                "init_command": "SET foreign_key_checks = 0;",
            },
        },

    'auth_db': {
            # 'ENGINE': 'django.db.backends.sqlite3',
            # 'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'yallavip',
            'USER': 'niger',
            'PASSWORD': 'Niger@2018',
            'HOST': 'localhost',
            'OPTIONS': {'charset': 'utf8mb4'},
        },
}

'''
DATABASE_ROUTERS = [ 'yallavip.PrimaryReplicaRouter.PrimaryReplicaRouter', 'yallavip.AuthRouter.AuthRouter']
DATABASE_APPS_MAPPING = {
    # example:
    #'app_name':'database_name',


}
'''


AUTH_USER_MODEL = 'users.UserProfile'    #由于我们在users/models.py继承了django的AbstractUser，所以需要在settings.py中指定我们自定义的user模型,否则创建模型会报E304错误


# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Riyadh'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)
STATIC_ROOT = os.path.join(BASE_DIR, 'collectedstatic/')

# 这个是默认设置，Django 默认会在 STATICFILES_DIRS中的文件夹 和 各app下的static文件夹中找文件
# 注意有先后顺序，找到了就不再继续找了
STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder"
)

DATA_UPLOAD_MAX_NUMBER_FIELDS = None

MEDIA_URL = '/media/'
#MEDIA_ROOT = os.path.join(BASE_DIR, 'static/media/')
MEDIA_ROOT = os.path.join(BASE_DIR, 'media/')


PRODUCT_URL = '/product/'
#MEDIA_ROOT = os.path.join(BASE_DIR, 'static/media/')
PRODUCT_ROOT = os.path.join(BASE_DIR, 'product/')

#MATERIAL_ROOT = os.path.join(BASE_DIR, 'static/media/material/')

DATETIME_FORMAT = 'Y-m-d H:i:s'
DATE_FORMAT = 'Y-m-d'

CELERY_RESULT_BACKEND = 'django-db'
CELERY_RESULT_BACKEND = 'django-cache'

# 跨域CORS设置
# CORS_ORIGIN_ALLOW_ALL = False  # 默认为False，如果为True则允许所有连接
CORS_ORIGIN_WHITELIST = (  # 配置允许访问的白名单
    'http://localhost:8080',
    'http://127.0.0.1:8080',
)

# JWT自定义配置
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=7),  # 配置过期时间
    'REFRESH_TOKEN_LIFETIME': timedelta(days=15),
}

'''
my_app_id = "562741177444068"
my_app_secret = "e6df363351fb5ce4b7f0080adad08a4d"
my_access_token = "EAAHZCz2P7ZAuQBABHO6LywLswkIwvScVqBP2eF5CrUt4wErhesp8fJUQVqRli9MxspKRYYA4JVihu7s5TL3LfyA0ZACBaKZAfZCMoFDx7Tc57DLWj38uwTopJH4aeDpLdYoEF4JVXHf5Ei06p7soWmpih8BBzadiPUAEM8Fw4DuW5q8ZAkSc07PrAX4pGZA4zbSU70ZCqLZAMTQZDZD"


my_app_id_dev = "1976935359278305"
my_app_secret_dev = "f4ee797596ed236c0bc74d33f52e6a54"
my_access_token_dev = "EAAcGAyHVbOEBAAL2mne8lmKC55lbDMndPYEVR2TRmOWf9ePUN97SiZCqwCd3KOZBrEkC57rVt3ZClhXi6oxxf1i0hRCK50QALuAQOCs60U30FjNYimeP97xLjfl7wZAAjThdkXPJujsWcAXOwkTNKvKlmP6tZBPUtSYb3i4i1vUs40MZAUOzNIG9v7HNjnyyIZD"

second_app_id = "437855903410360"
second_token = "EAAGOOkWV6LgBAIGWTMe3IRKJQNp5ld7nxmiafOdWwlPn8BksJxFUsCiAqzMQ1ZC1LJipR2tcHXZBO949i0ZB5xOOfHbut2hk7sIP3YZB5MfuqjFtm9LGq3J7xrBtUFPLZBT9pe2UcUTXann8DXhwMPQOlIBANiNJE6RA11vNrZC0fGijUsDJds"
'''
