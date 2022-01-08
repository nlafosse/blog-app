"""

Executes initialization code for the package

"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

# Configure application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'a9966de62ed8f6e458934a8c53c44710'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True
# Initiate database
db = SQLAlchemy(app)
# Hashing tool (for passwords)
bcrypt = Bcrypt(app)
# User session management. Handles logging in and out, and remembering users' sessions
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

from blog import routes

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response