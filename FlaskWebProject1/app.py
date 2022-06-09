import pymysql
import uuid, os, hashlib
from flask import Flask, render_template, request, redirect, session, abort, flash, jsonify
app = Flask(__name__)

# Register the setup page and import create_connection()
from utils import create_connection, setup
app.register_blueprint(setup)


# Make the WSGI interface available at the top level so wfastcgi can get it.
wsgi_app = app.wsgi_app


# ADD Restriction


@app.route('/')
def home():
    return render_template('index.html')



#ADD edit function

#ADD delete function

#ADD edit function

# ADD logout function

# ADD Information




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
