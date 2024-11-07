from datetime import datetime
from flask_socketio import SocketIO, emit
from flask import Flask, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
import re
from bson import ObjectId
from bson.regex import Regex
from flask_cors import CORS
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from flask_pymongo import PyMongo


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
CORS(app,resources={r"/*":{"origins":"*"}})
socketio = SocketIO(app,cors_allowed_origins="*")








# PRODUCTION SERVER
# # Create a new client and connect to the server
uri = "mongodb+srv://arpanbari05:Sachin10@cluster0.gfggbs6.mongodb.net/QuickBizz?retryWrites=true&w=majority&appName=Cluster0"
# Create a new client and connect to the server
client = MongoClient(uri)

# Create a new client and connect to the server
mongo = MongoClient(uri, server_api=ServerApi('1'))
db = mongo.QuickBizz
# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

# LOCAL SERVER
# app.config['MONGO_URI'] = 'mongodb://localhost:27017/QuickBizz'  # Update with your MongoDB URI
# mongo = PyMongo(app)
# db = mongo.db

# Categories route
@app.route('/categories', methods=['GET'])
def get_all_categories():
    categories = db.products.distinct("category")
    return jsonify(categories), 200

@app.route('/categories/<category>', methods=['GET'])
def get_products_in_category(category):
    products = list(db.products.find({'category': category}))
    
    for product in products:
        product['_id'] = str(product['_id'])
        
    return jsonify(products), 200

# Search route
@app.route('/search', methods=['GET'])
def search_products():
    query = request.args.get('query')

    if not query:
        return jsonify({'error': 'Query parameter "query" is required'}), 400

    # Construct a MongoDB query to search for products
    search_query = {
        '$or': [
            {'name': {'$regex': query, '$options': 'i'}},
            {'category': {'$regex': query, '$options': 'i'}}
        ]
    }

    products = list(db.products.find(search_query))

    # Convert ObjectId to str for serialization
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
    existing_user = db.users.find_one({'$or': [{'email': email_or_phone}, {'phone': email_or_phone}]})
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
    result = db.users.insert_one(user_data)

    return jsonify({'message': 'User created successfully', 'user_id': str(result.inserted_id)}), 201

# User login route
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email_or_phone = data.get('email_or_phone')
    password = data.get('password')

    # Check if user exists
    user = db.users.find_one({'$or': [{'email': email_or_phone}, {'phone': email_or_phone}]})
    if not user:
        return jsonify({'error': 'Invalid email/phone or password'}), 401

    # Check password
    if not check_password_hash(user['password'], password):
        return jsonify({'error': 'Invalid email/phone or password'}), 401

    # # Store user data in session
    # session['user_id'] = str(user['_id'])

    return jsonify({'message': 'Logged in successfully', 'user_id': str(user['_id'])}), 200

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
    sold_by = data.get('sold_by')

    if name and price:
        product_data = {
            'name': name,
            'price': price,
            'ratings': ratings,
            'number_of_reviews': number_of_reviews,
            'description': description,
            'category': category,
            'image': image,
            'sold_by': sold_by,
        }
        result = db.products.insert_one(product_data)
        return jsonify({'message': 'Product created successfully', 'product_id': str(result.inserted_id)}), 201
    else:
        return jsonify({'error': 'Name and price are required fields'}), 400

# Read (Retrieve Products)
@app.route('/products', methods=['GET'])
def get_all_products():
    products = list(db.products.find())
    
    for product in products:
        product['_id'] = str(product['_id'])
        
    return jsonify(products), 200

@app.route('/products/<string:product_id>', methods=['GET'])
def get_product(product_id):
    product = db.products.find_one({'_id': ObjectId(product_id)})
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
    sold_by = data.get('sold_by')

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
        if sold_by:
            update_data['sold_by'] = sold_by
        result = db.products.update_one({'_id': ObjectId(product_id)}, {'$set': update_data})
        if result.modified_count > 0:
            return jsonify({'message': 'Product updated successfully'}), 200
        else:
            return jsonify({'error': 'Product not found'}), 404
    else:
        return jsonify({'error': 'At least one field to update must be provided'}), 400

