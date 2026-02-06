"""Entry point for launching the desktop application.

Allows running the project as `python main.py` in addition to
`python -m app.main`.
"""

from app.main import main


if __name__ == "__main__":
    raise SystemExit(main())
