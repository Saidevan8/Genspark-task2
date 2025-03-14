from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import MySQLdb.cursors

app = Flask(__name__)
app.secret_key = 'your_secret_key'
BASE_URL = "https://your-app-name.onrender.com"
# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'expense_tracker'
mysql = MySQL(app)

# Flask-Login Configuration
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# Routes
@app.route('/')
def index():  
    return render_template('index.html',BASE_URL=BASE_URL)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('INSERT INTO users (username, password) VALUES (%s, %s)', (username, password))
        mysql.connection.commit()
        flash('Signup successful! Please login.')
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE username = %s AND password = %s', (username, password))
        user = cursor.fetchone()
        if user:
            login_user(User(user['id']))
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials!')
    return render_template('login.html')

@app.route('/analytics')
@login_required
def analytics():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # Total expenses
    cursor.execute('SELECT SUM(amount) as total FROM expenses WHERE user_id = %s', (current_user.id,))
    total_expenses = cursor.fetchone()['total']
    
    # Category-wise expenses
    cursor.execute('SELECT category, SUM(amount) as total FROM expenses WHERE user_id = %s GROUP BY category', (current_user.id,))
    category_expenses = cursor.fetchall()
    
    return render_template('analytics.html', total_expenses=total_expenses, category_expenses=category_expenses)

@app.route('/dashboard')
@login_required
def dashboard():
    username = session.get('username')
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM expenses WHERE user_id = %s', (current_user.id,))
    expenses = cursor.fetchall()
    return render_template('dashboard.html', username=username, expenses=expenses)

@app.route('/add_expense', methods=['POST'])
@login_required
def add_expense():
    title = request.form['title']
    amount = request.form['amount']
    category = request.form['category']
    date = request.form['date']
    cursor = mysql.connection.cursor()
    cursor.execute('INSERT INTO expenses (user_id, title, amount, category, date) VALUES (%s, %s, %s, %s, %s)',
                   (current_user.id, title, amount, category, date))
    mysql.connection.commit()
    flash('Expense added successfully!')
    return redirect(url_for('dashboard'))

@app.route('/delete_expense/<int:id>', methods=['POST'])
@login_required
def delete_expense(id):
    cursor = mysql.connection.cursor()
    cursor.execute('DELETE FROM expenses WHERE id = %s', (id,))
    mysql.connection.commit()
    flash('Expense deleted successfully!')
    return redirect(url_for('dashboard'))

@app.route('/update_expense/<int:id>', methods=['GET', 'POST'])
@login_required
def update_expense(id):
    if request.method == 'POST':
        title = request.form['title']
        amount = request.form['amount']
        category = request.form['category']
        date = request.form['date']
        cursor = mysql.connection.cursor()
        cursor.execute('''
            UPDATE expenses
            SET title = %s, amount = %s, category = %s, date = %s
            WHERE id = %s AND user_id = %s
        ''', (title, amount, category, date, id, current_user.id))
        mysql.connection.commit()
        flash('Expense updated successfully!')
        return redirect(url_for('dashboard'))
    # Fetch the expense to pre-fill the form
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM expenses WHERE id = %s AND user_id = %s', (id, current_user.id))
    expense = cursor.fetchone()
    return render_template('update_expense.html', expense=expense)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('username', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=False)
