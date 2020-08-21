import logging

import pytest

from zenslackchat.botlogging import log_setup


@pytest.fixture(scope="module")
def log():
    """Set up logging as a pytest fixture."""
    log_setup()
    return logging.getLogger('zenslackchat')
