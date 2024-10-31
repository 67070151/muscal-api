from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
import os

# Initialize Flask application
app = Flask(__name__)

# Set configurations
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:GWWoGUnWEbzBYRdkqmbfnRSLnOTiAkOv@autorack.proxy.rlwy.net:39603/railway'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Import routes (ensure you have a routes.py file with defined routes)
from routes import *

# Handler for Vercel serverless functions
def handler(environ, start_response):
    return app(environ, start_response)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create the database tables
    app.run(debug=True)
