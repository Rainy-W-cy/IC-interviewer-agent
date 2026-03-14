"""Shim module so `python -m ic_interviewer.cli` works without installation."""

from src.ic_interviewer.cli import *  # noqa: F401,F403


if __name__ == "__main__":
    main()
