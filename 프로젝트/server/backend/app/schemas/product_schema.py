from app.extensions import ma
from app.models.product import Product, Category
from marshmallow import fields
from app.schemas.location_schema import LocationSchema

from app.utils.image_utils import get_image_url

class CategorySchema(ma.SQLAlchemyAutoSchema):
  class Meta:
    model = Category
    load_instance = True

class ProductSchema(ma.SQLAlchemyAutoSchema):
  location = fields.Nested(LocationSchema, only=("location_code", "pos_x", "pos_y", "category"))

  class Meta:
    model = Product
    load_instance = True
    include_fk = True
    ordered = True
  
  image_url = fields.Method("get_full_image_url")
  
  def get_full_image_url(self, obj):
    return get_image_url(obj.image_url)

category_schema = CategorySchema()
categories_schema = CategorySchema(many = True)

product_schema = ProductSchema()
products_schema = ProductSchema(many = True)