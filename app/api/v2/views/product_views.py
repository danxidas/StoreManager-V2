from flask import jsonify, request, Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity
from ...utils import Validator, KeyValidators
from ..models.product_models import ProductModel
from ..models.sales_models import SalesModel
from ..models.user_models import UserModel

prod = Blueprint('v2_prods', __name__)
prod_obj = ProductModel()
sales_obj = SalesModel()
users_obj = UserModel()


@prod.route('/api/v2/products', methods=['POST'])
@jwt_required
def post_product():
    email = get_jwt_identity()
    user = users_obj.get_user_by_email(email)
    role = user["role"]
    if role != "admin":
        return jsonify({"Message":
                        "You must be an admin to add a product"}), 401
    data = request.get_json()
    key_valid = KeyValidators(data)
    if key_valid.check_missing_keys_in_product():
        return key_valid.check_missing_keys_in_product()
    validate = Validator(data)
    if validate.validate_product():
        return validate.validate_product()
    product = ProductModel(data)
    product.create_product()
    return jsonify({"Message": "Product registered successfully",
                    "Products Profile": product.get_all_products()}), 201


@prod.route('/api/v2/products', methods=['GET'])
@jwt_required
def get_all_products():
    """Fetches all products from the database and returns them"""
    prods = prod_obj.get_all_products()
    if len(prods) > 0:
        return jsonify({"Message": "Product list retrieved successfully!",
                        "All products": prods}), 200
    return jsonify({"Message": "Products not found!"}), 404


@prod.route('/api/v2/products/<int:product_id>', methods=['GET'])
@jwt_required
def get_products_by_id(product_id):
    """Fetches a product using supplied product id"""
    product = prod_obj.get_product_by_id(product_id)
    if not product or len(product) == 0:
        return jsonify({"Message": "Product not found!"}), 404
    return jsonify({"Message": "Product retrieved successfully!",
                    "Product Profile": product}), 200


@prod.route('/api/v2/products/<product_name>', methods=['GET'])
@jwt_required
def get_product_by_name(product_name):
    """Fetches a product using the supplied name"""
    product = prod_obj.get_product_by_name(product_name)
    if not product or len(product) == 0:
        return jsonify({"Message": "Product not found!"}), 404
    return jsonify({"Message": "Product retrieved successfully!",
                    "Product Profile": product}), 200


@prod.route('/api/v2/products/<int:product_id>', methods=['PUT'])
@jwt_required
def update_products(product_id):
    """Updates a specific product's details"""
    email = get_jwt_identity()
    user = users_obj.get_user_by_email(email)
    role = user["role"]
    if role != "admin":
        return jsonify({"Message":
                        "You must be an admin to perform this action"}), 401
    data = request.get_json()
    validate = Validator(data)
    key_valid = KeyValidators(data)
    if key_valid.check_missing_keys_in_product():
        return key_valid.check_missing_keys_in_product()
    if validate.validate_product():
        return validate.validate_product()
    product_obj = ProductModel(data)
    resp = product_obj.get_product_by_id(product_id)
    if resp:
        product_obj.update_product(product_id)
        return jsonify({"Message": "Product successfully updated",
                        "Product Profile":
                            prod_obj.get_product_by_id(product_id)
                        }), 200
    return jsonify({"Message": "Product not found!"}), 404


@prod.route('/api/v2/products/<int:product_id>', methods=['DELETE'])
@jwt_required
def delete_product_by_id(product_id):
    email = get_jwt_identity()
    user = users_obj.get_user_by_email(email)
    role = user["role"]
    if role != "admin":
        return jsonify({"Message":
                        "You must be an admin to sale a product"}), 401
    resp = prod_obj.get_product_by_id(product_id)
    resp2 = sales_obj.get_sale_by_prod_id(product_id)
    print(resp2)
    if resp:
        if not resp2:
            prod_obj.delete_product(product_id)
            return jsonify({"Message": "Product deleted successfully!"}), 200
        return jsonify({"Message": "Product cannot be deleted. "
                                   "A sale(s) for the product exists"}), 403
    return jsonify({"Message": "Product not found!"}), 404


@prod.route('/api/v2/sales', methods=['POST'])
@jwt_required
def create_sale_record():
    """Creates a sales record and saves it to the database"""
    email = get_jwt_identity()
    user = users_obj.get_user_by_email(email)
    role = user["role"]
    if role != "attendant":
        return jsonify({"Message":
                        "You must be an attendant to sale a product"}), 401
    data = request.get_json()
    key_valid = KeyValidators(data)
    if key_valid.check_missing_keys_in_sales():
        return key_valid.check_missing_keys_in_sales()
    validate = Validator(data)
    if validate.validate_sales():
        return validate.validate_sales()
    try:
        user_id = user["user_id"]
        prod_id = data["prod_id"]
        sold_quantity = data["quantity"]
    except KeyError:
        return jsonify({"Message": "You have a missing parameter!"}), 400
    resp = prod_obj.get_product_by_id(prod_id)
    if not resp:
        return jsonify({"Message": "Product was not found!"}), 404
    prod_price = resp['prod_price']
    if resp['prod_quantity'] > sold_quantity \
            and resp['prod_quantity'] > int(resp['minimum_allowed']):
        prod_obj.update_prod_quantity(
            resp["prod_quantity"] - sold_quantity, prod_id)
        sale_obj = SalesModel(user_id, prod_id, sold_quantity, prod_price)
        sale_obj.create_sale_record()
        return jsonify({"Message":
                        "Sale record created successfully!"}), 201
    return jsonify({"Message":
                    "Sold quantity exceeds what is in stock!"}), 400


@prod.route('/api/v2/sales', methods=['GET'])
@jwt_required
def get_all_sales():
    """Fetches all sales from the database"""
    email = get_jwt_identity()
    user = users_obj.get_user_by_email(email)
    role = user["role"]
    user_id = user["user_id"]
    if role != "admin":
        return jsonify({"Message": "Sale records retrieved successfully!",
                        "Sale records":
                            sales_obj.get_sales_by_user_id(user_id)}), 200
    sales = sales_obj.get_all_sales()
    if not sales or len(sales) == 0:
        return jsonify({"Message": "Sales not found!"}), 404
    return jsonify({"Message": "Sales retrieved successfully!",
                    "All Sales": sales
                    }), 200


@prod.route('/api/v2/sales/<int:sales_id>', methods=['GET'])
@jwt_required
def get_sales_by_id(sales_id):
    """Fetches a sale from the database using supplied id"""
    sale_one = sales_obj.get_sale_by_id(sales_id)
    if not sale_one or len(sale_one) == 0:
        return jsonify({"Message": "Sales record not found!"}), 404
    return jsonify({"Message": "Sale retrieved successfully",
                    "Sale Profile": sale_one}), 200


@prod.errorhandler(404)
def page_not_found(e):
    """Returns an error message if page is missing or route is wrong"""
    return jsonify(
        {"Message": "The page is missing. Please check your route!"}), 404


@prod.errorhandler(500)
def server_error(e):
    """Handles internal server errors"""
    return jsonify({
        "Message": "There was an error processing your request!"}), 500
