"""Local entry point; production servers can use app:create_app()."""

from dotenv import load_dotenv

from app import create_app
from app.extensions import db

if __name__ == "__main__":
    load_dotenv()
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)
