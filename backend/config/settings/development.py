from .base import *

DEBUG = env.bool("DJANGO_DEBUG", default=True)

# Development convenience only.
#
# The storefront may be served from any local origin (localhost:3000,
# 127.0.0.1:3000, or a tunneled/preview hostname). Django's CSRF
# Origin check compares the browser's Origin against the request host
# and then against CSRF_TRUSTED_ORIGINS, so in development we also
# trust every origin the CORS layer already allows. This does not
# relax CSRF validation itself - the cookie and submitted token are
# still both required - and it never applies to production settings,
# where CSRF_TRUSTED_ORIGINS stays explicit.
CSRF_TRUSTED_ORIGINS = list(
    dict.fromkeys(
        [
            *CSRF_TRUSTED_ORIGINS,  # noqa: F405
            *CORS_ALLOWED_ORIGINS,  # noqa: F405
        ],
    ),
)
