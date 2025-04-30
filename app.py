from flask import Flask

app = Flask(__name__)


#route go here
@app.route("/")
def index():
    return "<h1>Hello World!</h1>"

# runs the app with debug on
if __name__ == "__main__":
    app.run(debug=True)