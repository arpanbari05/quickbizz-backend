import datetime
from flask import Flask, request, jsonify, session
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
import re
from bson import ObjectId
from bson.regex import Regex

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a random secret key
app.config['MONGO_URI'] = 'mongodb://localhost:27017/QuickBizz'

mongo = PyMongo(app)

# Categories route
@app.route('/categories', methods=['GET'])
def get_all_categories():
    categories = mongo.db.products.distinct("category")
    return jsonify(categories), 200

@app.route('/categories/<category>', methods=['GET'])
def get_products_in_category(category):
    products = list(mongo.db.products.find({'category': category}))
    
    for product in products:
        product['_id'] = str(product['_id'])
        
    return jsonify(products), 200

# Search route
@app.route('/search', methods=['GET'])
def search_products():
    query = request.args.get('q')
    #Creating a case-insensitive regex to facilitate partial name search
    regex = Regex(".*" + query + ".*", "i")
    products = list(mongo.db.products.find({"name": {"$regex": regex}}))
    
    for product in products:
        product['_id'] = str(product['_id'])
        
    return jsonify(products), 200

# User signup route
@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    email_or_phone = data.get('email_or_phone')
    password = data.get('password')

    # Validate email or phone format
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email_or_phone) \
            and not re.match(r'^\+?\d{10,}$', email_or_phone):
        return jsonify({'error': 'Invalid email or phone format'}), 400

    # Check if user with the given email or phone already exists
    existing_user = mongo.db.users.find_one({'$or': [{'email': email_or_phone}, {'phone': email_or_phone}]})
    if existing_user:
        return jsonify({'error': 'User already exists'}), 400

    # Hash the password
    hashed_password = generate_password_hash(password)

    # Create user document
    user_data = {
        'first_name': first_name,
        'last_name': last_name,
        'email': email_or_phone if re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email_or_phone) else None,
        'phone': email_or_phone if re.match(r'^\+?\d{10,}$', email_or_phone) else None,
        'password': hashed_password,
        'address': '',
    }

    # Insert user into the database
    result = mongo.db.users.insert_one(user_data)

    return jsonify({'message': 'User created successfully', 'user_id': str(result.inserted_id)}), 201

# User login route
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email_or_phone = data.get('email_or_phone')
    password = data.get('password')

    # Check if user exists
    user = mongo.db.users.find_one({'$or': [{'email': email_or_phone}, {'phone': email_or_phone}]})
    if not user:
        return jsonify({'error': 'Invalid email/phone or password'}), 401

    # Check password
    if not check_password_hash(user['password'], password):
        return jsonify({'error': 'Invalid email/phone or password'}), 401

    # # Store user data in session
    # session['user_id'] = str(user['_id'])

    return jsonify({'message': 'Logged in successfully'}), 200

# Logout route
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return jsonify({'message': 'Logged out successfully'}), 200

# Create (Add a Product)
@app.route('/products', methods=['POST'])
def create_product():
    data = request.json
    name = data.get('name')
    price = data.get('price')
    ratings = data.get('ratings')
    number_of_reviews = data.get('number_of_reviews')
    description = data.get('description')
    category = data.get('category')
    image = data.get('image')

    if name and price:
        product_data = {
            'name': name,
            'price': price,
            'ratings': ratings,
            'number_of_reviews': number_of_reviews,
            'description': description,
            'category': category,
            'image': image,
        }
        result = mongo.db.products.insert_one(product_data)
        return jsonify({'message': 'Product created successfully', 'product_id': str(result.inserted_id)}), 201
    else:
        return jsonify({'error': 'Name and price are required fields'}), 400

# Read (Retrieve Products)
@app.route('/products', methods=['GET'])
def get_all_products():
    products = list(mongo.db.products.find())
    
    for product in products:
        product['_id'] = str(product['_id'])
        
    return jsonify(products), 200

@app.route('/products/<string:product_id>', methods=['GET'])
def get_product(product_id):
    product = mongo.db.products.find_one_or_404({'_id': ObjectId(product_id)})
    if product:
            product['_id'] = str(product['_id'])
            return jsonify(product), 200

# Update (Modify a Product)
@app.route('/products/<string:product_id>', methods=['PUT'])
def update_product(product_id):
    data = request.json
    name = data.get('name')
    price = data.get('price')
    ratings = data.get('ratings')
    number_of_reviews = data.get('number_of_reviews')
    description = data.get('description')
    category = data.get('category')
    image = data.get('image')

    if name or price or ratings or number_of_reviews or description:
        update_data = {}
        if name:
            update_data['name'] = name
        if price:
            update_data['price'] = price
        if ratings:
            update_data['ratings'] = ratings
        if number_of_reviews:
            update_data['number_of_reviews'] = number_of_reviews
        if description:
            update_data['description'] = description
        if category:
            update_data['category'] = category
        if image:
            update_data['image'] = image
        result = mongo.db.products.update_one({'_id': ObjectId(product_id)}, {'$set': update_data})
        if result.modified_count > 0:
            return jsonify({'message': 'Product updated successfully'}), 200
        else:
            return jsonify({'error': 'Product not found'}), 404
    else:
        return jsonify({'error': 'At least one field to update must be provided'}), 400

