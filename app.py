from flask import Flask, render_template
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
@app.route("/")
def index():
    sql = "SELECT * FROM Sheets"
    results = query_db(sql)
    return render_template('index.html', results=results)


# this is the app with debug on
if __name__ == "__main__":
    app.run(debug=True)