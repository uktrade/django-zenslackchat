import os
import sys
import logging
import logging.config

from django.utils.log import DEFAULT_LOGGING
from django_log_formatter_ecs import ECSFormatter


config = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        "ecs": {
            "()": ECSFormatter,
        }
    },
    'handlers': {
        'default': {
            'level': 'NOTSET',
            'formatter': 'ecs',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout'
        },
    },
    'loggers': {
        '': {
            'handlers': ['default'],
            'level': 'INFO',
            'propagate': True
        },
        'django': {
            'handlers': ['default'],
            'level': 'INFO',
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
    """
    """
    if os.environ.get("DISABLE_ECS_LOG_FORMAT", "0").strip() == "1":
        sys.stderr.write("DISABLE_ECS_LOG_FORMAT=1 is set in environment!\n")
        # Format for more readable console output
        config['formatters']['ecs'] = {
           'format': 
                '%(asctime)s %(name)s.%(funcName)s %(levelname)s %(message)s'
        }

    logging.config.dictConfig(config)
