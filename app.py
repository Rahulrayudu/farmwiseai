from flask import Flask, request, jsonify, render_template, session, make_response
from flask_mysqldb import MySQL
from datetime import datetime, timedelta
from functools import wraps
import jwt
import os

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'farmai'

mysql = MySQL(app)

# Token verification decorator
def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.args.get('token')
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token!'}), 401

        return f(*args, **kwargs)

    return decorated_function

# Routes
@app.route('/')
def home():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        return 'Logged in currently'

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    if username and password == '123456':  # Replace with actual password verification
        session['logged_in'] = True
        token = jwt.encode({
            'user': username,
            'expiration': str(datetime.utcnow() + timedelta(seconds=60))
        }, app.config['SECRET_KEY'], algorithm='HS256')
        return jsonify({'token': token}), 201
    else:
        return make_response('Unable to verify', 403, {'WWW-Authenticate': 'Basic realm="Authentication Failed"'})


# Insert data into the database
@app.route('/insert_data', methods=['POST'])
@token_required
def insert_data():
    try:
        data = request.get_json()
        book_title = data['title']
        book_author = data['author']
        book_isbn = data['isbn']
        book_price = data['price']
        book_quantity = data['quantity']

        cursor = mysql.connection.cursor()
        cursor.execute(
            'INSERT INTO books (title, author, isbn, price, quantity) VALUES (%s, %s, %s, %s, %s)',
            (book_title, book_author, book_isbn, book_price, book_quantity)
        )
        mysql.connection.commit()
        cursor.close()

        return jsonify({'message': 'Data inserted successfully'})
    except Exception as e:
        return jsonify({'message': f'Error inserting data: {str(e)}'}), 500

# Retrieve all books from the database
@app.route('/get_all_books')
def get_all_books():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM books')
        books = cursor.fetchall()
        cursor.close()

        book_list = [{'id': book[0], 'title': book[1], 'author': book[2], 'isbn': book[3], 'price': book[4], 'quantity': book[5]}
                     for book in books]
        return jsonify({'books': book_list})
    except Exception as e:
        return jsonify({'message': f'Error retrieving books: {str(e)}'}), 500

# Retrieve a specific book by ISBN
@app.route('/get_book_by_isbn/<string:isbn>')
def get_book_by_isbn(isbn):
    try:
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM books WHERE isbn=%s', (isbn,))
        book = cursor.fetchone()
        cursor.close()

        if book:
            book_data = {'id': book[0], 'title': book[1], 'author': book[2], 'isbn': book[3], 'price': book[4], 'quantity': book[5]}
            return jsonify({'book': book_data})
        else:
            return jsonify({'message': 'Book not found'}), 404
    except Exception as e:
        return jsonify({'message': f'Error retrieving book: {str(e)}'}), 500

@app.route('/update_book/<string:isbn>', methods=['PUT'])
@token_required
def update_book(isbn):
    try:
        data = request.get_json()
        updated_title = data['title']
        updated_author = data['author']
        updated_price = data['price']
        updated_quantity = data['quantity']

        cursor = mysql.connection.cursor()
        cursor.execute(
            'UPDATE books SET title=%s, author=%s, price=%s, quantity=%s WHERE isbn=%s',
            (updated_title, updated_author, updated_price, updated_quantity, isbn)
        )
        mysql.connection.commit()
        cursor.close()

        return jsonify({'message': 'Book updated successfully'})
    except Exception as e:
        return jsonify({'message': f'Error updating book: {str(e)}'}), 500

# Delete a book from the database
@app.route('/delete_book/<string:isbn>', methods=['DELETE'])
@token_required
def delete_book(isbn):
    try:
        cursor = mysql.connection.cursor()
        cursor.execute('DELETE FROM books WHERE isbn=%s', (isbn,))
        mysql.connection.commit()
        cursor.close()

        return jsonify({'message': 'Book deleted successfully'})
    except Exception as e:
        return jsonify({'message': f'Error deleting book: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)
