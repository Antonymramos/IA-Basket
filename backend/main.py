#!/usr/bin/env python3
"""Oracle NBA API entrypoint.

Para rodar: `python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000`
"""

from backend.oracle_api import app