# Delete (Remove a Product)
@app.route('/products/<string:product_id>', methods=['DELETE'])
def delete_product(product_id):
    result = db.products.delete_one({'_id': ObjectId(product_id)})
    if result.deleted_count > 0:
        return jsonify({'message': 'Product deleted successfully'}), 200
    else:
        return jsonify({'error': 'Product not found'}), 404


# Route to update the sold_by field of a product
@app.route('/products/update/sold_by/<string:product_id>', methods=['PUT'])
def update_sold_by(product_id):
    seller = request.json.get('seller')

    if not seller:
        return jsonify({'error': 'Seller information is required in the request body'}), 400

    # Check if the product exists
    product = db.products.find_one({'_id': ObjectId(product_id)})
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    # Add the seller to the sold_by list
    sold_by_list = product.get('sold_by', [])
    sold_by_list.append(seller)

    # Update the product document with the new sold_by list
    db.products.update_one({'_id': ObjectId(product_id)}, {'$set': {'sold_by': sold_by_list}})

    return jsonify({'message': 'Sold_by field updated successfully'}), 200


# Create (Add an item to Wishlist)
@app.route('/wishlist/add', methods=['POST'])
def add_to_wishlist():
    data = request.json
    product_id = data.get('product_id')
    user_id = data.get('user_id')

    try:
        # Convert product_id string to ObjectId
        product_id = ObjectId(product_id)
        user_id = ObjectId(user_id)
    except Exception as e:
        return jsonify({'error': 'Invalid product_id format'}), 400

    # Check if product exists
    product = db.products.find_one({'_id': product_id})
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    

    # Check if the product is already in the user's wishlist
    existing_wishlist_item = db.wishlist.find_one({'product_id': product_id, 'user_id': user_id})
    if existing_wishlist_item:
        return jsonify({'error': 'Product already in wishlist'}), 400

    # Add item to the wishlist
    wishlist_item = {
        'product_id': product_id,
        'user_id': user_id
    }
    db.wishlist.insert_one(wishlist_item)

    return jsonify({'message': 'Product added to wishlist'}), 201

# Read (Retrieve items from Wishlist)
@app.route('/wishlist/<string:user_id>', methods=['GET'])
def get_wishlist(user_id):

    # Retrieve items from the user's wishlist
    wishlist_items = list(db.wishlist.find({'user_id': ObjectId(user_id)}))

    # Get product details for each wishlist item
    products_in_wishlist = []
    for item in wishlist_items:
        product_id = ObjectId(item['product_id'])
        product = db.products.find_one({'_id': product_id})
        if product:
             # Convert ObjectId to string for serialization
            product['_id'] = str(product['_id'])
            products_in_wishlist.append(product)

    return jsonify(products_in_wishlist), 200

# Update (Modify an item in Wishlist) - Not necessary for this use case
# Route to remove product from wishlist
@app.route('/wishlist/remove', methods=['DELETE'])
def remove_product_from_wishlist():
    user_id = request.args.get('user_id')
    product_id = request.args.get('product_id')

    if not (user_id and product_id):
        return jsonify({'error': 'Missing user_id or product_id parameter'}), 400

    # Remove product from wishlist
    result = db.wishlist.delete_one({'user_id': ObjectId(user_id), 'product_id': ObjectId(product_id)})
    if result.deleted_count > 0:
        return jsonify({'message': 'Product removed from wishlist'}), 200
    else:
        return jsonify({'error': 'Product not found in wishlist'}), 404


