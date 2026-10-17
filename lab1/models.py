from extensions import db


class AuthModel(db.Model):
    __tablename__ = 'auth_table'

    login    = db.Column(db.String(50), primary_key=True)
    password = db.Column(db.String(255), nullable=False)


class ProductModel(db.Model):
    __tablename__ = 'product_table'

    id   = db.Column(db.Integer, primary_key=True, autoincrement=True)
    data = db.Column(db.String, nullable=False)
