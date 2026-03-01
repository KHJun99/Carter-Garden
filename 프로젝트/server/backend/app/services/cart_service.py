from app.models.cart import Cart
from app.extensions import db

def rent_cart(user_id, cart_id):
    cart = Cart.query.get(cart_id)
    if not cart:
        raise ValueError("Cart not found")
    if cart.status != 'WAITING':
        raise ValueError("Cart is not available for rent")
    # 카트 대여
    cart.user_id = user_id
    cart.status = 'USED'
    db.session.commit()
    return cart

def return_cart(cart_id):
    cart = Cart.query.get(cart_id)
    if not cart:
        raise ValueError("Cart not found")
    if cart.status != 'USED':
        raise ValueError("Cart is not currently rented out")
    # 카트 반납
    cart.user_id = None
    cart.status = 'WAITING'
    db.session.commit()
    return cart