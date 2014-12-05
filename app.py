import os
from flask import Flask, abort, request, jsonify
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
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True)
    password = db.Column(db.String)
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)

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
            fields = ("id", "name", "lat", "lon")

class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
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
    # for something
    return "todo"

@app.route('/login', methods=['POST'])
def login():
    # for logging in a user
    posted_user = request.get_json()
    user = User.query.filter(db.func.lower(User.name) == posted_user['name'].lower()).first()
    if user and bcrypt.check_password_hash(user.password, posted_user['password']):
        login_user(user)
        return "logged in as {}".format(user.name)
    else:
        abort(401)

@app.route('/logout')
@login_required
def logout():
    # for logging out a user
    logout_user()
    return "logged out"

@app.route('/user', methods=['POST'])
def add_user():
    # for adding a new user to the database
    posted_user = request.get_json()
    existing_user = User.query.filter(db.func.lower(User.name) == posted_user['name'].lower()).first()
    if existing_user:
        return "user already exists"
    hashed_password = bcrypt.generate_password_hash(posted_user['password'])
    new_user = User(posted_user['name'], hashed_password)
    db.session.add(new_user)
    db.session.commit()
    return "added a new user"

@app.route('/user/location', methods=['POST'])
@login_required
def user_location():
    # for updating the users location
    posted_location = request.get_json()
    current_user.lat = posted_location['lat']
    current_user.lon = posted_location['lon']
    db.session.commit()
    return "updated users location"

@app.route('/user/<name>')
def user_get(name):
    # for returning a list of cards a user has
    user = User.query.filter_by(name=name).first()
    if not user:
        abort(404)
    cards = user.cards.all()
    return jsonify(user=User.Serializer(user).data,
                   cards=Card.Serializer(cards, many=True).data)

@app.route('/user/nearby')
@login_required
def user_nearby():
    # for returning users that are nearby the logged in user
    return "todo"

@app.route('/user/nearby/search')
@login_required
def user_nearby_search():
    # for searching for cards of nearby users
    return "todo"

@app.route('/card', methods=['POST'])
@login_required
def add_card():
    # for adding a card to the logged in users collection
    posted_card = request.get_json()
    new_card = Card(posted_card['name'], current_user.id)
    db.session.add(new_card)
    db.session.commit()
    return "added a card"

@app.route('/card/<int:card_id>', methods=['DELETE'])
@login_required
def delete_card(card_id):
    # for deleting a card from the logged in users collection
    card = Card.query.get(card_id)
    if not card:
        abort(404)
    if not card.user_id == current_user.id:
        abort(401)
    db.session.delete(card)
    db.session.commit()
    return "deleted the card"

#
# MAIN
#

if __name__ == '__main__':
    app.run(debug=True)
