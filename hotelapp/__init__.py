from flask import Flask
from urllib.parse import quote
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail, Message

app = Flask(__name__, static_folder='./static')

app.secret_key = '890f32ff363679f635988bd8c7910afe41fb463937feafb39df5490489c4c171'
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:%s@localhost/bookingdb?charset=utf8mb4" % quote(
    '0335037042Think.')
# app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:%s@localhost/bookingdb?charset=utf8mb4" % quote(
#     'Admin@123')
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config["PAGE_SIZE"] = 8
app.config["SESSION_COOKIE_HTTPONLY"] = False

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'pthinh.lama@gmail.com'
app.config['MAIL_PASSWORD'] = 'hqdf zduc bsyg eixo'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

login_manager = LoginManager(app)
mail = Mail(app)

db = SQLAlchemy(app)
