from .base import *  # noqa: F401,F403

DEBUG = True

ALLOWED_HOSTS = list(set(ALLOWED_HOSTS) | {"localhost", "127.0.0.1", "10.0.2.2"})
