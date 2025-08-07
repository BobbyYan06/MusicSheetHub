from flask import Flask, render_template, redirect, request, flash, redirect, url_for, session, send_from_directory, g
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'Bobby'
#path and filename for the database
DATABASE = "musicsheethub.db"

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Configurations for file uploads
UPLOAD_FILES = 'static/files'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
MAX_CONTENT_LENGTH = 5 * 1024 * 1024 #5MB limit

app.config['UPLOAD_FILES'] = UPLOAD_FILES
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Helper function to check if a file is allowed based on extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#route go here
@app.route("/")
@app.route("/home")
def home():
    db=get_db()
    cursor = db.cursor()
    # Top 12 download sheets
    cursor.execute('''SELECT id, filename, sheetname, composer, Instrument, download_count FROM sheets ORDER BY
                   download_count DESC LIMIT 12'''
    )
    top_download = cursor.fetchall()

    # Top 12 uploaded sheets
    cursor.execute('''SELECT id, filename, sheetname, composer, Instrument, created_at FROM sheets ORDER BY
                   created_at DESC LIMIT 12'''
    )
    latest_uploaded = cursor.fetchall()
    return render_template('home.html', top_download=top_download, latest_uploaded = latest_uploaded)


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
            db=get_db()
            cursor = db.cursor()
            cursor.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)', (username, email, password))
            db.commit()
            flash('Account created!Please log in.', 'success')
        except sqlite3.IntegrityError:
            flash('Username already exists.', 'danger')

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
        
        db=get_db()
        cursor = db.cursor()
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

    db=get_db()
    cursor = db.cursor()

    cursor.execute("SELECT id FROM users WHERE username=?", (username, ))
    # user_id = str(cursor.fetchone()[0])
    user_id = cursor.fetchone()[0]

    # Fetch genres to populate the dropdown
    cursor.execute("SELECT id, name FROM Genres")
    genres = cursor.fetchall()

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
                db.commit()
                flash("Password updated successfully.", "success")

            return redirect(url_for('profile', tab='account'))
        
        elif form_type == 'upload_sheet':
            file = request.files.get('file')
            sheetname = request.form.get('sheetname')
            composer = request.form.get('composer')
            instrument = request.form.get('instrument')
            # Get selected genre from the form
            genre_id = request.form.get("genre")

            if file and allowed_file(file.filename):
                filename = f"{username}_{secure_filename(file.filename)}"
                filepath = os.path.join(app.config['UPLOAD_FILES'], filename)
                file.save(filepath)

                cursor.execute("INSERT INTO sheets (sheetname, filename, composer, instrument, uploader_id) VALUES (?, ?, ?, ?,?)", 
                               (sheetname, filename, composer, instrument, user_id))
                
                sheet_id = cursor.lastrowid
                # Insert into SheetGenres
                if genre_id:
                    cursor.execute('''
                        INSERT INTO SheetGenres (sid, gid) VALUES (?, ?)
                    ''', (sheet_id, genre_id))
                    
                db.commit()
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
        cursor.execute("SELECT id, filename, sheetname, composer, instrument, created_at FROM sheets WHERE uploader_id = ? ORDER BY created_at DESC", (user_id, ))
        sheets = cursor.fetchall()
    
    # Load user downloads if viewing downloads tab
    downloads = []
    if active_tab == 'downloads':
        cursor.execute('''
                SELECT id, sheet_id, sheetname, filename, composer, instrument, download_at
                FROM downloads
                WHERE username = ?
                ORDER BY download_at DESC   
            ''', (username,))
        downloads = cursor.fetchall()

    # Load user favourites if viewing favourites tab
    favourites = []
    if active_tab == 'favourites':
        cursor.execute("""
        SELECT id, sheet_id, sheetname, filename, composer, instrument, favourited_at
        FROM favourites
        WHERE username = ?
        ORDER BY favourited_at DESC
        """, (username,))
        favourites = cursor.fetchall()
        
    print("Genres loaded:", genres)
    return render_template('profile.html', tab=active_tab, username=username, email=email, sheets=sheets, downloads=downloads, favourites=favourites, genres=genres)


@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out', 'warning')
    return redirect(url_for('login'))

@app.route('/sheets')
def sheets():
    page = request.args.get('page', 1, type=int)
    per_page = 12
    offset = (page - 1) * per_page

    db=get_db()
    cursor = db.cursor()

    # Fetch paginated sheets
    cursor.execute('''
        SELECT id, filename, sheetname, composer, instrument, download_count
        FROM sheets
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
    ''', (per_page, offset))
    results = cursor.fetchall()

    # Fetch total number of sheets for pagination
    cursor.execute('SELECT COUNT(*) FROM sheets')
    total_sheets = cursor.fetchone()[0]
    total_pages = (total_sheets + per_page - 1) // per_page

    return render_template('sheets.html', sheets=results, page=page, total_pages=total_pages)

