import bcrypt
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from markupsafe import escape

from extensions import db
from models import AuthModel

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


def _validate(login, password):
    if not login or not password:
        return 'login and password are required'
    if not (5 <= len(login) <= 50):
        return 'login must be 5-50 characters'
    if not (5 <= len(password) <= 50) or len(password.encode()) > 72:
        return 'password must be 5-50 characters'
    return None


@auth_bp.route('/register', methods=['POST'])
def register():
    data     = request.get_json(silent=True) or {}
    login    = str(data.get('login', '')).strip()
    password = str(data.get('password', ''))

    err = _validate(login, password)
    if err:
        return jsonify({'error': err}), 400

    safe_login = str(escape(login))
    if db.session.get(AuthModel, safe_login):
        return jsonify({'error': 'User already exists'}), 409

    hashed     = bcrypt.hashpw(password.encode(), bcrypt.gensalt(12)).decode()

    db.session.add(AuthModel(login=safe_login, password=hashed))
    db.session.commit()

    return jsonify({'access_token': create_access_token(identity=safe_login)}), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data     = request.get_json(silent=True) or {}
    login    = str(data.get('login', '')).strip()
    password = str(data.get('password', ''))

    err = _validate(login, password)
    if err:
        return jsonify({'error': err}), 400

    safe_login = str(escape(login))
    user = db.session.get(AuthModel, safe_login)

    if not user or not bcrypt.checkpw(password.encode(), user.password.encode()):
        return jsonify({'error': 'Incorrect password'}), 401

    return jsonify({'access_token': create_access_token(identity=safe_login)}), 200
