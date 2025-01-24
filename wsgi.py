# wsgi.py
import sys

# add your project directory to the sys.path
project_home = '/app'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# Import flask app and create 'app' variable for Render
from app.flask_app import app as application
app = application  # Add this line to make it work with Render

if __name__ == "__main__":
    app.run()