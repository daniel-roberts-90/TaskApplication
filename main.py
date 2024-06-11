from flask import Flask, render_template, redirect, url_for, request, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_migrate import Migrate
from config import Config
from datetime import date


app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
migrate = Migrate(app, db)  # Initialize Flask-Migrate

login_manager = LoginManager()
login_manager.login_message = ' '
login_manager.init_app(app)
login_manager.login_view = 'login'

# User model
class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    todos = db.relationship('ToDo', backref='user', lazy=True)

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = Users.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == ['POST']:
        username = request.form['username']
        password = request.form['password']
        user = Users(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        flash('Account created successfully', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ToDo model and routes
class ToDo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String(200), nullable=False)
    done = db.Column(db.Boolean, default=False)
    day = db.Column(db.String(10), nullable=False)
    task_date = db.Column(db.Date, nullable=False, default=date.today)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

with app.app_context():
    db.create_all()

@app.route("/")
@login_required
def index():
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    todos_by_day = {day: ToDo.query.filter_by(day=day, user_id=current_user.id).all() for day in days}
    return render_template("index.html", todos_by_day=todos_by_day, days=days)

@app.route("/add", methods=["POST"])
@login_required
def add():
    task = request.form["todo"]
    day = request.form["day"]
    task_date = request.form["task_date"]
    new_todo = ToDo(task=task, day=day, task_date=task_date, user_id=current_user.id)
    db.session.add(new_todo)
    db.session.commit()
    return redirect(url_for("index"))

@app.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit(id):
    todo = ToDo.query.get_or_404(id)
    if todo.user_id != current_user.id:
        abort(403)  # Forbidden
    if request.method == ["POST"]:
        todo.task = request.form["todo"]
        todo.task_date = request.form["task_date"]
        db.session.commit()
        return redirect(url_for("index"))
    return render_template("edit.html", todo=todo)

@app.route("/check/<int:id>", methods=["POST"])
@login_required
def check(id):
    todo = ToDo.query.get_or_404(id)
    if todo.user_id != current_user.id:
        abort(403)
    todo.done = not todo.done
    db.session.commit()
    return redirect(url_for("index"))

@app.route("/delete/<int:id>", methods=["POST"])
@login_required
def delete(id):
    todo = ToDo.query.get_or_404(id)
    if todo.user_id != current_user.id:
        abort(403)  # Forbidden
    db.session.delete(todo)
    db.session.commit()
    return redirect(url_for("index"))

if __name__ == '__main__':
    app.run(debug=True)
