from flask import Flask
from .config import Config
from .extensions import db, migrate, cors, swagger, ma, jwt
from .errors import register_error_handlers

def create_app():
    app = Flask(__name__, static_folder='../static')
    app.config.from_object(Config)

    # JWT 초기화
    jwt.init_app(app)

    # DB, Migrate, CORS 초기화
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app)

    # Swagger 설정
    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": 'apispec_1',
                "route": '/apispec_1.json',
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/apidocs/"
    }

    template = {
        "swagger": "2.0",
        "info": {
            "title": "Smart Cart API",
            "description": "SSAFY 스마트 카트 프로젝트 API 문서",
            "version": "1.0.0"
        },
        "securityDefinitions": {
            "Bearer": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "JWT Authorization header using the Bearer scheme. Example: \"Bearer {token}\""
            }
        },
        "security": [
            {"Bearer": []}
        ]
    }

    # init_app() 안에 넣지 않고, app.config와 객체 속성으로 설정
    app.config['SWAGGER'] = swagger_config
    swagger.template = template
    swagger.init_app(app)
    ma.init_app(app)
    # ==========================================

    # Register error handlers
    register_error_handlers(app)

    # Register Blueprints (Routes)
    from .routes.product_route import product_bp
    from .routes.cart_route import cart_bp
    from .routes.s3_route import s3_bp
    from .routes.coupon_route import coupon_bp
    from .routes.user_route import user_bp
    from .routes.location_route import location_bp
    from .routes.park_route import park_bp
    from .routes.map_route import map_bp
    from .routes.payment_route import payment_bp
    
    app.register_blueprint(user_bp, url_prefix='/api/users')
    app.register_blueprint(product_bp, url_prefix='/api/products')
    app.register_blueprint(cart_bp, url_prefix='/api/carts')
    app.register_blueprint(s3_bp, url_prefix='/api/s3')
    app.register_blueprint(coupon_bp, url_prefix='/api/coupons')
    app.register_blueprint(location_bp, url_prefix='/api/locations')
    app.register_blueprint(park_bp, url_prefix='/api/parking')
    app.register_blueprint(map_bp, url_prefix='/api/map')
    app.register_blueprint(payment_bp, url_prefix='/api/payment')

    return app