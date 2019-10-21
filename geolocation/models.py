from datetime import datetime
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from geolocation import db, login_manager ,app
from flask_login import UserMixin
import json
from time import time


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


followers = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)



class User(db.Model, UserMixin):

    id = db.Column(db.Integer, primary_key=True)
    last_seen = db.Column(db.DateTime)
    joined_day = db.Column(db.DateTime, default=datetime.utcnow)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(120), unique=True, nullable=False)
    acc_amounts = db.Column(db.Integer, nullable=False, default=0)
    location = db.relationship('Location', backref='author', lazy=True)
    sell_select = db.relationship('Sell_select', backref='author', lazy=True)
    buy_select = db.relationship('Buy_select', backref='author', lazy=True)
    posts = db.relationship('Post', backref='author', lazy=True)
    comments = db.relationship('Comment', backref='author', lazy=True)
    uploaded_items = db.relationship('Uploaded_items', backref='author', lazy=True)
    pubposts = db.relationship('Pubpost', backref='author', lazy=True)
    pubcomments = db.relationship('Pubcomment', backref='author', lazy=True)
    profile = db.relationship('Profile', backref='author', lazy=True)
    profesional = db.relationship('Profesional', backref='author', lazy=True)
    transactions = db.relationship('Transactions', backref='author', lazy=True)
    same_transactions = db.relationship('Same_transactions', backref='author', lazy=True)
    same_transactions2 = db.relationship('Same_transactions2', backref='author', lazy=True)
    withdraws = db.relationship('Withdraw_trans', backref='author', lazy=True)
    withdraw_same_trans = db.relationship('Withdraw_same_trans', backref='author', lazy=True)
    withdraw_same_trans2 = db.relationship('Withdraw_same_trans2', backref='author', lazy=True)
    notifications = db.relationship('Notification', backref='user',lazy='dynamic')
    messages_sent = db.relationship('Pvtmessage',foreign_keys='Pvtmessage.sender_id', backref='author', lazy='dynamic')
    messages_received = db.relationship('Pvtmessage', foreign_keys='Pvtmessage.recipient_id', backref='recipient', lazy='dynamic')
    last_message_read_time = db.Column(db.DateTime)
    admin_fund_depost = db.relationship('Admin_fund_depost', backref='author', lazy=True)



    def new_messages(self):
        last_read_time = self.last_message_read_time or datetime(1900, 1, 1)
        return Pvtmessage.query.filter_by(recipient=self).filter(
            Pvtmessage.timestamp > last_read_time).count()



    def add_notification(self, name, data):
        self.notifications.filter_by(name=name).delete()
        n = Notification(name=name, payload_json=json.dumps(data), user=self)
        db.session.add(n)
        return n


    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')




    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0


    def followed_posts(self):
        followed = Post.query.join(
            followers, (followers.c.followed_id == Post.user_id)).filter(
                followers.c.follower_id == self.id)
        own = Post.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Post.date_posted.desc())



    def get_reset_token(self, expires_sec=1800):
        s = Serializer(app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')




    @staticmethod
    def verify_reset_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)



    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"





class Pvtmessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)


    def __repr__(self):
        return '<Pvtmessage {}>'.format(self.body)



class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.Float, index=True, default=time)
    payload_json = db.Column(db.Text)


    def get_data(self):
        return json.loads(str(self.payload_json))





class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    latitude = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    longitude = db.Column(db.Text, nullable=False )
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Location('{self.latitude}', '{self.longitude}')"



class Sell_select(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    select_one = db.Column(db.Text)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    #longitude = db.Column(db.Text, nullable=False)
    image_file = db.Column(db.String(120), nullable=False, default='default.jpg')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Sell_select('{self.select_one}','{self.date_posted}')"


class Buy_select(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    select_one = db.Column(db.Text)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    #longitude = db.Column(db.Text, nullable=False)
    image_file = db.Column(db.String(120), nullable=False, default='default.jpg')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Buy_select('{self.select_one}','{self.date_posted}')"




class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    comments = db.relationship('Comment', backref='post', lazy=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)



    def __repr__(self):
        return f"Post('{self.title}', '{self.date_posted}')"



class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    

    def __repr__(self):
        return f"Comment('{self.content}', '{self.date_posted}')"



class Pubpost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    comments = db.relationship('Pubcomment', backref='pubpost', lazy=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)



    def __repr__(self):
        return f"Pubpost('{self.title}', '{self.date_posted}')"



class Pubcomment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('pubpost.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    

    def __repr__(self):
        return f"Pubcomment('{self.content}', '{self.date_posted}')"






class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    #longitude = db.Column(db.Text, nullable=False)
    image_file = db.Column(db.String(120))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Profile('{self.content}','{self.date_posted}')"


class Profesional(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    #longitude = db.Column(db.Text, nullable=False)
    image_file = db.Column(db.String(120))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Profesional('{self.content}','{self.date_posted}')"



class Transactions(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transactions = db.Column(db.Text, nullable=False )
    amounts = db.Column(db.Text, nullable=False )
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Transactions('{self.transactions}','{self.date_posted}')"



class Same_transactions(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    same_transactions = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Same_transactions('{self.same_transactions}','{self.date_posted}')"


class Same_transactions2(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    same_transactions2 = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Same_transactions2('{self.same_transactions2}','{self.date_posted}')"


class Withdraw_trans(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transactions = db.Column(db.Text, nullable=False )
    amounts = db.Column(db.Text, nullable=False )
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Withdraw_trans('{self.transactions}','{self.date_posted}')"




class Withdraw_same_trans(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    same_transactions = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Withdraw_same_trans('{self.same_transactions}','{self.date_posted}')"




class Withdraw_same_trans2(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    same_transactions2 = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Withdraw_same_trans2('{self.same_transactions2}','{self.date_posted}')"




class Admin_fund_sent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fund_sent = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


    def __repr__(self):
        return f"Same_transactions2('{self.fund_sent}','{self.date_posted}')"



class Admin_fund_withdraw(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fund_withdraw = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"Same_transactions2('{self.fund_withdraw}','{self.date_posted}')"

class Admin_fund_depost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fund_depost = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


    def __repr__(self):
        return f"Same_transactions2('{self.fund_withdraw}','{self.date_posted}')"


class Uploaded_items(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text)
    the_file = db.Column(db.Text, nullable=False)
    recipient = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


    def __repr__(self):
        return f"Uploaded_items('{self.message}','{self.date_posted}')"