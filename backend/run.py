"""
Convenience launcher — run this instead of typing the full uvicorn command.

    python run.py

Equivalent to:

    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
"""

import uvicorn
from config import settings

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level=settings.log_level,
    )
