from flask import Flask, render_template, redirect, request
import sqlite3

app = Flask(__name__)

#path and filename for the database
DATABASE = "musicsheethub.db"

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