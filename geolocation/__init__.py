import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_moment import Moment
from flask_script import Manager 
from flask_migrate import Migrate ,MigrateCommand
from flask_mail import Mail






app = Flask(__name__)
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///busspower.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:07888095501997Luck@localhost/buss'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False



db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'jokamediatz@gmail.com'
app.config['MAIL_PASSWORD'] = '07888095501997Luck'
mail = Mail(app)
moment = Moment(app)
migrate = Migrate(app ,db)
manager = Manager(app)

manager.add_command('db', MigrateCommand)


with app.app_context():
	if db.engine.url.drivername == 'sqlite':
	    migrate.init_app(app, db, render_as_batch=True)
	else:
	    migrate.init_app(app, db)


from geolocation import route