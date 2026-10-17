from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from markupsafe import escape

from models import ProductModel

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/data', methods=['GET'])
@jwt_required()
def get_data():
    products = ProductModel.query.all()
    return jsonify([
        {'id': p.id, 'data': str(escape(p.data))}
        for p in products
    ]), 200
