from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
import MySQLdb.cursors
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Change this to your secret key (it can be anything, it's for extra protection)
app.secret_key = "your_secret_key"

# Database connection details
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "todo_db"

# Initialize MySQL
mysql = MySQL(app)


@app.route("/")
def home():
    if "loggedin" in session:
        return redirect(url_for("todo"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    msg = ""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        account = cursor.fetchone()

        if account and check_password_hash(account["password"], password):
            session["loggedin"] = True
            session["id"] = account["id"]
            session["username"] = account["username"]
            return redirect(url_for("todo"))
        else:
            msg = "Incorrect username/password!"
    return render_template("login.html", msg=msg)


@app.route("/register", methods=["GET", "POST"])
def register():
    msg = ""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        email = request.form["email"]

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        account = cursor.fetchone()

        if account:
            msg = "Account already exists!"
        else:
            hashed_password = generate_password_hash(password)
            cursor.execute(
                "INSERT INTO users (username, password, email) VALUES (%s, %s, %s)",
                (username, hashed_password, email),
            )
            mysql.connection.commit()
            msg = "You have successfully registered!"
            return redirect(url_for("login"))
    return render_template("register.html", msg=msg)


@app.route("/todo")
def todo():
    if "loggedin" not in session:
        return redirect(url_for("login"))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM tasks WHERE user_id = %s", (session["id"],))
    tasks = cursor.fetchall()
    return render_template("todo.html", tasks=tasks)


@app.route("/add_task", methods=["POST"])
def add_task():
    if "loggedin" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        task = request.form["task"]
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            "INSERT INTO tasks (user_id, task, completed) VALUES (%s, %s, %s)",
            (session["id"], task, False),
        )
        mysql.connection.commit()
    return redirect(url_for("todo"))


@app.route("/complete_task/<int:id>")
def complete_task(id):
    if "loggedin" not in session:
        return redirect(url_for("login"))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(
        "UPDATE tasks SET completed = TRUE WHERE id = %s AND user_id = %s",
        (id, session["id"]),
    )
    mysql.connection.commit()
    return redirect(url_for("todo"))


@app.route("/delete_task/<int:id>")
def delete_task(id):
    if "loggedin" not in session:
        return redirect(url_for("login"))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(
        "DELETE FROM tasks WHERE id = %s AND user_id = %s", (id, session["id"])
    )
    mysql.connection.commit()
    return redirect(url_for("todo"))


@app.route("/logout")
def logout():
    session.pop("loggedin", None)
    session.pop("id", None)
    session.pop("username", None)
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
