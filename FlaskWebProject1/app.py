import pymysql
import uuid, os, hashlib
from flask import Flask, render_template, request, redirect, session, abort, flash, jsonify
app = Flask(__name__)

# Register the setup page and import create_connection()
from utils import create_connection, setup
app.register_blueprint(setup)


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
        return redirect('/login')

@app.route('/')
def home():
    return render_template('index.html')






# TODO: Add a '/profile' (view_user) route that uses SELECT


# TODO: Add a '/delete_user' route that uses DELETE

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':

        password = request.form['password']
        encrypted_password = hashlib.sha256(password.encode()).hexdigest()

        with create_connection() as connection:
            with connection.cursor() as cursor:
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
            session['id'] = result['idusers_table']
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
            cursor.execute("DELETE FROM users_table WHERE id = %s", request.args['id'])
            connection.commit()
    return redirect('/dashboard')



# TODO: Add an '/edit_user' route that uses UPDATE
@app.route('/edit', methods =['GET','POST'])
def edit():
    # admin users with the right id are allowed,
    # Everyone else will receive error 404 
    if session['role'] != 'admin' and str(session['id']) != request.args['id']:
        return abort(403)
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
                         # Add this row
                    )




                connection.commit()
            return redirect('/')
        return 'success'
    else:
        with create_connection() as connection:
            with connection.cursor() as cursor:
                sql = "SELECT * FROM users_table WHERE id = %s"
                values = (request.args['id'])
                cursor.execute(sql,values)
                result = cursor.fetchone()
        return render_template('edit.html', result=result)

# Admin user dashboard route 
@app.route('/dashboard')
def list_users():
    if session['role'] != 'admin':
        return redirect('/')
    with create_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM users_table") # selects all from users table in lianaidoo_subject
            result = cursor.fetchall()
    return render_template('connection_list.html',result=result) # returns an html page to get something in the table

# add_user route
@app.route('/register', methods=['GET', 'POST'] )
def add():
    if request.method == 'POST':

        password = request.form['password']
        encrypted_password = hashlib.sha256(password.encode()).hexdigest()

        
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
                    cursor.execute("INSERT INTO users_table (name, last_name, DOB, year_level, house, email, password, avatar) VALUE (%s, %s, %s, %s, %s, %s, %s, %s)",(
                        request.form['name'],request.form['last_name'],request.form['DOB'],request.form['year_level'],request.form['house'], request.form['email'], encrypted_password, avatar_filename))
                except pymysql.err.IntegrityError:
                    flash("example")
                    return redirect('/register')

                connection.commit()
            return redirect('/')
        return 'success'
    else:
        return render_template('users_add.html')




# ADD SUBJECT FROM USER
@app.route('/add_subject', methods=['GET', 'POST'] )
def add_movie():
    if request.method == 'POST':

        with create_connection() as connection:
            with connection.cursor() as cursor:
                try:
                    cursor.execute("INSERT INTO subeject_table (subject_name, period, subject_code,) VALUES (%s, %s, %s)",(
                        request.form['subject_name'],request.form['period'], request.form['subject_code']))
                except pymysql.err.IntegrityError:
                    flash("example")
                    return redirect('/register')

                connection.commit()
                cursor.execute("SELECT * FROM subject_table WHERE subject_name = %s", request.form['subject_name'])
                result = cursor.fetchone()
                subject_id = result['id_subject']

                cursor.execute("INSERT INTO connect (user_id, subject_id) VALUES (%s, %s)",(request.args['id'], subject_id))
                connection.commit()
            return redirect('/')
        return 'success'
    else:
        return render_template('add_subject.html')


@app.route('/view')
def view_user():
    with create_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM users_table WHERE id=%s", request.args['id'])
            result = cursor.fetchone()
            cursor.execute("select * from lianaidoo_subject.users_table join connect on connect.user_id = users_table.id join movie_table on movie_table.idmovie_table = connect.movie_id WHERE users_table.id=%s", request.args['id'])
            result = cursor.fetchall()
            
    return render_template('users_view.html', result=result)


@app.route ('/checkemail')
def check_email():
    with create_connection() as connection:
            with connection.cursor() as cursor:
                sql = "SELECT * FROM users_table WHERE email=%s"
                values = (
                    request.args['email'],
                )
                cursor.execute(sql, values)
                result = cursor.fetchone()
    if result:
        return jsonify({'status':'Error'})
    else:
         return jsonify({'status':'OK'})





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
