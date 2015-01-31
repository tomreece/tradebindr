import os
import datetime
import pytz
from flask import Flask, abort, request, jsonify, redirect, render_template, url_for
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.sql import or_
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
login_manager.login_view = "/login"
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

    def pretty_last_active(self):
        """
        Get a datetime object or a int() Epoch timestamp and return a
        pretty string like 'an hour ago', 'Yesterday', '3 months ago',
        'just now', etc
        """
        from datetime import datetime
        time = self.last_active
        if not time:
            return "never"
        now = datetime.now(pytz.utc)
        if type(time) is int:
            diff = now - datetime.fromtimestamp(time)
        elif isinstance(time,datetime):
            diff = now - time
        elif not time:
            diff = now - now
        second_diff = diff.seconds
        day_diff = diff.days

        if day_diff < 0:
            return ''

        if day_diff == 0:
            if second_diff < 10:
                return "just now"
            if second_diff < 60:
                return str(second_diff) + " seconds ago"
            if second_diff < 120:
                return "a minute ago"
            if second_diff < 3600:
                return str(second_diff / 60) + " minutes ago"
            if second_diff < 7200:
                return "an hour ago"
            if second_diff < 86400:
                return str(second_diff / 3600) + " hours ago"
        if day_diff == 1:
            return "Yesterday"
        if day_diff < 7:
            return str(day_diff) + " days ago"
        if day_diff < 31:
            return str(day_diff / 7) + " weeks ago"
        if day_diff < 365:
            return str(day_diff / 30) + " months ago"
        return str(day_diff / 365) + " years ago"

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

class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    from_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    from_user = db.relationship('User', primaryjoin=(from_user_id == User.id), backref=db.backref('from', lazy='dynamic'))
    to_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    to_user = db.relationship('User', primaryjoin=(to_user_id == User.id), backref=db.backref('to', lazy='dynamic'))
    message = db.Column(db.String)
    time = db.Column(db.DateTime(timezone=True), index=True)
    is_read = db.Column(db.Boolean, default=False, server_default='FALSE')

#
# ROUTES
#

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    # for logging in a user
    if request.method == 'POST':
        user = User.query.filter(db.func.lower(User.name) == request.form['name'].lower()).first()
        if user and bcrypt.check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(request.args.get("next") or url_for('home'))
        else:
            abort(401)
    else:
        # request.method is GET
        if current_user.is_authenticated():
            return redirect(url_for('home'))
        else:
            return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


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

@app.route('/location')
@login_required
def location():
    return render_template('location.html')

@app.route('/nearby')
@login_required
def nearby():
    DISTANCE_THRESHOLD = 0.6 # about 50 miles
    TIME_THRESHOLD = 5 # minutes
    if current_user.lat and current_user.lon and \
            current_user.last_active > datetime.datetime.now(pytz.utc) - datetime.timedelta(minutes=TIME_THRESHOLD):
        users = (User.query
            #.filter(User.last_active > db.func.now() - datetime.timedelta(minutes=TIME_THRESHOLD))
            .filter(User.id != current_user.id)
            .filter(User.lat > current_user.lat - DISTANCE_THRESHOLD)
            .filter(User.lat < current_user.lat + DISTANCE_THRESHOLD)
            .filter(User.lon > current_user.lon - DISTANCE_THRESHOLD)
            .filter(User.lon < current_user.lon + DISTANCE_THRESHOLD)
            .order_by(User.last_active.desc())
            .all())
    else:
        return redirect(url_for('location'))
    return render_template('nearby.html', users=users, which_traders='Nearby')

@app.route('/all')
@login_required
def all_traders():
    users = (User.query
        .filter(User.id != current_user.id)
        .order_by(User.last_active == None, User.last_active.desc())
        .all())
    return render_template('nearby.html', users=users, which_traders='All')

@app.route('/card/<int:card_id>/remove')
@login_required
def remove_card(card_id):
    # for removing a card from the logged in users collection
    card = Card.query.get(card_id)
    if card:
        if card.user_id == current_user.id:
            db.session.delete(card)
            db.session.commit()
        else:
            abort(401)
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
    messages = (Message.query
        .filter(or_(Message.to_user_id == current_user.id, Message.from_user_id == current_user.id))
        .order_by(Message.time.desc())
        .limit(50)
        .all())
    return render_template('messages.html', messages=messages)

@app.route('/messages/send/<int:to_user_id>')
@login_required
def messages_send(to_user_id):
    to_user = User.query.get(to_user_id)
    return render_template('send_message.html', to_user=to_user)

@app.route('/messages/send', methods=['POST'])
@login_required
def messages_send_post():
    to_user_id = request.form['to_user_id']
    message_body = request.form['message']
    message = Message()
    message.from_user_id = current_user.id
    message.to_user_id = to_user_id
    message.message = message_body
    message.time = db.func.now()
    db.session.add(message)
    db.session.commit()
    return redirect(url_for('messages'))

#
# MAIN
#

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
