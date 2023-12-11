from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

db = SQLAlchemy()
bcrypt = Bcrypt()


def create_app(test_config=None):
    app = Flask(__name__)

   # added following 2 lines, configures database connection and initialize the object, untested
    app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+mysqldb://24_webapp_024:TSTTfeYu@mysql.lab.it.uc3m.es/24_webapp_024a"

    # A secret for signing session cookies
    app.config["SECRET_KEY"] = "93220d9b340cf9a6c39bac99cce7daf220167498f91fa"
    
    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)
    from . import model

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(model.User, int(user_id))


    # Register blueprints
    # import main from here to avoid circular imports
    from . import main

    app.register_blueprint(main.bp)

    from . import auth
    app.register_blueprint(auth.bp)

   # I think don't need since never calls init.py? 
    # from. import recipes
    # app.register_blueprint(recipes.bp)

    return app

