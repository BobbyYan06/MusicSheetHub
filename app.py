from flask import Flask, render_template

app = Flask(__name__)


#route go here
@app.route("/")
def index():
    return render_template('index.html')

# this is the app with debug on
if __name__ == "__main__":
    app.run(debug=True)