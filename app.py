from flask import Flask, render_template, redirect, request, flash, redirect, url_for, session
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'Bobby'
#path and filename for the database
DATABASE = "musicsheethub.db"

# Configurations for file uploads
UPLOAD_FILES = 'static/files'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
MAX_CONTENT_LENGTH = 5 * 1024 * 1024 #5MB limit

app.config['UPLOAD_FILES'] = UPLOAD_FILES
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Helper function to check if a file is allowed based on extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# function to automatically connect and query
def query_db(sql, args=(), one=False):
    '''connect and query-will return one item if one=true and can accept arguments as tuple'''
    # Connect to the database file
    db = sqlite3.connect(DATABASE)
    # create the cursor
    cursor = db.cursor()
    # excute the query
    cursor.execute(sql, args)
    # fetch all the results of the query
    results = cursor.fetchall()
    # save the data
    db.commit()
    # close the database
    db.close()
    # return None if there is no result from the query
    # return the first item only if one=True
    # return the list of tuples if one=False
    return(results[0] if results else None) if one else results


#route go here
@app.route("/home")
def home():
    return render_template('home.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm = request.form.get('confirmpassword')

        if password != confirm:
            flash('Password do not match.', 'danger')
            return redirect(url_for('signup'))
        
        try:
            connect = sqlite3.connect(DATABASE)
            cursor = connect.cursor()
            cursor.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)', (username, email, password))
            connect.commit()
            flash('Account created!Please log in.', 'success')
        except sqlite3.IntegrityError:
            flash('Username already exists.', 'danger')
        finally:
            connect.close()

        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST']) 
def login():
    if 'username' in session:
        flash('You are already logged in.', 'warning')
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        connect = sqlite3.connect(DATABASE)
        cursor = connect.cursor()
        cursor.execute('SELECT password from Users where username = ?', (username, ))
        row = cursor.fetchone()

        if row and row[0] == password:
            session['username'] = username
            flash("Login success", 'success')

            return redirect('home')
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html')


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    active_tab = request.args.get('tab', 'account')
    username = session['username']

    connect = sqlite3.connect(DATABASE)
    cursor = connect.cursor()

    cursor.execute("SELECT id FROM users WHERE username=?", (username, ))
    user_id = str(cursor.fetchone())

    if request.method == 'POST':
        form_type = request.form.get('form_type')
        if form_type == 'profile_update':
            new_email = request.form.get('email')
            if new_email:
                cursor.execute("UPDATE users SET email = ? WHERE username = ?", (new_email, username))
                flash("Email updated.", "success")
        
        elif form_type == 'change_password':
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')

            cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            if not row:
                flash("User not found.", "danger")
            elif row[0] != current_password:
                flash("Current password is incorrect.", "danger")
            elif new_password != confirm_password:
                flash("New passwords do not match.", "danger")
            else:
                cursor.execute("Update users SET password = ? WHERE username = ?", (new_password, username))
                connect.commit()
                flash("Password updated successfully.", "success")

            return redirect(url_for('profile', tab='account'))
        
        elif form_type == 'upload_sheet':
            file = request.files.get('file')
            sheetname = request.form.get('sheetname')
            composer = request.form.get('composer')
            instrument = request.form.get('instrument')

            if file and allowed_file(file.filename):
                filename = f"{username}_{secure_filename(file.filename)}"
                filepath = os.path.join(app.config['UPLOAD_FILES'], filename)
                file.save(filepath)

                cursor.execute("INSERT INTO sheets (sheetname, file_path, composer, instrument, uploader_id) VALUES (?, ?, ?, ?,?)", 
                               (sheetname, filename, composer, instrument, user_id))
                connect.commit()
                flash('Sheet uploaded successfully.', 'success')
            else:
                flash('Invalid file type.', 'danger')

            return redirect(url_for('profile', tab='sheets'))

    # load user email information
    cursor.execute("SELECT email from users WHERE username = ?", (username,))
    row = cursor.fetchone()
    email = row[0] if row else ''

    # Load user sheets if viewing sheets tab
    sheets = []
    if active_tab == 'sheets':
        cursor.execute("SELECT id, sheetname, file_path, composer, instrument, created_at FROM sheets WHERE uploader_id = ? ORDER BY created_at DESC", (user_id, ))
        sheets = cursor.fetchall()

    return render_template('profile.html', tab=active_tab, username=username, email=email, sheets=sheets)


@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out', 'warning')
    return render_template('home.html')

@app.route('/sheet')
def sheet():
    return render_template('sheet.html')

@app.route('/composer')
def composer():
    return render_template('composer.html')

@app.route('/search')
def search():
    return render_template('search.html')

@app.route('/upload')
def upload():
    return render_template('upload.html')

@app.route('/download')
def download():
    return render_template('download.html')




@app.route("/")
def index():
    sql = "SELECT * FROM Sheets"
    results = query_db(sql)
    return render_template('index.html', results=results)


@app.route('/add_sheets', methods=['GET','POST'])
def add_sheets():
    # get the form data from the request object
    sheetname = request.form['sheetname']
    composer = request.form['composer']
    instrument = request.form['instrument']
    file_path = request.form['file_path']
    uploader_id = request.form['uploader_id']
    download_count = request.form['download_count']
    # create a query to insert the data
    sql = "INSERT INTO sheets (sheetname, composer, instrument, file_path, uploader_id, download_count) VALUES (?, ?, ?, ?, ?, ?);"
    # execute the query
    query_db(sql, args=(sheetname, composer, instrument, file_path, uploader_id, download_count))
    # redirect back to the home page
    return redirect('/')


# this is the app with debug on
if __name__ == "__main__":
    app.run(debug=True)