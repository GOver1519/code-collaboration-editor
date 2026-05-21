#render_template is used to open html files and render them to the user
#request is used to get form data when user submits a form
#redirect and url_for are used to redirect the user to a different page after they submit a form
#flash is used to display messages to the user
#session is used to keep user logged in
from flask import Flask, render_template, request, redirect, url_for, flash, session

#database connection
from database import cursor, conn

#password hashing
import bcrypt

#random room code generation
import random
import string

#run code
import subprocess

#socketio for realtime collaboration
from flask_socketio import SocketIO, emit, join_room

import os


#---------------------------------------------------------------------------
# Flask App Setup
#---------------------------------------------------------------------------

app = Flask(__name__)

#secret key
app.secret_key = "mysecretkey"

#socketio setup
socketio = SocketIO(app)


#---------------------------------------------------------------------------
# Landing Page
#---------------------------------------------------------------------------

@app.route('/')
def landing():

    return render_template('landing.html')


#---------------------------------------------------------------------------
# Home Page
#---------------------------------------------------------------------------

@app.route('/home')
def home():

    #check login
    if 'user' not in session:

        return redirect(url_for('landing'))

    return render_template('home.html')


#---------------------------------------------------------------------------
# Logout
#---------------------------------------------------------------------------

@app.route('/logout')
def logout():

    #remove user session
    session.pop('user', None)

    return redirect(url_for('landing'))


#---------------------------------------------------------------------------
# Register
#---------------------------------------------------------------------------

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        #get form data
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        #validation
        if username == "" or email == "" or password == "" or confirm_password == "":

            flash("Please fill all fields")

            return redirect(url_for('register'))

        #password validation
        if password != confirm_password:

            flash("Passwords do not match")

            return redirect(url_for('register'))

        #check existing user
        query = """
        SELECT * FROM users
        WHERE email = %s
        """

        cursor.execute(query, (email,))

        existing_user = cursor.fetchone()

        if existing_user:

            flash("Email already exists")

            return redirect(url_for('register'))

        #hash password
        hashed_password = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        )

        #insert user
        query = """
        INSERT INTO users (username, email, password)
        VALUES (%s, %s, %s)
        """

        values = (
            username,
            email,
            hashed_password.decode('utf-8')
        )

        cursor.execute(query, values)

        conn.commit()

        #create session
        session['user'] = username

        return redirect(url_for('home'))

    return render_template('register.html')


#---------------------------------------------------------------------------
# Login
#---------------------------------------------------------------------------

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        #get form data
        email = request.form['email']
        password = request.form['password']

        #validation
        if email == "" or password == "":

            flash("Please fill all fields")

            return redirect(url_for('login'))

        #find user
        query = """
        SELECT * FROM users
        WHERE email = %s
        """

        cursor.execute(query, (email,))

        user = cursor.fetchone()

        #invalid email
        if user is None:

            flash("Invalid email")

            return redirect(url_for('login'))

        #stored password
        stored_password = user[3]

        #compare password
        password_match = bcrypt.checkpw(
            password.encode('utf-8'),
            stored_password.encode('utf-8')
        )

        #invalid password
        if not password_match:

            flash("Invalid password")

            return redirect(url_for('login'))

        #create session
        session['user'] = user[1]

        return redirect(url_for('home'))

    return render_template('login.html')


#---------------------------------------------------------------------------
# Dashboard
#---------------------------------------------------------------------------

@app.route('/dashboard')
def dashboard():

    #check login
    if 'user' not in session:

        return redirect(url_for('landing'))

    username = session['user']

    #get rooms
    query = """
    SELECT * FROM rooms
    WHERE created_by = %s
    """

    cursor.execute(query, (username,))

    rooms = cursor.fetchall()

    return render_template(
        'dashboard.html',
        rooms=rooms
    )


#---------------------------------------------------------------------------
# Create Room
#---------------------------------------------------------------------------

@app.route('/create-room', methods=['POST'])
def create_room():

    #check login
    if 'user' not in session:

        return redirect(url_for('landing'))

    #get room name
    room_name = request.form['room_name']

    #validation
    if room_name == "":

        flash("Please enter room name")

        return redirect(url_for('dashboard'))

    #generate room code
    room_code = ''.join(
        random.choices(
            string.ascii_uppercase + string.digits,
            k=6
        )
    )

    created_by = session['user']

    #insert room
    query = """
    INSERT INTO rooms (
        room_code,
        room_name,
        created_by
    )
    VALUES (%s, %s, %s)
    """

    values = (
        room_code,
        room_name,
        created_by
    )

    cursor.execute(query, values)

    conn.commit()

    flash(f"Room created successfully! Code: {room_code}")

    return redirect(url_for('dashboard'))


#---------------------------------------------------------------------------
# Join Room
#---------------------------------------------------------------------------