# Delete (Remove a Product)
@app.route('/products/<string:product_id>', methods=['DELETE'])
def delete_product(product_id):
    result = mongo.db.products.delete_one({'_id': ObjectId(product_id)})
    if result.deleted_count > 0:
        return jsonify({'message': 'Product deleted successfully'}), 200
    else:
        return jsonify({'error': 'Product not found'}), 404



# Create (Add an item to Wishlist)
@app.route('/wishlist/add', methods=['POST'])
def add_to_wishlist():
    data = request.json
    product_id = data.get('product_id')
    user_id = data.get('user_id')

    try:
        # Convert product_id string to ObjectId
        product_id = ObjectId(product_id)
    except Exception as e:
        return jsonify({'error': 'Invalid product_id format'}), 400

    # Check if product exists
    product = mongo.db.products.find_one({'_id': product_id})
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    

    # Check if the product is already in the user's wishlist
    existing_wishlist_item = mongo.db.wishlist.find_one({'product_id': product_id, 'user_id': user_id})
    if existing_wishlist_item:
        return jsonify({'error': 'Product already in wishlist'}), 400

    # Add item to the wishlist
    wishlist_item = {
        'product_id': product_id,
        'user_id': user_id
    }
    mongo.db.wishlist.insert_one(wishlist_item)

    return jsonify({'message': 'Product added to wishlist'}), 201

# Read (Retrieve items from Wishlist)
@app.route('/wishlist', methods=['GET'])
def get_wishlist():
    user_id = request.args.get('user_id')

    # Retrieve items from the user's wishlist
    wishlist_items = list(mongo.db.wishlist.find({'user_id': user_id}))

    # Get product details for each wishlist item
    products_in_wishlist = []
    for item in wishlist_items:
        product_id = ObjectId(item['product_id'])
        product = mongo.db.products.find_one({'_id': product_id})
        if product:
             # Convert ObjectId to string for serialization
            product['_id'] = str(product['_id'])
            products_in_wishlist.append(product)

    return jsonify(products_in_wishlist), 200

# Update (Modify an item in Wishlist) - Not necessary for this use case

# Delete (Remove an item from Wishlist)
@app.route('/wishlist/<string:wishlist_id>', methods=['DELETE'])
def remove_from_wishlist(wishlist_id):
    # Check if wishlist item exists
    wishlist_item = mongo.db.wishlist.find_one({'_id': ObjectId(wishlist_id)})
    if not wishlist_item:
        return jsonify({'error': 'Wishlist item not found'}), 404

    # Remove item from the wishlist
    mongo.db.wishlist.delete_one({'_id': ObjectId(wishlist_id)})

    return jsonify({'message': 'Item removed from wishlist'}), 200

# Route to find wishlisted products based on user email
@app.route('/wishlist', methods=['GET'])
def find_wishlisted_products():
    user_email = request.args.get('user_email')

    # Check if user exists
    user = mongo.db.users.find_one({'email': user_email})
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Retrieve wishlisted products for the user
    wishlist_items = list(mongo.db.wishlist.find({'user_id': str(user['_id'])}))

    # Get product details for each wishlisted item
    wishlisted_products = []
    for item in wishlist_items:
        product = mongo.db.products.find_one({'_id': item['product_id']})
        if product:
            wishlisted_products.append(product)

    return jsonify(wishlisted_products), 200




# Route to add an item to the cart
@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    data = request.json
    product_id = data.get('product_id')
    user_id = data.get('user_id')

    # Check if product exists
    product = mongo.db.products.find_one({'_id': product_id})
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    # Check if the product is already in the user's cart
    existing_cart_item = mongo.db.cart.find_one({'product_id': product_id, 'user_id': user_id})
    if existing_cart_item:
        return jsonify({'error': 'Product already in cart'}), 400

    # Calculate total price
    total_price = product['price']

    # Create cart item document
    cart_item = {
        'product_id': product['_id'],
        'user_id': user_id,
        'product': product,
        'quantity': 1,  # Default quantity is 1
        'total_price': total_price
    }

    # Insert item into the cart
    mongo.db.cart.insert_one(cart_item)

    return jsonify({'message': 'Product added to cart', 'total_price': total_price}), 201

# Route to find cart items and total price based on user email
@app.route('/cart', methods=['GET'])
def find_cart_items():
    user_id = request.args.get('user_id')

    # Retrieve cart items for the user
    cart_items = list(mongo.db.cart.find({'user_id': user_id}))

    # Calculate total price of all products in the cart
    total_price = sum(item['product']['price'] * item['quantity'] for item in cart_items)

    # Format cart items to include product details
    formatted_cart_items = []
    for item in cart_items:
        product = item['product']
        product['quantity'] = item['quantity']
        formatted_cart_items.append(product)

    return jsonify({'cart_items': formatted_cart_items, 'total_price': total_price}), 200