# Route to find wishlisted products based on user email
@app.route('/wishlist', methods=['GET'])
def find_wishlisted_products():
    user_email = request.args.get('user_email')

    # Check if user exists
    user = db.users.find_one({'email': user_email})
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Retrieve wishlisted products for the user
    wishlist_items = list(db.wishlist.find({'user_id': str(user['_id'])}))

    # Get product details for each wishlisted item
    wishlisted_products = []
    for item in wishlist_items:
        product = db.products.find_one({'_id': item['product_id']})
        if product:
            wishlisted_products.append(product)

    return jsonify(wishlisted_products), 200


# Route to check if a product is wishlisted for a user
@app.route('/wishlist/check', methods=['GET'])
def check_product_wishlist():
    user_id = request.args.get('user_id')
    product_id = request.args.get('product_id')

    if not (user_id and product_id):
        return jsonify({'error': 'Missing user_id or product_id parameter'}), 400

    # Convert user_id and product_id to ObjectId
    # try:
    #     user_id = ObjectId(user_id)
    #     product_id = ObjectId(product_id)
    # except:
    #     return jsonify({'error': 'Invalid user_id or product_id format'}), 400

    # Check if product is wishlisted for the user
    print(list(db.wishlist.find()))
    wishlist_item = db.wishlist.find_one({'user_id': ObjectId(user_id), 'product_id': ObjectId(product_id)})
    if wishlist_item:
        return jsonify({'wishlist_status': True}), 200
    else:
        return jsonify({'wishlist_status': False}), 200


# Route to add an item to the cart
@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    data = request.json
    product_id = data.get('product_id')
    user_id = data.get('user_id') 
    seller = data.get('seller')
    quantity = data.get('quantity') or 1

    # Check if product exists
    product = db.products.find_one({'_id': ObjectId(product_id)})
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    # Check if the product is already in the user's cart
    existing_cart_item = db.cart.find_one({'product_id': product_id, 'user_id': user_id})
    if existing_cart_item:
        return jsonify({'error': 'Product already in cart'}), 400

    # Calculate total price
    total_price = product['price']

    # Create cart item document
    cart_item = {
        'product_id': product['_id'],
        'user_id': user_id,
        'product': product,
        'quantity': quantity,  # Default quantity is 1
        'total_price': total_price,
        'seller': seller
    }

    # Insert item into the cart
    db.cart.insert_one(cart_item)

    return jsonify({'message': 'Product added to cart', 'total_price': total_price}), 201

# Route to find cart items and total price based on user email
@app.route('/cart/<string:user_id>', methods=['GET'])
def find_cart_items(user_id):
    # Retrieve cart items for the user
    cart_items = list(db.cart.find({'user_id': user_id}))

    # Calculate total price of all products in the cart
    total_price = sum(item['product']['price'] * item['quantity'] for item in cart_items)

    # Format cart items to include product details
    formatted_cart_items = []
    for item in cart_items:
        product = item['product']
        product['quantity'] = item['quantity']
        product['_id'] = str(product['_id'])
        product['seller'] = item['seller']
        formatted_cart_items.append(product)

    return jsonify({'cart_items': formatted_cart_items, 'total_price': total_price}), 200


# Route to delete cart based on user ID
@app.route('/cart/<string:user_id>', methods=['DELETE'])
def delete_cart_by_user_id(user_id):
    result = db.cart.delete_many({'user_id': user_id})
    if result.deleted_count > 0:
        return jsonify({'message': 'Cart deleted successfully'}), 200
    else:
        return jsonify({'error': 'Cart not found for the user'}), 404

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
    result = db.users.update_one({'_id': ObjectId(user_id)}, {'$set': new_data})
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
    user = db.users.find_one({'_id': ObjectId(user_id)})
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Check if current password is correct
    if not check_password_hash(user['password'], current_password):
        return jsonify({'error': 'Current password is incorrect'}), 400

    # Hash the new password
    hashed_new_password = generate_password_hash(new_password)

    # Update user's password
    result = db.users.update_one({'_id': ObjectId(user_id)}, {'$set': {'password': hashed_new_password}})
    if result.modified_count > 0:
        return jsonify({'message': 'Password changed successfully'}), 200
    else:
        return jsonify({'error': 'Failed to change password'}), 500

