import pymysql
import uuid, os, hashlib
from flask import Flask, render_template, request, redirect, session, abort, flash, jsonify
app = Flask(__name__)

# Register the setup page and import create_connection()
from utils import create_connection, setup
app.register_blueprint(setup)


# Restricted pages
@app.before_request
def restrict():
    restricted_pages = [
        'list_users',
        'view_user',
        'edit_user',
        'delete_user'

    ]
    admin_only = [
        'lists_users'
        'connection_list'
        ]

    if 'logged_in' not in session and request.endpoint in restricted_pages:
        return redirect('/login')       # Returns user to login route.


@app.route('/')
def home():
    with create_connection() as connection:
        with connection.cursor() as cursor:
            # Select all from subject_table
            cursor.execute("SELECT * FROM subject_table")
            result = cursor.fetchall()

    return render_template('index.html', result = result)           # Returns user to Index.html (Home)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':

        password = request.form['password']
        encrypted_password = hashlib.sha256(password.encode()).hexdigest()

        with create_connection() as connection:
            with connection.cursor() as cursor:

                # Selects all from user_table where email and password is unique
                sql = "SELECT * FROM users_table WHERE email=%s AND password=%s"
                values = (
                    request.form['email'],
                    encrypted_password
                )
                cursor.execute(sql, values)
                result = cursor.fetchone()
        if result:
            session['logged_in'] = True
            session['name'] = result['name']
            session['role'] = result['role']
            session['id'] = result['id']
            return redirect("/dashboard")
        else:
            flash("Invalid username or password!")

            return redirect("/login")
    else:
        return render_template('login.html')

# logout function
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# delete function
@app.route('/delete')
def delete():
    with create_connection() as connection:
        with connection.cursor() as cursor:

            # Deletes a selected row from users_table
            cursor.execute("DELETE FROM users_table WHERE id = %s", request.args['id'])
            connection.commit()
    return redirect('/dashboard')


# delete subject function
@app.route('/delete_subject')
def delete_subject():
    with create_connection() as connection:
        with connection.cursor() as cursor:

            # Deletes a selected row from connect table
            cursor.execute("DELETE FROM connect WHERE subject_id = %s AND user_id = %s", (request.args['id'], session['id']))
            connection.commit()
    return redirect(f"/view?id={session['id']}")


# edit_user route that
@app.route('/edit', methods =['GET', 'POST'])
def edit():


    if session['role'] != 'admin' and str(session['id']) != request.args['id']:
        return abort(403)                                                                   # Everyone else will receive error 403, error 403 is a forbiden error
    if request.method == 'POST':
        if request.files['avatar'].filename:
            avatar_image = request.files["avatar"]
            ext = os.path.splitext(avatar_image.filename)[1]
            avatar_filename = str(uuid.uuid4())[:8] + ext
            avatar_image.save("static/images/" + avatar_filename)
            if request.form['old_avatar'] != 'None' and os.path.exists("static/images/" + request.form['old_avatar']):
                os.remove("static/images/" + request.form['old_avatar'])
            elif request.form['old_avatar'] != 'None':
                avatar_filename = request.form['old_avatar']
            else:
                avatar_filename = None
        with create_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("""UPDATE users_table SET
                                name = %s,
                                last_name = %s,
                                email = %s,
                                avatar = %s
                              WHERE id = %s
                                """

                                ,(
                     request.form['name'],
                     request.form['last_name'],
                     request.form['email'],
                     avatar_filename,
                     request.form['id'])
                    )




                connection.commit()
            return redirect('/')
        return 'success'
    else:
        with create_connection() as connection:
            with connection.cursor() as cursor:

                # selects all from users_table where id is unique
                sql = "SELECT * FROM users_table WHERE id = %s"
                values = (request.args['id'])
                cursor.execute(sql, values)
                result = cursor.fetchone()
        return render_template('edit.html', result=result)              # returns user to edit.html

# Admin user dashboard route
@app.route('/dashboard')
def list_users():
    if session['role'] != 'admin':
        return redirect('/')
    with create_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM users_table")         # selects all from users_table
            result = cursor.fetchall()
    return render_template('connection_list.html', result=result)        # returns user to connection_list.html


