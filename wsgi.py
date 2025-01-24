# wsgi.py
from app.flask_app import app as application  # noqa

if __name__ == "__main__":
    application.run()