# Get user information route
@app.route('/user/<string:user_id>', methods=['GET'])
def get_user(user_id):
    print(user_id)
    user = db.users.find_one({'_id': ObjectId(user_id)})
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
    users = list(db.users.find({}, {'password': 0}))  # Exclude password field
    
    for user in users:
        user['_id'] = str(user['_id'])
        
    return jsonify(users), 200



# Add order route
@app.route('/orders', methods=['POST'])
def add_order():
    data = request.json
    user_id = data.get('user_id')
    cart_items = data.get('cart_items')
    billing_details = data.get('billing_details')
    total_price = data.get('total_price')
    payment_mode = data.get('payment_mode')

    # Validate input
    if not (user_id or cart_items or billing_details):
        return jsonify({'error': 'Missing required fields'}), 400

    # Autofill order fields
    order_date = datetime.utcnow()
    status = 'not_delivered'

    # Create order document
    order_data = {
        'user_id': ObjectId(user_id),
        'cart_items': cart_items,
        'total_price': total_price,
        'order_date': order_date,
        'status': status,
        'billing_details': billing_details,
        'payment_mode': payment_mode
    }

    # Insert order into the database
    result = db.orders.insert_one(order_data)

    return jsonify({'message': 'Order added successfully', 'order_id': str(result.inserted_id)}), 201


# Route to get orders by user ID
@app.route('/orders/<string:user_id>', methods=['GET'])
def get_orders_by_user_id(user_id):
    orders = list(db.orders.find({'user_id': ObjectId(user_id)}))

    # Convert ObjectId to str for serialization
    for order in orders:
        order['_id'] = str(order['_id'])
        order['user_id'] = str(order['user_id'])

    return jsonify(orders), 200

# Sales route
@app.route('/sales', methods=['GET'])
def get_products_on_sale():
    products = list(db.products.find({'price': {'$lt': 1000}}))

    # Convert ObjectId to str for serialization
    for product in products:
        product['_id'] = str(product['_id'])

    return jsonify(products), 200


# Best selling products route
@app.route('/best-selling', methods=['GET'])
def get_best_selling_products():
    # Find products with reviews greater than 4.5
    best_selling_products = list(db.products.find({'ratings': {'$gt': 4.5}}))

    # Convert ObjectId to str for serialization
    for product in best_selling_products:
        product['_id'] = str(product['_id'])

    return jsonify(best_selling_products), 200

# Route to get products by category
@app.route('/products/category/<string:category>', methods=['GET'])
def get_products_by_category(category):
    products = list(db.products.find({'category': category}))

    # Convert ObjectId to str for serialization
    for product in products:
        product['_id'] = str(product['_id'])

    return jsonify(products), 200

# Route to send a message
@app.route('/chat/send', methods=['POST'])
def send_message():
    data = request.json
    sender_id = data.get('sender_id')
    receiver_id = data.get('receiver_id')
    message = data.get('message')

    # Validate input
    if not (sender_id and receiver_id and message):
        return jsonify({'error': 'Missing required fields'}), 400

    # Create message document
    message_data = {
        'sender_id': ObjectId(sender_id),
        'receiver_id': ObjectId(receiver_id),
        'message': message,
        'timestamp': datetime.utcnow(),
        'seen': False  # Set seen status to False by default
    }

    # Insert message into the database
    result = db.messages.insert_one(message_data)
    
    # Emit the new message to the receiver's room
    socketio.emit('new_message', {
        'sender_id': str(message_data['sender_id']),  # Convert ObjectId to string
        'receiver_id': str(message_data['receiver_id']),  # Convert ObjectId to string
        'message': message,
        'timestamp': message_data['timestamp'].isoformat(),
        'seen': False  # Initially mark the message as unseen
    })

    return jsonify({'message': 'Message sent successfully', 'message_id': str(result.inserted_id)}), 201