@app.route('/composer')
def composer():
    return render_template('composer.html')

@app.route('/search')
def search():
    query = request.args.get('query', "").strip()
    results = []

    if query:
       db=get_db()
       cursor = db.cursor()
       # Fetch search results
       cursor.execute('''
            SELECT id, filename, sheetname, composer, instrument, download_count
            FROM sheets
            WHERE sheetname LIKE ? OR composer LIKE ?
            ORDER BY created_at DESC
        ''', (f'%{query}%', f'%{query}%',) )
       results = cursor.fetchall()

    return render_template('search_results.html', query=query, sheets=results)

@app.route('/upload')
def upload():
    return render_template('upload.html')

@app.route('/download/<sheet_id>')
def download_file(sheet_id):
    if 'username' not in session:
        flash('Please log in to download', 'warning')
        return redirect(url_for('login'))
    
    db=get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE Sheets SET download_count = download_count + 1 WHERE id = ?", (sheet_id,))

    # Fetch sheet details
    cursor.execute("SELECT filename, sheetname, composer, instrument FROM sheets WHERE id = ?", (sheet_id,))
    row = cursor.fetchone()

    if row:
        username = session['username']
        filename, sheetname, composer, instrument = row
        # Log donwload
        cursor.execute('''INSERT INTO downloads (sheet_id, username, filename, sheetname, composer, instrument) VALUES (?, ?, ?, ?, ?, ?)''', (sheet_id, username, filename, sheetname, composer, instrument))
    
    db.commit()
    return send_from_directory(app.config['UPLOAD_FILES'], filename, as_attachment=True)

# favourite file
@app.route('/favourite/<sheet_id>')
def favourite_file(sheet_id):
    if 'username' not in session:
        flash('Please log in to download', 'warning')
        return redirect(url_for('login'))
    
    db=get_db()
    cursor = db.cursor()
    sheet_id = str(sheet_id)
    cursor.execute('SELECT filename, sheetname, composer, instrument FROM sheets WHERE id = ?', (sheet_id,))
    row = cursor.fetchone()

    if row:
        username = session['username']
        filename, sheetname, composer, instrument = row
        cursor.execute('INSERT INTO favourites (sheet_id, username, filename, sheetname, composer, instrument) VALUES (?, ?, ?, ?, ?, ?)', (sheet_id, username, filename, sheetname, composer, instrument))

    db.commit()
    flash('File was added to favourite.', 'success')
    return redirect(url_for('home'))


@app.route('/add_sheets', methods=['GET','POST'])
def add_sheets():
    # get the form data from the request object
    sheetname = request.form['sheetname']
    composer = request.form['composer']
    instrument = request.form['instrument']
    filename = request.form['filename']
    uploader_id = request.form['uploader_id']
    download_count = request.form['download_count']
    # create a query to insert the data
    sql = "INSERT INTO sheets (sheetname, composer, instrument, filename, uploader_id, download_count) VALUES (?, ?, ?, ?, ?, ?);"
    # execute the query
    db=get_db()
    cursor = db.cursor()
    cursor.execute(sql, (sheetname, composer, instrument, filename, uploader_id, download_count))
    # redirect back to the home page
    return redirect('/')

# Preview file in browser
@app.route('/preview/<filename>', methods=['GET','POST'])
def preview_file(filename):
    return send_from_directory(app.config['UPLOAD_FILES'], filename, as_attachment=False)

@app.route('/sheet/<int:sheet_id>',methods=['GET','POST'])
def sheet_detail(sheet_id):
    db=get_db()
    cursor = db.cursor()
    cursor.execute('SELECT id, filename, sheetname, composer, instrument, download_count FROM sheets WHERE id = ?', (sheet_id,))
    sheet = cursor.fetchone()

    if not sheet:
        flash("Sheet not found.", "danger")
        return redirect(url_for('home'))
    
    # Handle form submissions
    if request.method == 'POST' and 'username' in session:
        cursor.execute('SELECT id FROM users WHERE username = ?', (session['username'],))
        user_id = cursor.fetchone()[0]

        form_type = request.form.get('form_type')
        if form_type == 'rating':
            rating = int(request.form.get('rating'))
            if 1 <= rating <= 5:
                # Insert or update user rating
                cursor.execute('''
                    INSERT INTO ratings (sheet_id, user_id, rating)
                    VALUES (?, ?, ?)
                    ON CONFLICT(sheet_id, user_id) DO UPDATE SET rating = excluded.rating
                ''', (sheet_id, user_id, rating))
                db.commit()
        else:
            comment = request.form.get('comment')
            cursor.execute("INSERT INTO comments (user_id, sheet_id, comment) VALUES (?, ?, ?)", (user_id, sheet_id, comment))
            db.commit()
    
    # Load comments
    cursor.execute('''
        SELECT u.username, c.comment, c.created_at 
        FROM comments c 
        JOIN users u ON c.user_id = u.id 
        WHERE c.sheet_id = ? 
        ORDER BY c.created_at DESC
    ''', (sheet_id,))
    comments = cursor.fetchall()

    # Load user rating
    cursor.execute('SELECT AVG(rating), COUNT(*) FROM ratings WHERE sheet_id = ?', (sheet_id,))
    avg_rating, rating_count = cursor.fetchone()
    avg_rating = round(avg_rating, 1) if avg_rating else None
    
    return render_template('sheet_detail.html', sheet=sheet, comments=comments, avg_rating=avg_rating)

