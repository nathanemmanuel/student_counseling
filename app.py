from flask import Flask, render_template, request
from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_mysqldb import MySQL
from werkzeug.utils import redirect
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo
from email_validator import validate_email, EmailNotValidError
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import mysql.connector

# Add this section at the top of your code, above the app creation
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'student_counseling'
}


app = Flask(__name__)

app.config['SECRET_KEY'] = 'your-secret-key'

app.secret_key = 'some_random_data'

app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_USER']='root'
app.config['MYSQL_PASSWORD']=''
app.config['MYSQL_DB']='student_counseling'

mysql=MySQL(app)
@app.route('/favicon.ico')
def favicon():
    # Return an empty response or a custom 404 page
    return '', 404


login_manager = LoginManager()
login_manager.init_app(app)

# User model for Flask-Login
class User(UserMixin):
    def __init__(self, user_id, first_name, last_name, email, role):
        self.id = user_id
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.role = role

# Login form using Flask-WTF
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])

# User registration form using Flask-WTF
class RegistrationForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[('student', 'Student'), ('counselor', 'Counselor')])

@login_manager.user_loader
def load_user(user_id):
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()

    select_query = "SELECT user_id, first_name, last_name, email, role FROM Users WHERE user_id = %s"
    cursor.execute(select_query, (user_id,))
    user = cursor.fetchone()

    cursor.close()
    connection.close()

    if user:
        return User(user[0], user[1], user[2], user[3], user[4])

# User registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get form data from request
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = request.form['password']

        # Connect to the database
        cur = mysql.connection.cursor()

        # Execute the query to insert user data into the database
        cur.execute(
            "INSERT INTO users (first_name, last_name, email, password) VALUES (%s, %s, %s, %s)",
            (first_name, last_name, email, password)
        )

        # Commit changes to the database
        mysql.connection.commit()

        # Close the cursor
        cur.close()

        # Redirect to a success page or login page
        return "Registration successful!"

    return render_template('register.html')

# User login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        select_query = "SELECT user_id, first_name, last_name, email, role, password_hash FROM Users WHERE email = %s"
        cursor.execute(select_query, (form.email.data,))
        user = cursor.fetchone()

        cursor.close()
        connection.close()

        if user and form.password.data == user[5]:
            user_obj = User(user[0], user[1], user[2], user[3], user[4])
            login_user(user_obj)
            return redirect(url_for('dashboard'))

    return render_template('login.html', form=form)

# User logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# User dashboard route
@app.route('/dashboard')
@login_required
def dashboard():
    user_id = current_user.id  # Assuming you have access to the current logged-in user object
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()

    select_query = "SELECT user_id, first_name, last_name, email, role FROM Users WHERE user_id = %s"
    cursor.execute(select_query, (user_id,))
    user = cursor.fetchone()

    cursor.close()
    connection.close()

    if user:
        user_data = {
            "user_id": user[0],
            "first_name": user[1],
            "last_name": user[2],
            "email": user[3],
            "role": user[4]
        }
        return jsonify(user_data)
    else:
        return jsonify({"message": "User not found"}), 404

# User profile update route
@app.route('/profile', methods=['PUT'])
@login_required
def update_profile():
    user_id = current_user.id  # Assuming you have access to the current logged-in user object
    data = request.get_json()
    first_name = data['first_name']
    last_name = data['last_name']
    email = data['email']

    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()

    update_query = "UPDATE Users SET first_name = %s, last_name = %s, email = %s WHERE user_id = %s"
    cursor.execute(update_query, (first_name, last_name, email, user_id))
    connection.commit()

    cursor.close()
    connection.close()

    return jsonify({"message": "Profile updated successfully"})

# User deletion route
@app.route('/users/<int:user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    if user_id != current_user.id:
        return jsonify({"message": "You are not authorized to delete this user"}), 403

    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()

    delete_query = "DELETE FROM Users WHERE user_id = %s"
    cursor.execute(delete_query, (user_id,))
    connection.commit()

    cursor.close()
    connection.close()

    return jsonify({"message": "User deleted successfully"})
if __name__ == '__main__':
    app.run(debug=True)
    app.debug = True