# Account information update route
@app.route('/account/update', methods=['PUT'])
def update_account():
    data = request.json
    user_id = data.get('user_id')  # Assuming user_id is provided in the request
    new_data = {}
    
    # Validate and update fields if provided
    if 'first_name' in data:
        new_data['first_name'] = data['first_name']
    if 'last_name' in data:
        new_data['last_name'] = data['last_name']
    if 'address' in data:
        new_data['address'] = data['address']
    if 'email_or_phone' in data:
        # Validate email or phone format
        email_or_phone = data['email_or_phone']
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email_or_phone) \
                and not re.match(r'^\+?\d{10,}$', email_or_phone):
            return jsonify({'error': 'Invalid email or phone format'}), 400
        new_data['email'] = email_or_phone if re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email_or_phone) else None
        new_data['phone'] = email_or_phone if re.match(r'^\+?\d{10,}$', email_or_phone) else None

    # Update user information
    result = mongo.db.users.update_one({'_id': ObjectId(user_id)}, {'$set': new_data})
    if result.modified_count > 0:
        return jsonify({'message': 'Account information updated successfully'}), 200
    else:
        return jsonify({'error': 'User not found'}), 404

# Change password route
@app.route('/account/change_password', methods=['PUT'])
def change_password():
    data = request.json
    user_id = data.get('user_id')  # Assuming user_id is provided in the request
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    confirm_new_password = data.get('confirm_new_password')

    # Check if new password matches confirm new password
    if new_password != confirm_new_password:
        return jsonify({'error': 'New password and confirm new password do not match'}), 400

    # Check if user exists
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Check if current password is correct
    if not check_password_hash(user['password'], current_password):
        return jsonify({'error': 'Current password is incorrect'}), 400

    # Hash the new password
    hashed_new_password = generate_password_hash(new_password)

    # Update user's password
    result = mongo.db.users.update_one({'_id': ObjectId(user_id)}, {'$set': {'password': hashed_new_password}})
    if result.modified_count > 0:
        return jsonify({'message': 'Password changed successfully'}), 200
    else:
        return jsonify({'error': 'Failed to change password'}), 500

# Get user information route
@app.route('/user/<string:user_id>', methods=['GET'])
def get_user(user_id):
    print(user_id)
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    if user:
        # Remove the password field from the response
        user.pop('password', None)
        user['_id'] = str(user['_id'])
        return jsonify(user), 200
    else:
        return jsonify({'error': 'User not found'}), 404
    
# Get all users route
@app.route('/users', methods=['GET'])
def get_all_users():
    users = list(mongo.db.users.find({}, {'password': 0}))  # Exclude password field
    
    for user in users:
        user['_id'] = str(user['_id'])
        
    return jsonify(users), 200



# Add order route
@app.route('/orders', methods=['POST'])
def add_order():
    data = request.json
    user_id = data.get('user_id')
    product_id = data.get('product_id')

    # Validate input
    if not (user_id and product_id):
        return jsonify({'error': 'Missing required fields'}), 400

    # Get product info
    product = mongo.db.products.find_one({'_id': ObjectId(product_id)})
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    # Autofill order fields
    total_amount = product.get('price')
    order_date = datetime.utcnow()
    status = 'In transit'

    # Create order document
    order_data = {
        'user_id': ObjectId(user_id),
        'product_id': ObjectId(product_id),
        'total_amount': total_amount,
        'order_date': order_date,
        'status': status
    }

    # Insert order into the database
    result = mongo.db.orders.insert_one(order_data)

    return jsonify({'message': 'Order added successfully', 'order_id': str(result.inserted_id)}), 201


# Sales route
@app.route('/sales', methods=['GET'])
def get_products_on_sale():
    products = list(mongo.db.products.find({'price': {'$lt': 100}}))

    # Convert ObjectId to str for serialization
    for product in products:
        product['_id'] = str(product['_id'])

    return jsonify(products), 200


# Best selling products route
@app.route('/best-selling', methods=['GET'])
def get_best_selling_products():
    # Find products with reviews greater than 4.5
    best_selling_products = list(mongo.db.products.find({'ratings': {'$gt': 4.5}}))

    # Convert ObjectId to str for serialization
    for product in best_selling_products:
        product['_id'] = str(product['_id'])

    return jsonify(best_selling_products), 200

# Route to get products by category
@app.route('/products/category/<string:category>', methods=['GET'])
def get_products_by_category(category):
    products = list(mongo.db.products.find({'category': category}))

    # Convert ObjectId to str for serialization
    for product in products:
        product['_id'] = str(product['_id'])

    return jsonify(products), 200


if __name__ == '__main__':
    app.run(debug=True)