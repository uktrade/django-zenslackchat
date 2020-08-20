import logging
import logging.config

config = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format':
                '%(asctime)s %(name)s.%(funcName)s %(levelname)s %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level': 'NOTSET',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        '': {
            'handlers': ['default'],
            'level': 'INFO',
            'propagate': True
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
        }
    }
}

def log_setup():
    logging.config.dictConfig(config)
