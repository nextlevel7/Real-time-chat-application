"""Compatibility entry point for uv run main.py."""

from dotenv import load_dotenv

from app import create_app

if __name__ == "__main__":
    load_dotenv()
    create_app().run()
