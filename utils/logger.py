import logging
import logging.config


logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'husky.chat.generated.utils.logger_utils.FormattedStreamHandler',
            'level': 'INFO'
        },
        'laconic': {
            'class': 'husky.chat.generated.utils.logger_utils.LaconicStreamHandler',
            'level': 'INFO'
        }
    },
    'loggers': {
        'husky.chat.generated': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'husky.chat.generated.laconic_logger': {
            'handlers': ['laconic'],
            'level': 'INFO',
            'propagate': False
        }
    }
})


def get_logger(name):
    return logging.getLogger(name)


def get_tools_logger(name):
    return logging.getLogger('husky.chat.generated.' + name)


def _get_laconic_logger():
    return get_tools_logger('laconic_logger')


class WithLogger(object):
    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__module__ + '.' + self.__class__.__name__)


laconic_logger = _get_laconic_logger()
