import os
import datetime
from flask import Flask, abort, request, jsonify, redirect, render_template, url_for
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager, login_required, login_user, current_user, logout_user
from flask.ext.bcrypt import Bcrypt
from marshmallow import Serializer

#
# SETUP
#

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
app.secret_key = '\nZ\x89\xf4N\x8d;^\xc5NOJ\x88H\x00p\xc5\x9d0\x13P\t2a'
login_manager = LoginManager(app)
@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

#
# MODELS
#

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True)
    password = db.Column(db.String)
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)
    last_active = db.Column(db.DateTime(timezone=True), index=True)

    def __init__(self, name, password):
        self.name = name
        self.password = password

    # Flask-Login functions
    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)
    # /Flask-Login functions

    class Serializer(Serializer):
        class Meta:
            fields = ("id", "name", "lat", "lon", "last_active")

class Card(db.Model):
    __tablename__ = 'cards'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship('User', backref=db.backref('cards', lazy='dynamic'))

    def __init__(self, name, user_id):
        self.name = name
        self.user_id = user_id

    class Serializer(Serializer):
        class Meta:
            fields = ("id", "name", "user_id")

#
# ROUTES
#

@app.route('/')
def index():
    # todo, detect if user already logged in and redirect to /home if so
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    # for logging in a user
    user = User.query.filter(db.func.lower(User.name) == request.form['name'].lower()).first()
    if user and bcrypt.check_password_hash(user.password, request.form['password']):
        login_user(user)
        return redirect(url_for('home'))
    else:
        abort(401)

@app.route('/user/create')
def create_user():
    # for viewing the create account page
    return render_template('create_account.html')

@app.route('/user/create', methods=['POST'])
def create_user_post():
    # for adding a new user
    existing_user = User.query.filter(db.func.lower(User.name) == request.form['name'].lower()).first()
    if existing_user:
        return "user already exists"
    hashed_password = bcrypt.generate_password_hash(request.form['password'])
    new_user = User(request.form['name'], hashed_password)
    db.session.add(new_user)
    db.session.commit()
    login_user(new_user)
    return redirect(url_for('home'))

@app.route('/home')
@login_required
def home():
    # for viewing the logged in users collection
    cards = current_user.cards.order_by(db.func.lower(Card.name)).all()
    return render_template('home.html', cards=cards)

@app.route('/nearby')
@login_required
def nearby():
    DISTANCE_THRESHOLD = 0.003
    TIME_THRESHOLD = 15 # minutes
    if current_user.lat and current_user.lon:
        users = (User.query
            .filter(User.last_active > db.func.now() - datetime.timedelta(minutes=TIME_THRESHOLD))
            .filter(User.id != current_user.id)
            .filter(User.lat > current_user.lat - DISTANCE_THRESHOLD)
            .filter(User.lat < current_user.lat + DISTANCE_THRESHOLD)
            .filter(User.lon > current_user.lon - DISTANCE_THRESHOLD)
            .filter(User.lon < current_user.lon + DISTANCE_THRESHOLD)
            .order_by(db.func.lower(User.name))
            .all())
    else:
        users = []
    return render_template('nearby.html', users=users)

@app.route('/card/<int:card_id>/remove')
@login_required
def remove_card(card_id):
    # for removing a card from the logged in users collection
    card = Card.query.get(card_id)
    if not card.user_id == current_user.id:
        abort(401)
    if card:
        db.session.delete(card)
        db.session.commit()
    return redirect(url_for('home'))

@app.route('/card/add', methods=['POST'])
@login_required
def add_card():
    # for adding a card to the logged in users collection
    new_card = Card(request.form['card_name'], current_user.id)
    db.session.add(new_card)
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/user/<int:user_id>')
@login_required
def user_by_id(user_id):
    # for viewing a users collection
    user = User.query.get(user_id)
    cards = user.cards.order_by(db.func.lower(Card.name)).all()
    return render_template('user.html', user=user, cards=cards)

@app.route('/user/location', methods=['POST'])
@login_required
def user_location():
    # for updating the users location
    current_user.lat = request.form['lat']
    current_user.lon = request.form['lon']
    current_user.last_active = db.func.now()
    db.session.commit()
    return "ok"

@app.route('/messages')
@login_required
def messages():
    return render_template('messages.html')

#
# MAIN
#

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
