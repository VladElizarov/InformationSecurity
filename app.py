import os
from dotenv import load_dotenv
from flask import Flask, jsonify

from extensions import db, jwt
from auth import auth_bp
from api import api_bp

load_dotenv()


def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY']                     = os.environ.get('SECRET_KEY', 'dev-secret')
    app.config['JWT_SECRET_KEY']                 = os.environ.get('JWT_SECRET_KEY', 'S3cur3JWTSecretKeyF0rLab1Python256Bits!')
    app.config['JWT_ACCESS_TOKEN_EXPIRES']       = int(os.environ.get('JWT_EXPIRATION_SEC', 86400))
    app.config['SQLALCHEMY_DATABASE_URI']        = os.environ.get('DATABASE_URL', 'sqlite:///securedb.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    jwt.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)

    @jwt.unauthorized_loader
    def missing_token(_):
        return jsonify({'error': 'Unauthorized'}), 401

    @jwt.invalid_token_loader
    def invalid_token(_):
        return jsonify({'error': 'Unauthorized'}), 401

    @jwt.expired_token_loader
    def expired_token(_, __):
        return jsonify({'error': 'Token expired'}), 401

    with app.app_context():
        db.create_all()

    return app


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 9091))
    create_app().run(host='0.0.0.0', port=port, debug=False)
