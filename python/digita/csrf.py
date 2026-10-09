"""Jeton CSRF stocké en session (équivalent de CsrfMiddleware PHP)."""
import hmac
import secrets

from . import php

TOKEN_NAME = "_csrf_token"


def get_token(session):
    if TOKEN_NAME not in session:
        session[TOKEN_NAME] = secrets.token_hex(32)
    return session[TOKEN_NAME]


def csrf_field(session):
    return f'<input type="hidden" name="{TOKEN_NAME}" value="{php.h(get_token(session))}">'


def validate(session, token):
    expected = session.get(TOKEN_NAME)
    return bool(expected and token and hmac.compare_digest(expected, token))
