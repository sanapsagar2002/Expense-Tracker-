from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
from config import Config
import MySQLdb.cursors
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config.from_object(Config)

mysql = MySQL(app)
bcrypt = Bcrypt(app)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cursor.fetchone()
        
        if user and bcrypt.check_password_hash(user['password_hash'], password):
            session['loggedin'] = True
            session['id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        
        cursor = mysql.connection.cursor()
        cursor.execute('INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)',
                       (username, email, password_hash))
        mysql.connection.commit()
        flash('You are now registered and can log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/dashboard')
def dashboard():
    if 'loggedin' in session:
        return render_template('dashboard.html', username=session['username'])
    return redirect(url_for('login'))
'''
@app.route('/add_expense', methods=['GET', 'POST'])
def add_expense():
    if 'loggedin' in session:
        if request.method == 'POST':
            item = request.form['item']
            cost = request.form['cost']
            expense_date = request.form['expense_date']
            cursor = mysql.connection.cursor()
            cursor.execute('INSERT INTO expenses (user_id, item, cost, expense_date) VALUES (%s, %s, %s, %s)',
                           (session['id'], item, cost, expense_date))
            mysql.connection.commit()
            flash('Expense added successfully', 'success')
            return redirect(url_for('dashboard'))
        return render_template('add_expense.html')
    return redirect(url_for('login'))
'''
@app.route('/add_expense', methods=['GET', 'POST'])
def add_expense():
    if 'loggedin' in session:
        if request.method == 'POST':
            item = request.form['item']
            cost = float(request.form['cost'])  # Ensure cost is treated as a float
            expense_date = request.form['expense_date']  # Date of the expense
            
            # Check if expense exceeds the daily, monthly, or yearly budget
            period = determine_period(expense_date)  # Function to determine if it's daily, monthly, or yearly
            budget_overage = check_budget_overage(cost, period)
            
            if budget_overage:
                flash(f'{budget_overage.capitalize()} budget is over! Please minimize your expenses or update your {budget_overage} budget.', 'warning')
                return redirect(url_for('update_budget', period=budget_overage))  # Redirect to update the specific budget

            # Proceed with adding expense if within budget
            cursor = mysql.connection.cursor()
            cursor.execute('INSERT INTO expenses (user_id, item, cost, expense_date) VALUES (%s, %s, %s, %s)',
                           (session['id'], item, cost, expense_date))
            mysql.connection.commit()
            flash('Expense added successfully', 'success')
            return redirect(url_for('dashboard'))
        return render_template('add_expense.html')
    
    return redirect(url_for('login'))

def determine_period(expense_date):
    # You can use logic to determine whether it's a daily, monthly, or yearly expense
    # For simplicity, assuming you return 'daily', 'monthly', or 'yearly' based on expense date
    # Example logic:
    from datetime import datetime
    expense_date_obj = datetime.strptime(expense_date, '%Y-%m-%d')
    today = datetime.now()
    
    if expense_date_obj.date() == today.date():
        return 'daily'
    elif expense_date_obj.month == today.month and expense_date_obj.year == today.year:
        return 'monthly'
    elif expense_date_obj.year == today.year:
        return 'yearly'
    return None

def check_budget_overage(expense, period):
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT daily_budget, monthly_budget, yearly_budget FROM budgets WHERE user_id = %s', (session['id'],))
    budget = cursor.fetchone()  # Fetches the first result as a tuple
    
    # Accessing the values in the tuple using indices (0 for daily, 1 for monthly, 2 for yearly)
    daily_budget = budget[0]
    monthly_budget = budget[1]
    yearly_budget = budget[2]
    
    if period == 'daily' and expense > daily_budget:
        return 'daily'
    elif period == 'monthly' and expense > monthly_budget:
        return 'monthly'
    elif period == 'yearly' and expense > yearly_budget:
        return 'yearly'
    return None













@app.route('/manage_expense')
def manage_expense():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM expenses WHERE user_id = %s', (session['id'],))
        expenses = cursor.fetchall()
        return render_template('manage_expense.html', expenses=expenses)
    return redirect(url_for('login'))

@app.template_filter('strftime')
def format_datetime(value, format='%Y-%m-%d'):
    return value.strftime(format)


@app.route('/edit_expense/<int:id>', methods=['GET', 'POST'])
def edit_expense(id):
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM expenses WHERE id = %s AND user_id = %s', (id, session['id']))
        expense = cursor.fetchone()
        
        if request.method == 'POST':
            item = request.form['item']
            cost = request.form['cost']
            expense_date = request.form['expense_date']
            cursor.execute('UPDATE expenses SET item = %s, cost = %s, expense_date = %s WHERE id = %s',
                           (item, cost, expense_date, id))
            mysql.connection.commit()
            flash('Expense updated successfully', 'success')
            return redirect(url_for('manage_expense'))
        
        # Format the date in the correct format before passing it to the template
        if expense:
            if isinstance(expense['expense_date'], datetime):
                expense['expense_date'] = expense['expense_date'].strftime('%Y-%m-%d')
        
        return render_template('edit_expense.html', expense=expense)
    return redirect(url_for('login'))


@app.route('/delete_expense/<int:id>')
def delete_expense(id):
    if 'loggedin' in session:
        cursor = mysql.connection.cursor()
        cursor.execute('DELETE FROM expenses WHERE id = %s AND user_id = %s', (id, session['id']))
        mysql.connection.commit()
        flash('Expense deleted successfully', 'success')
        return redirect(url_for('manage_expense'))
    return redirect(url_for('login'))


@app.route('/report', methods=['GET', 'POST'])
def report():
    if request.method == 'POST':
        # Get filter parameters
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        period = request.form.get('period')  # daywise, monthwise, yearwise

        # SQL query based on period
        if period == 'daywise':
            query = 'SELECT DATE(expense_date) AS date, item, cost FROM expenses WHERE expense_date BETWEEN %s AND %s'
        elif period == 'monthwise':
            query = 'SELECT DATE_FORMAT(expense_date, "%%Y-%%m") AS month, item, SUM(cost) AS total_cost FROM expenses WHERE expense_date BETWEEN %s AND %s GROUP BY month, item'
        elif period == 'yearwise':
            query = 'SELECT DATE_FORMAT(expense_date, "%%Y") AS year, item, SUM(cost) AS total_cost FROM expenses WHERE expense_date BETWEEN %s AND %s GROUP BY year, item'

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(query, (start_date, end_date))
        expenses = cursor.fetchall()

        # Prepare data for pie chart
        labels = [expense['item'] for expense in expenses]
        data = [expense['cost'] for expense in expenses] if period == 'daywise' else [expense['total_cost'] for expense in expenses]

        return render_template('report.html', expenses=expenses, labels=labels, data=data)

    # Default values when the page is loaded without form submission
    return render_template('report.html', expenses=[], labels=[], data=[])


from werkzeug.security import generate_password_hash

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cursor.fetchone()

        if user:
            return redirect(url_for('reset_password', email=email))  # Redirect to reset password page
        else:
            flash('Email not found', 'danger')
    
    return render_template('forgot_password.html')

'''
@app.route('/reset_password/<email>', methods=['GET', 'POST'])
def reset_password(email):
    if request.method == 'POST':
        new_password = request.form['password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('reset_password.html', email=email)

        # Hash the new password
        hashed_password = generate_password_hash(new_password)

        # Update password in the database (set in `update_password` column)
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('UPDATE users SET update_password = %s WHERE email = %s', (hashed_password, email))
        mysql.connection.commit()

        flash('Password has been successfully updated', 'success')
        return redirect(url_for('login'))

    return render_template('reset_password.html', email=email)

'''
@app.route('/reset_password/<email>', methods=['GET', 'POST'])
def reset_password(email):
    if request.method == 'POST':
        print("POST request received")  # Debugging step to ensure POST request is received
        new_password = request.form['password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('reset_password.html', email=email)

        # Hash the new password
        hashed_password = generate_password_hash(new_password)

        # Update password in the database (set in `update_password` column)
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('UPDATE users SET update_password = %s WHERE email = %s', (hashed_password, email))
        mysql.connection.commit()

        flash('Password has been successfully updated', 'success')
        return redirect(url_for('login'))

    return render_template('reset_password.html', email=email)

'''
@app.route('/set_budget', methods=['GET', 'POST'])
def set_budget():
    if 'loggedin' in session:
        if request.method == 'POST':
            budget = request.form['budget']
            month = request.form['month']
            year = request.form['year']
            cursor = mysql.connection.cursor()
            cursor.execute('INSERT INTO budgets (user_id, budget, month, year) VALUES (%s, %s, %s, %s)',
                           (session['id'], budget, month, year))
            mysql.connection.commit()
            flash('Budget set successfully', 'success')
            return redirect(url_for('dashboard'))
        return render_template('set_budget.html')
    return redirect(url_for('login'))
'''

@app.route('/set_budget', methods=['GET', 'POST'])
def set_budget():
    if 'loggedin' in session:
        if request.method == 'POST':
            daily_budget = request.form['daily_budget']
            monthly_budget = request.form['monthly_budget']
            yearly_budget = request.form['yearly_budget']

            cursor = mysql.connection.cursor()
            cursor.execute('INSERT INTO budgets (user_id, daily_budget, monthly_budget, yearly_budget) VALUES (%s, %s, %s, %s)',
                           (session['id'], daily_budget, monthly_budget, yearly_budget))
            mysql.connection.commit()
            flash('Budget set successfully', 'success')
            return redirect(url_for('dashboard'))
        return render_template('set_budget.html')
    return redirect(url_for('login'))
'''
def check_budget_overage(expense, period):
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT daily_budget, monthly_budget, yearly_budget FROM budgets WHERE user_id = %s', (session['id'],))
    budget = cursor.fetchone()
    
    if period == 'daily' and expense > budget['daily_budget']:
        return 'daily'
    elif period == 'monthly' and expense > budget['monthly_budget']:
        return 'monthly'
    elif period == 'yearly' and expense > budget['yearly_budget']:
        return 'yearly'
    return None
'''

@app.route('/update_budget/<period>', methods=['GET', 'POST'])
def update_budget(period):
    if 'loggedin' in session:
        if request.method == 'POST':
            new_budget = request.form['new_budget']
            
            cursor = mysql.connection.cursor()
            if period == 'daily':
                cursor.execute('UPDATE budgets SET daily_budget = %s WHERE user_id = %s', (new_budget, session['id']))
            elif period == 'monthly':
                cursor.execute('UPDATE budgets SET monthly_budget = %s WHERE user_id = %s', (new_budget, session['id']))
            elif period == 'yearly':
                cursor.execute('UPDATE budgets SET yearly_budget = %s WHERE user_id = %s', (new_budget, session['id']))
            
            mysql.connection.commit()
            flash(f'{period.capitalize()} budget updated successfully', 'success')
            return redirect(url_for('dashboard'))
        
        return render_template('update_budget.html', period=period)
    return redirect(url_for('login'))


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
