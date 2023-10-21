import os
from flask import Flask
from models import db
from views import auth_bp
from flask_cors import CORS
from flask_jwt_extended import JWTManager

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///db.sqlite3")
app.config['CONVERTED_FOLDER'] = '/app/media/converted'
app.config['ORIGINALS_FOLDER'] = '/app/media/uploaded'
app.config['JWT_SECRET_KEY'] = 'frase-secreta'
app.config['PROPAGATE_EXCEPTIONS'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app_context = app.app_context()
app_context.push()

db.init_app(app)
db.create_all()

cors = CORS(app)
jwt = JWTManager(app)

app.register_blueprint(auth_bp, url_prefix='/api/auth')

if __name__ == "__main__":
    API_PORT = os.environ.get("API_PORT", 5000)
    app.run(debug=True, port=API_PORT, host="0.0.0.0")
