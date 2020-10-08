import logging
import logging.config

from django.utils.log import DEFAULT_LOGGING
from django_log_formatter_ecs import ECSFormatter


config = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'django.server': {
            "()": ECSFormatter,
        },
        "ecs_formatter": {
            "()": ECSFormatter,
        },
        'standard': {
            'format':
                '%(asctime)s %(name)s.%(funcName)s %(levelname)s %(message)s'
        },
    },
    'handlers': {
        'django.server': {
            'level': 'NOTSET',
            'formatter': 'ecs_formatter',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout'
        },
        'default': {
            'level': 'NOTSET',
            'formatter': 'ecs_formatter',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout'
        },
        'celery': {
            'level': 'NOTSET',
            'formatter': 'ecs_formatter',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout'
        }
    },
    'loggers': {
        '': {
            'handlers': ['default'],
            'level': 'INFO',
            'propagate': True
        },
        'django.server': {
            'handlers': ['default'],
            'level': 'DEBUG',
            'propagate': False
        },
        'zenslackchat': {
            'handlers': ['default'],
            'level': 'DEBUG',
            'propagate': False
        },
        'slack': {
            'handlers': ['default'],
            'level': 'INFO',
            'propagate': False
        },
        'celery': {
            'handlers': ['default'],
            'level': 'DEBUG',
            'propagate': False
        }
    }
}

def log_setup():
    logging.config.dictConfig(config)