# Registration route
@app.route('/register', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':

        # Encrypts password with sha256, which is 64bit
        password = request.form['password']
        encrypted_password = hashlib.sha256(password.encode()).hexdigest()

        # Encoded file Names (Purpose of making unique names so Python doesn't have errors)
        if request.files['avatar'].filename:
            avatar_image = request.files["avatar"]
            ext = os.path.splitext(avatar_image.filename)[1]
            avatar_filename = str(uuid.uuid4())[:8] + ext
            avatar_image.save("static/images/" + avatar_filename)
        else:
            avatar_filename = None

        with create_connection() as connection:
            with connection.cursor() as cursor:
                try:
                    # Inserts values into the users_table to create the user.
                    cursor.execute("INSERT INTO users_table (name, last_name, DOB, year_level, house, email, password, avatar) VALUE (%s, %s, %s, %s, %s, %s, %s, %s)", (
                        request.form['name'], request.form['last_name'], request.form['DOB'], request.form['year_level'], request.form['house'], request.form['email'], encrypted_password, avatar_filename))
                except pymysql.err.IntegrityError:
                    flash("example")
                    return redirect('/register')

                connection.commit()
            return redirect('/')
        return 'success'
    else:
        return render_template('users_add.html')            # returns user to user_add.html

# Selection route
@app.route('/select', methods=['GET', 'POST'])
def select():
    with create_connection() as connection:
        with connection.cursor() as cursor:

            # prints out the number of subjects selected
            cursor.execute("SELECT * FROM connect WHERE user_id = %s", session['id'])
            result = cursor.fetchall()
            print(len(result))

            if (len(result)) == 5:              # If user has five subjects don't add anymore.
                 flash("You reached your limit of selected subjects")

            elif (len(result)) >= 5:              # If user has five subjects don't add anymore.
                 flash("You already reached your limit of selected subjects")

            else:
               # Inserts values into connect table for subjects selected
                cursor.execute("INSERT INTO connect (user_id, subject_id) VALUES (%s, %s)", (session['id'], request.args['id']))
                connection.commit()
    return redirect('/dashboard')       # returns user to /dashboard route


# ADD SUBJECT FROM USER
@app.route('/add_subject', methods=['GET', 'POST'])
def add_movie():
    if request.method == 'POST':

        with create_connection() as connection:
            with connection.cursor() as cursor:
                try:
                    # Inserts values into subject_table to create subject.
                    cursor.execute("INSERT INTO subject_table (subject_name, period, subject_code) VALUES (%s, %s, %s)", (
                        request.form['subject_name'], request.form['period'], request.form['subject_code']))
                except pymysql.err.IntegrityError:
                    flash("example")
                    return redirect('/register')

                connection.commit()

                # User can select a subject (subject_name) from subject_table
                cursor.execute("SELECT * FROM subject_table WHERE subject_name = %s", request.form['subject_name'])
                result = cursor.fetchone()
                subject_id = result['id']

                # Inserts values into connect to save and store it into database.
                cursor.execute("INSERT INTO connect (user_id, subject_id) VALUES (%s, %s)", (request.args['id'], subject_id))
                connection.commit()
            return redirect('/')
        return 'success'

    else:
        return render_template('add_subject.html')       # returns user to add_subject.html

# VIEW USER ROUTE
@app.route('/view')
def view_user():
    with create_connection() as connection:
        with connection.cursor() as cursor:

            # Selects all from users_table
            cursor.execute("SELECT * FROM users_table WHERE id=%s", request.args['id'])
            result = cursor.fetchone()

            # This make the users_table and subject_table connect together
            cursor.execute("select * from lianaidoo_subject.users_table join connect on connect.user_id = users_table.id join subject_table on subject_table.id = connect.subject_id WHERE users_table.id=%s", request.args['id'])
            result = cursor.fetchall()
            print(result)
    return render_template('users_view.html', result=result)                   # returns user to users_view.html


# Unique route
@app.route('/checkemail')
def check_email():
    with create_connection() as connection:
            with connection.cursor() as cursor:

                # Selects all from users_table where email is unique
                sql = "SELECT * FROM users_table WHERE email=%s"
                values = (
                    request.args['email'],
                )
                cursor.execute(sql, values)
                result = cursor.fetchone()
    if result:
        return jsonify({'status': 'Error'})
    else:
        return jsonify({'status': 'OK'})

if __name__ == '__main__':
    import os

    # This is required to allow sessions.
    app.secret_key = os.urandom(32)

    HOST = os.environ.get('SERVER_HOST', 'localhost')
    try:
        PORT = int(os.environ.get('SERVER_PORT', '5555'))
    except ValueError:
        PORT = 5555
    app.run(HOST, PORT, debug=True)
