from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os


# Flask INIT
app = Flask(__name__,
            template_folder=os.path.join(os.path.dirname(__file__), "../frontend/templates"),
            static_folder=os.path.join(os.path.dirname(__file__), "../frontend/static")
            )

# App Configurations
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///storygram.db"
app.config["DATABASE_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "randomKey"

# Database INIT
db = SQLAlchemy(app)

migrate = Migrate(app, db)

