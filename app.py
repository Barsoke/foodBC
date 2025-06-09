
from datetime import datetime, timedelta
from flask_cors import CORS
from flask import Flask, request, jsonify
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, get_jwt_identity
)
from models import db, User, Category, Product, CartItem, Order

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    CORS(app)

    db.init_app(app)
    jwt = JWTManager(app)

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({'msg': 'Токен истёк. Пожалуйста, войдите снова.'}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({'msg': 'Неверный токен. Пожалуйста, войдите снова.'}), 422

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({'msg': 'Токен не предоставлен.'}), 401

    @app.route('/api/auth/test-token', methods=['GET'])
    @jwt_required()
    def test_token():
        user_id = get_jwt_identity()
        return jsonify({'msg': 'Токен валиден', 'sub_type': str(type(user_id)), 'sub_value': user_id}), 200

    with app.app_context():
        db.create_all()


    @app.route('/api/auth/register', methods=['POST'])
    def register():

        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        full_name = data.get('full_name')

        if not email or not password:
            return jsonify({'msg': 'Email и пароль обязательны.'}), 400

        if User.query.filter_by(email=email).first():
            return jsonify({'msg': 'Пользователь с таким email уже существует.'}), 400

        user = User(email=email, full_name=full_name)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        return jsonify({'msg': 'Регистрация прошла успешно.'}), 201

    @app.route('/api/auth/login', methods=['POST'])
    def login():

        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            return jsonify({'msg': 'Неверные учётные данные.'}), 401

        access_token = create_access_token(identity=str(user.id), expires_delta=timedelta(hours=1))
        return jsonify({'access_token': access_token, 'user_id': user.id}), 200


    @app.route('/api/categories', methods=['GET'])
    def get_categories():

        categories = Category.query.all()
        result = []
        for cat in categories:
            result.append({
                'id': cat.id,
                'name': cat.name
            })
        return jsonify(result), 200

    @app.route('/api/categories/<int:category_id>/products', methods=['GET'])
    def get_products_by_category(category_id):

        products = Product.query.filter_by(category_id=category_id).all()
        result = []
        for p in products:
            result.append({
                'id': p.id,
                'name': p.name,
                'description': p.description,
                'price': p.price,
                'image_url': p.image_url
            })
        return jsonify(result), 200

    @app.route('/api/products', methods=['GET'])
    def get_all_products():

        products = Product.query.all()
        result = []
        for p in products:
            result.append({
                'id': p.id,
                'name': p.name,
                'description': p.description,
                'price': p.price,
                'image_url': p.image_url,
                'category_id': p.category_id
            })
        return jsonify(result), 200


    @app.route('/api/cart', methods=['GET'])
    @jwt_required()
    def view_cart():

        user_id = get_jwt_identity()
        items = CartItem.query.filter_by(user_id=user_id).all()
        result = []
        for item in items:
            result.append({
                'id': item.id,
                'product_id': item.product_id,
                'product_name': item.product.name,
                'price': item.product.price,
                'quantity': item.quantity
            })
        return jsonify(result), 200

    @app.route('/api/cart/add', methods=['POST'])
    @jwt_required()
    def add_to_cart():

        user_id = get_jwt_identity()
        data = request.get_json()
        product_id = data.get('product_id')
        quantity = data.get('quantity', 1)

        if not product_id or quantity < 1:
            return jsonify({'msg': 'Неверные данные.'}), 400

        product = Product.query.get(product_id)
        if not product:
            return jsonify({'msg': 'Товар не найден.'}), 404

        existing = CartItem.query.filter_by(user_id=user_id, product_id=product_id).first()
        if existing:
            existing.quantity += quantity
        else:

            item = CartItem(user_id=user_id, product_id=product_id, quantity=quantity)
            db.session.add(item)
        db.session.commit()
        return jsonify({'msg': 'Товар добавлен в корзину.'}), 200

    @app.route('/api/auth/logout', methods=['POST'])
    @jwt_required()
    def logout():

        return jsonify({'msg': 'Вы вышли из системы. Удалите токен на клиенте.'}), 200
    @app.route('/api/cart/update', methods=['PUT'])
    @jwt_required()
    def update_cart_item():

        user_id = get_jwt_identity()
        data = request.get_json()
        cart_item_id = data.get('cart_item_id')
        quantity = data.get('quantity')

        if quantity is None or cart_item_id is None:
            return jsonify({'msg': 'Неверные данные.'}), 400

        item = CartItem.query.filter_by(id=cart_item_id, user_id=user_id).first()
        if not item:
            return jsonify({'msg': 'Позиция не найдена.'}), 404

        if quantity < 1:
            db.session.delete(item)
        else:
            item.quantity = quantity
        db.session.commit()
        return jsonify({'msg': 'Корзина обновлена.'}), 200

    @app.route('/api/cart/clear', methods=['POST'])
    @jwt_required()
    def clear_cart():

        user_id = get_jwt_identity()
        CartItem.query.filter_by(user_id=user_id).delete()
        db.session.commit()
        return jsonify({'msg': 'Корзина очищена.'}), 200



    @app.route('/api/order/create', methods=['POST'])
    @jwt_required()
    def create_order():

        user_id = get_jwt_identity()
        data = request.get_json()
        delivery_address = data.get('delivery_address')

        if not delivery_address:
            return jsonify({'msg': 'Адрес доставки обязателен'}), 400

        items = CartItem.query.filter_by(user_id=user_id).all()
        if not items:
            return jsonify({'msg': 'Корзина пустая.'}), 400

        subtotal = sum(item.product.price * item.quantity for item in items)
        delivery_fee = 5.99 + subtotal * 0.1  # Базовая плата + 10% от суммы заказа

        items_list = []
        for item in items:
            items_list.append({
                'product_id': item.product_id,
                'name': item.product.name,
                'price': item.product.price,
                'quantity': item.quantity
            })

        order = Order(
            user_id=user_id,
            status='pending',
            items=items_list,
            delivery_address=delivery_address,
            delivery_fee=delivery_fee,
            courier_path=None
        )
        db.session.add(order)

        # Очищаем корзину
        for it in items:
            db.session.delete(it)

        db.session.commit()

        return jsonify({
            'msg': 'Заказ создан.',
            'order_id': order.id,
            'delivery_fee': delivery_fee
        }), 201

    @app.route('/api/order/<int:order_id>/pay', methods=['POST'])
    @jwt_required()
    def pay_order(order_id):

        user_id = get_jwt_identity()
        order = Order.query.filter_by(id=order_id, user_id=user_id).first()
        if not order:
            return jsonify({'msg': 'Заказ не найден.'}), 404

        if order.status != 'pending':
            return jsonify({'msg': f'Нельзя оплатить заказ в статусе {order.status}.'}), 400

        order.status = 'accepted'


        delivery_steps = [
            {"step": "Заказ принят", "timestamp": (datetime.utcnow() + timedelta(minutes=0)).isoformat()},
            {"step": "Начали собирать", "timestamp": (datetime.utcnow() + timedelta(minutes=5)).isoformat()},
            {"step": "Передали курьеру", "timestamp": (datetime.utcnow() + timedelta(minutes=15)).isoformat()},
            {"step": "Курьер в пути", "timestamp": (datetime.utcnow() + timedelta(minutes=20)).isoformat()},
            {"step": "Прибыл к вам", "timestamp": (datetime.utcnow() + timedelta(minutes=35)).isoformat()}
        ]
        order.courier_path = delivery_steps

        db.session.commit()
        return jsonify({
            'msg': 'Оплата принята. Заказ в процессе доставки.',
            'order_id': order.id,
            'delivery_steps': delivery_steps
        }), 200

    @app.route('/api/order/<int:order_id>/status', methods=['GET'])
    @jwt_required()
    def order_status(order_id):

        user_id = get_jwt_identity()
        order = Order.query.filter_by(id=order_id, user_id=user_id).first()
        if not order:
            return jsonify({'msg': 'Заказ не найден.'}), 404

        response = {
            'order_id': order.id,
            'status': order.status,
        }
        if order.status == 'accepted':
            response['courier_path'] = order.courier_path

        return jsonify(response), 200


    @app.route('/api/account/me', methods=['GET'])
    @jwt_required()
    def get_my_account():
        """
        Возвращает информацию о текущем пользователе.
        """
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        return jsonify({
            'id': user.id,
            'email': user.email,
            'full_name': user.full_name,
            'created_at': user.created_at.isoformat()
        }), 200

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
