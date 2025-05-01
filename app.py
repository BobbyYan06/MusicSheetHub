from flask import Flask, render_template
import sqlite3

app = Flask(__name__)

#path and filename for the database
DATABASE = "musicsheethub.db"

#route go here
@app.route("/")
def index():
    # Connect to the database file
    db = sqlite3.connect(DATABASE)
    # Create the cursor
    cursor = db.cursor()
    # Store a query as a string variable
    sql = "SELECT * FROM Users"
    # Excute the query
    cursor.execute(sql)
    # Fetch all the results of the query
    results = cursor.fetchall()
    # Close the database
    db.close()
    # Send the data to the template
    return render_template('index.html', results=results)

# this is the app with debug on
if __name__ == "__main__":
    app.run(debug=True)