# Route to get messages between two users
@app.route('/chat/<string:user_id>/<string:other_user_id>', methods=['GET'])
def get_messages(user_id, other_user_id):
    # Find messages between two users
    messages = list(db.messages.find({
        '$or': [
            {'sender_id': ObjectId(user_id), 'receiver_id': ObjectId(other_user_id)},
            {'sender_id': ObjectId(other_user_id), 'receiver_id': ObjectId(user_id)}
        ]
    }).sort([('timestamp', 1)]))

    # Convert ObjectId to str for serialization
    for message in messages:
        message['_id'] = str(message['_id'])
        message['sender_id'] = str(message['sender_id'])
        message['receiver_id'] = str(message['receiver_id'])

        # Mark the message as seen if the recipient is the current user
        if str(message['receiver_id']) == user_id:
            message['seen'] = True
            db.messages.update_one({'_id': ObjectId(message['_id'])}, {'$set': {'seen': True}})
    
    return jsonify(messages), 200

# Route to fetch recent users
@app.route('/chat/recent-users/<string:user_id>', methods=['GET'])
def get_recent_users(user_id):
    try:
        # Query to fetch recent users from messages
        recent_users_from_messages_cursor = db.messages.aggregate([
            {'$match': {'$or': [{'sender_id': ObjectId(user_id)}, {'receiver_id': ObjectId(user_id)}]}},
            {'$group': {'_id': {'$cond': [{'$eq': ['$sender_id', ObjectId(user_id)]}, '$receiver_id', '$sender_id']}}},
            {'$lookup': {'from': 'users', 'localField': '_id', 'foreignField': '_id', 'as': 'user'}},
            {'$project': {'_id': 1, 'user_id': '$_id', 'user': {'$arrayElemAt': ['$user', 0]}}},
            {'$project': {'user_id': 1}}
        ])

        recent_users_from_messages = [str(user['_id']) for user in recent_users_from_messages_cursor]

        # Query to fetch recent users from orders
        recent_users_from_orders_cursor = db.orders.aggregate([
            {'$match': {'user_id': ObjectId(user_id)}},
            {'$unwind': '$cart_items'},  # Unwind to access each cart item
            {'$lookup': {'from': 'users', 'localField': 'cart_items.seller', 'foreignField': '_id', 'as': 'seller'}},
            {'$project': {'seller_id': '$cart_items.seller'}},
            {'$group': {'_id': '$seller_id'}}
        ])

        recent_users_from_orders = [str(order['_id']) for order in recent_users_from_orders_cursor]

        # Merge recent users from messages and orders
        recent_users = recent_users_from_messages + recent_users_from_orders

        return jsonify(recent_users), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Route to fetch the last recent chat
@app.route('/chat/recent/<string:user_id>/<string:chat_user_id>', methods=['GET'])
def get_last_recent_chat(user_id, chat_user_id):
    try:
        # Query to fetch the last recent chat
        last_recent_chat = db.messages.find_one(
            {'$or': [
                {'sender_id': ObjectId(user_id), 'receiver_id': ObjectId(chat_user_id)},
                {'sender_id': ObjectId(chat_user_id), 'receiver_id': ObjectId(user_id)}
            ]},
            sort=[('_id', -1)]  # Sort by _id in descending order to get the latest message
        )
        if last_recent_chat:
            last_recent_chat = {
            '_id': str(last_recent_chat['_id']),
            'sender_id': str(last_recent_chat['sender_id']),
            'receiver_id': str(last_recent_chat['receiver_id']),
            'message': last_recent_chat['message'],
            'timestamp': last_recent_chat['timestamp'].isoformat(),
            'seen': last_recent_chat['seen']  # Initially mark the message as unseen
            }
            
            return jsonify(last_recent_chat), 200
        else:
            return jsonify({'message': 'No recent chat found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    socketio.run(app, debug=True)
