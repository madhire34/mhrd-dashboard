"""Gunicorn configuration for Render.

Render only routes traffic to a process listening on 0.0.0.0:$PORT, and the
Start Command configured in the Render dashboard can override render.yaml.
Gunicorn loads this file automatically from the working directory, so the
correct bind address is applied even if the Start Command omits --bind.
"""

import os

bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"
workers = int(os.environ.get('WEB_CONCURRENCY', '2'))
timeout = 120
keepalive = 5