@app.route('/edit/<int:sheet_id>', methods=['GET', 'POST'])
def edit_sheet(sheet_id):
    if 'username' not in session:
        flash("You must be logged in to edit a sheet.", "warning")
        return redirect(url_for('login'))

    db=get_db()
    cursor = db.cursor()

    # Get the sheet
    cursor.execute("SELECT id, sheetname, composer, instrument, uploader_id FROM sheets WHERE id = ?", (sheet_id,))
    sheet = cursor.fetchone()

    if not sheet:
        flash("Sheet not found.", "danger")
        return redirect(url_for('profile', tab='sheets'))

    # Make sure the user owns the sheet
    cursor.execute("SELECT id FROM users WHERE username = ?", (session['username'],))
    user_id = cursor.fetchone()[0]
    if sheet[4] != user_id:
        flash("You do not have permission to edit this sheet.", "danger")
        return redirect(url_for('profile', tab='sheets'))

    if request.method == 'POST':
        sheetname = request.form.get('sheetname')
        composer = request.form.get('composer')
        instrument = request.form.get('instrument')

        cursor.execute('''
            UPDATE sheets
            SET sheetname = ?, composer = ?, instrument = ?
            WHERE id = ?
        ''', (sheetname, composer, instrument, sheet_id))
        db.commit()
        flash("Sheet updated successfully!", "success")
        return redirect(url_for('profile', tab='sheets'))

    return render_template('edit_sheet.html', sheet=sheet)

@app.route('/delete/<int:sheet_id>', methods=['POST'])
def delete_sheet(sheet_id):
    if 'username' not in session:
        flash("You must be logged in to delete a sheet.", "warning")
        return redirect(url_for('login'))

    db=get_db()
    cursor = db.cursor()

    # Get sheet and verify ownership
    cursor.execute("SELECT filename, uploader_id FROM sheets WHERE id = ?", (sheet_id,))
    row = cursor.fetchone()

    if not row:
        flash("Sheet not found.", "danger")
        return redirect(url_for('profile', tab='sheets'))

    filename, uploader_id = row

    cursor.execute("SELECT id FROM users WHERE username = ?", (session['username'],))
    user_id = cursor.fetchone()[0]

    if uploader_id != user_id:
        flash("You do not have permission to delete this sheet.", "danger")
        return redirect(url_for('profile', tab='sheets'))

    # Delete file from folder
    file_path = os.path.join(app.config['UPLOAD_FILES'], filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    # Delete from database
    cursor.execute("DELETE FROM sheets WHERE id = ?", (sheet_id,))
    db.commit()

    flash("Sheet deleted successfully!", "success")
    return redirect(url_for('profile', tab='sheets'))

@app.route('/delete_download/<int:download_id>', methods=['POST'])
def delete_download(download_id):
    if 'username' not in session:
        flash("You must be logged in to delete a download.", "warning")
        return redirect(url_for('login'))

    db=get_db()
    cursor = db.cursor()

    # Ensure the download belongs to the user
    cursor.execute("SELECT username FROM downloads WHERE id = ?", (download_id,))
    row = cursor.fetchone()

    if not row or row[0] != session['username']:
        flash("You do not have permission to delete this download.", "danger")
        return redirect(url_for('profile', tab='downloads'))

    cursor.execute("DELETE FROM downloads WHERE id = ?", (download_id,))
    db.commit()

    flash("Download record deleted successfully!", "success")
    return redirect(url_for('profile', tab='downloads'))

@app.route('/delete_favourite/<int:favourite_id>', methods=['POST'])
def delete_favourite(favourite_id):
    if 'username' not in session:
        flash("You must be logged in to delete a favourite.", "warning")
        return redirect(url_for('login'))

    db=get_db()
    cursor = db.cursor()

    cursor.execute("SELECT username FROM favourites WHERE id = ?", (favourite_id,))
    row = cursor.fetchone()

    if not row or row[0] != session['username']:
        flash("You do not have permission to delete this favourite.", "danger")
        return redirect(url_for('profile', tab='favourites'))

    cursor.execute("DELETE FROM favourites WHERE id = ?", (favourite_id,))
    db.commit()
    

    flash("Favourite removed successfully!", "success")
    return redirect(url_for('profile', tab='favourites'))

# this is the app with debug on
if __name__ == "__main__":
    app.run(debug=True)