@app.route('/join-room', methods=['POST'])
def join_room_page():

    #check login
    if 'user' not in session:

        return redirect(url_for('landing'))

    #get room code
    room_code = request.form['room_code']

    #validation
    if room_code == "":

        flash("Please enter room code")

        return redirect(url_for('dashboard'))

    #find room
    query = """
    SELECT * FROM rooms
    WHERE room_code = %s
    """

    cursor.execute(query, (room_code,))

    room = cursor.fetchone()

    #room not found
    if room is None:

        flash("Room not found")

        return redirect(url_for('dashboard'))

    return redirect(f'/room/{room_code}')


#---------------------------------------------------------------------------
# Room Page
#---------------------------------------------------------------------------

@app.route('/room/<room_code>')
def room(room_code):

    #check login
    if 'user' not in session:

        return redirect(url_for('landing'))

    #find room
    query = """
    SELECT * FROM rooms
    WHERE room_code = %s
    """

    cursor.execute(query, (room_code,))

    room = cursor.fetchone()

    #room not found
    if room is None:

        flash("Room not found")

        return redirect(url_for('dashboard'))

    return render_template(
        'room.html',
        room=room
    )


#---------------------------------------------------------------------------
# Delete Room
#---------------------------------------------------------------------------

@app.route('/delete-room/<int:room_id>', methods=['POST'])
def delete_room(room_id):

    #check login
    if 'user' not in session:

        return redirect(url_for('landing'))

    username = session['user']

    #find room
    query = """
    SELECT * FROM rooms
    WHERE id = %s
    AND created_by = %s
    """

    cursor.execute(query, (room_id, username))

    room = cursor.fetchone()

    #room not found
    if room is None:

        flash("Room not found")

        return redirect(url_for('dashboard'))

    #delete room
    query = """
    DELETE FROM rooms
    WHERE id = %s
    """

    cursor.execute(query, (room_id,))

    conn.commit()

    flash("Room deleted successfully")

    return redirect(url_for('dashboard'))


#---------------------------------------------------------------------------
# Save Code
#---------------------------------------------------------------------------

@app.route('/save-code/<room_code>', methods=['POST'])
def save_code(room_code):

    #check login
    if 'user' not in session:

        return redirect(url_for('landing'))

    #get form data
    code = request.form['code']

    language = request.form['language']

    #update room
    query = """
    UPDATE rooms
    SET code = %s,
        language = %s
    WHERE room_code = %s
    """

    values = (
        code,
        language,
        room_code
    )

    cursor.execute(query, values)

    conn.commit()

    flash("Code saved successfully")

    return redirect(f'/room/{room_code}')


#---------------------------------------------------------------------------
# Run Code
#---------------------------------------------------------------------------

@app.route('/run-code/<room_code>', methods=['POST'])
def run_code(room_code):

    #check login
    if 'user' not in session:

        return redirect(url_for('landing'))

    #get form data
    code = request.form['code']

    language = request.form['language']

    #save current editor state
    query = """
    UPDATE rooms
    SET code = %s,
        language = %s
    WHERE room_code = %s
    """

    values = (
        code,
        language,
        room_code
    )

    cursor.execute(query, values)

    conn.commit()

    try:

        #-----------------------------------------------------------
        # Python
        #-----------------------------------------------------------

        if language == "Python":

            with open("temp.py", "w") as file:

                file.write(code)

            result = subprocess.run(
                ["python", "temp.py"],
                capture_output=True,
                text=True,
                timeout=5
            )

        #-----------------------------------------------------------
        # JavaScript
        #-----------------------------------------------------------

        elif language == "JavaScript":

            with open("temp.js", "w") as file:

                file.write(code)

            result = subprocess.run(
                ["node", "temp.js"],
                capture_output=True,
                text=True,
                timeout=5
            )

        else:

            result = None

            output = "Unsupported language"

        #store output
        if result:

            output = result.stdout

            #show errors
            if result.stderr:

                output = result.stderr

    except Exception as error:

        output = str(error)

    #fetch room again
    query = """
    SELECT * FROM rooms
    WHERE room_code = %s
    """

    cursor.execute(query, (room_code,))

    room = cursor.fetchone()

    return render_template(
        'room.html',
        room=room,
        output=output
    )


#---------------------------------------------------------------------------
# Realtime Collaboration
#---------------------------------------------------------------------------

#join websocket room
@socketio.on('join')
def on_join(data):

    room_code = data['room_code']

    join_room(room_code)

    print(f"User joined room: {room_code}")


#realtime typing
@socketio.on('code_change')
def handle_code_change(data):

    room_code = data['room_code']

    code = data['code']

    #send updated code to everyone except sender
    emit(
        'update_code',
        {'code': code},
        room=room_code,
        include_self=False
    )


#---------------------------------------------------------------------------
# Run Application
#---------------------------------------------------------------------------

if __name__ == '__main__':

    port = int(os.environ.get("PORT", 5000))

    socketio.run(
        app,
        host='0.0.0.0',
        port=port,
        debug=False
    )