import os
import sys
import secrets
from datetime import datetime
from PIL import Image
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
from flask import Flask, render_template,jsonify ,request,json,redirect,g,flash, url_for,send_from_directory,abort
import requests
from geopy.distance import geodesic
from opencage.geocoder import OpenCageGeocode
from flask_bcrypt import Bcrypt
from datetime import datetime
from flask import request, jsonify, render_template
from flask_login import UserMixin, LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from datetime import datetime
from flask_login import login_user, current_user, logout_user, login_required
from geolocation import app, db, bcrypt ,mail
from geolocation.forms import (RegistrationForm, LoginForm ,UpdateAccountForm,PostForm,PubpostForm ,RequestResetForm,
                                 ResetPasswordForm)
from geolocation.models import  (Location ,User , Sell_select ,Buy_select ,Profile ,Pvtmessage ,
                                    Notification,Post,Pubpost , Comment, Pubcomment , Profesional,Transactions,Same_transactions,
                                     Same_transactions2,Admin_fund_sent ,Admin_fund_withdraw ,Admin_fund_depost,
                                     Withdraw_trans,Withdraw_same_trans ,Withdraw_same_trans2,Uploaded_items)
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed,FileRequired
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from flask_uploads import UploadSet, configure_uploads, IMAGES, patch_request_class
from werkzeug.utils import secure_filename
from os.path import join, dirname, realpath
from flask_mail import Message








@app.route('/')
@login_required
def index():
    return render_template("index.html")


@app.route('/myposition',methods = ['POST', 'GET'])
@login_required
def myposition():
    if request.method == 'POST':
        return redirect(url_for(get_location))
    return render_template("index.html")


@app.route('/map')
@login_required
def map():
    return render_template("map.html")


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('get_location'))
    form = RegistrationForm()
    if form.validate_on_submit():
        phone_number = form.phone.data
        if len(str(phone_number)) == 9:   
            hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            name = form.username.data
            lower_name = name.lower()
            email=form.email.data
            lower_email = email.lower()
            phone_number = '0'+ str(phone_number)
            user = User(username=lower_name, email=lower_email, phone=phone_number, password=hashed_password)
            db.session.add(user)
            db.session.commit()
            flash('Your account has been created! You are now able to log in', 'success')
            return redirect(url_for('login'))
        else:
            flash("Phone number must be ten numbers eg 0788XXXX10","warning")     
    return render_template('register.html', title='Register', form=form)



@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('get_location'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        same_user = User.query.filter_by(phone=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            user.last_seen = datetime.utcnow()
            loc = Location(latitude='-6.7924', longitude='39.2083',author=current_user)
            db.session.add(loc)
            db.session.commit()
            #assume that each user withdrawn 0 since cant affect account 
            transc = Transactions(transactions="MYDEFAULT", amounts="0" ,author=current_user)
            asume = Withdraw_trans(transactions= "MYDEFAULT" ,amounts= "0",author=current_user)
            db.session.add(asume)
            db.session.add(transc)
            db.session.commit()
            return redirect(next_page) if next_page else redirect(url_for('index'))

        elif same_user and bcrypt.check_password_hash(same_user.password, form.password.data):
            login_user(same_user, remember=form.remember.data)
            next_page = request.args.get('next')
            same_user.last_seen = datetime.utcnow()
            loc = Location(latitude='-6.7924', longitude='39.2083',author=current_user)
            db.session.add(loc)
            db.session.commit()
            #assume that each user withdrawn 0 since cant affect account 
            transc = Transactions(transactions="MYDEFAULT", amounts="0" ,author=current_user)
            asume = Withdraw_trans(transactions= "MYDEFAULT" ,amounts= "0",author=current_user)
            db.session.add(asume)
            db.session.add(transc)
            db.session.commit()
            return redirect(next_page) if next_page else redirect(url_for('index'))

        else:
            flash('Login unsuccessful. Please check your email or phone number and password', 'danger')
    return render_template('login.html', title='Login', form=form)



def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request',
                  sender='noreply@demo.com',
                  recipients=[user.email])
    msg.body = f'''Wellcome to Luck Kajoka @ Jokamediatz
To reset your password, visit the following link:
{url_for('reset_token', token=token, _external=True)}
If you did not make this request then simply ignore this email and no changes will be made.
this link will be expired in 30 minutes
'''
    mail.send(msg)


@app.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('login'))
    return render_template('reset_request.html', title='Reset Password', form=form)


@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', title='Reset Password', form=form)





@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('login'))



@app.route('/api/<lat>/<lng>/')
@login_required
def my_location(lat=None,lng=None):
    lats =lat
    lngs =lng
    loc = Location(latitude=lat, longitude=lng,author=current_user)
    db.session.add(loc)
    db.session.commit()
    return json.jsonify({
        'latitude': lats,
        'longitude':lngs
    })


@app.route('/get_location', methods=['GET', 'POST'])
@login_required
def get_location():
    user = current_user
    mypos = Location.query.filter_by(author=user).order_by(Location.date_posted.desc()).limit(1).all()
    """for pos in mypos:
        lat = pos.latitude
        lng = pos.longitude"""
    mypos = mypos[-1:]
    lat = [x.latitude for x in mypos]
    lng = [x.longitude for x in mypos]
    lat = lat[0]
    lng = lng[0]
    key = '60e3fd805ffc4a4c83e75048eb9b4175'
    geocoder = OpenCageGeocode(key)
    results = geocoder.reverse_geocode( lat, lng)
    loc_data = results[0]
    adr = loc_data['formatted']
    area = loc_data['components']
    continent = area['continent']
    country = area['country']
    city = area['city']
    #distric = area['city_district']
    #road = area['road']
    #surbub = area['suburb']
    #myarea = [continent,country,city,road,surbub,myarea]
    #adr ="my"
    return render_template("get_location.html" ,mypos=mypos,lat=lat ,lng=lng
     ,adr=adr ,continent=continent, country=country,city=city)




@app.route('/sell_selected', methods=['GET', 'POST'])
@login_required
def sell_selected():
    selected = []
    select = Sell_select.query.order_by(Sell_select.date_posted.desc()).all()
    for i in select:
        if i.author.username == current_user.username:
            selected.append(i)
    return render_template("sell_select.html",selected=selected)


@app.route('/buy_selected', methods=['GET', 'POST'])
@login_required
def buy_selected():
    selected = []
    select = Buy_select.query.order_by(Buy_select.date_posted.desc()).all()
    for i in select:
        if i.author.username == current_user.username:
            selected.append(i)
    return render_template("buy_select.html",selected=selected)



@app.route('/sell_select', methods=['GET', 'POST'])
@login_required
def sell_select():
    if request.method == "POST":
        sell_selected = []
        the_user = User.query.filter_by(username=current_user.username).first()
        the_sold = the_user.sell_select
        old_sold = [i.select_one for i in the_sold]
        sells = request.form.get("cars", None)
        if not sells in old_sold and sells!=None:
            sell = Sell_select(select_one=sells,author=current_user)
            db.session.add(sell)
            db.session.commit()
            sold = Sell_select.query.order_by(Sell_select.date_posted.desc()).all()
            for sell in sold:
                if sell.author.username == current_user.username:
                    sell_selected.append(sell)
            return render_template("sell_select.html", sell_selected=sell_selected)
        else:
            flash("You aready have {} in your list! please select other one ".format(sells),'warning')
            return redirect(url_for('sell_selected'))
    return render_template("sell_select.html")



@app.route('/buy_select', methods=['GET', 'POST'])
@login_required
def buy_select():
    if request.method == "POST":
        buy_selected = []
        the_user = User.query.filter_by(username=current_user.username).first()
        the_bought = the_user.buy_select
        old_bought = [i.select_one for i in the_bought]
        buys = request.form.get("cars", None)
        if not buys in old_bought and buys!=None:
            buy = Buy_select(select_one=buys,author=current_user)
            db.session.add(buy)
            db.session.commit()
            bought = Buy_select.query.order_by(Buy_select.date_posted.desc()).all()
            for buy in bought:
                if buy.author.username == current_user.username:
                    buy_selected.append(buy)
            return render_template("buy_select.html", buy_selected = buy_selected)
        else:           
            flash("You have aready ordered {}! please select the other one".format(buys),'warning')
            return redirect(url_for('buy_selected'))
    return render_template("buy_select.html")


@app.route('/customer',methods=['GET', 'POST'])
@login_required
def customer():
    sellers = []
    buyers = {}
    far_buyers = []
    a_buyer = []
    myloc = current_user.location
    myloc = myloc[-1:][0]
    mylat = float(myloc.latitude)
    mylng = float(myloc.longitude)
    mylatlng = (float(myloc.latitude),float(myloc.longitude))
    sold = Sell_select.query.all()
    for sell in sold:
        if sell.author == current_user:
            sells = sell.select_one
            buys = Buy_select.query.filter_by(select_one=sells).all()
            for buy in buys:
                loc = buy.author.location
                loc = loc[-1:][0]
                latlng = (float(loc.latitude),float(loc.longitude))
                dis = geodesic(mylatlng, latlng).km
                image_file = url_for('static', filename='profile_pics/' + buy.author.image_file)
                buyer = buy.author.username
                s_buy = buy.select_one
                if dis > 200 or buy.author == current_user:
                    if buy.author == current_user:
                        f_buyers = "You has {} you can't buy from yourself".format(s_buy)
                        far_buyers.append(f_buyers)
                    else:
                        f_buyers = "{} need what you are selling but is far from you contact us for further help".format(buyer)
                        far_buyers.append(f_buyers)
                else:
                    dis = format(dis,'.3f')
                    #geocoders
                    key = '60e3fd805ffc4a4c83e75048eb9b4175'
                    geocoder = OpenCageGeocode(key)
                    results = geocoder.reverse_geocode( loc.latitude, loc.longitude)
                    loc_data = results[0]
                    adr = loc_data['formatted']
                    s_buyers = {"{1} is {0} km away from you. \n{1} want to buy : {2}. \n{1} is curently at : {3}  ".format(dis,buyer,s_buy,adr):image_file}
                    buyers.update({buyer:s_buyers})
                    lat = float(loc.latitude)
                    lng = float(loc.longitude)
                    #a_buyer.append(buyer)
                    #image_file = url_for('static', filename='profile_pics/' + buy.author.image_file)
    return render_template('geo1.html',buyers=buyers,far_buyers=far_buyers,mylat=mylat,
        mylng=mylng )
    



@app.route('/the_sellers',methods=['GET', 'POST'])
@login_required
def the_sellers():
    sellers = {}
    buyers = []
    far_sellers = []
    a_seller = []
    myloc = current_user.location
    myloc = myloc[-1:][0]
    mylat = float(myloc.latitude)
    mylng = float(myloc.longitude)
    mylatlng = (float(myloc.latitude),float(myloc.longitude))
    bought = Buy_select.query.all()
    for buy in bought:
        if buy.author == current_user:
            buys = buy.select_one
            sells = Sell_select.query.filter_by(select_one=buys).all()
            for sell in sells:
                loc = sell.author.location
                loc = loc[-1:][0]
                latlng = (float(loc.latitude),float(loc.longitude))
                dis = geodesic(mylatlng, latlng).km
                image_file = url_for('static', filename='profile_pics/' + sell.author.image_file)
                seller = sell.author.username
                s_sell = sell.select_one
                if dis >200 or sell.author == current_user:
                    if sell.author== current_user:
                        f_sellers = "You has {} you can't sell to yourself".format(s_sell)
                    else:
                        f_sellers = "{} has what you are looking but is far from you contact us for further help ".format(seller)
                        far_sellers.append(f_sellers)
                else:
                    dis = format(dis,'.3f')
                    #geocoders
                    key = '60e3fd805ffc4a4c83e75048eb9b4175'
                    geocoder = OpenCageGeocode(key)
                    results = geocoder.reverse_geocode( loc.latitude, loc.longitude)
                    loc_data = results[0]
                    adr = loc_data['formatted']                    
                    s_sellers = {"{1} is {0} km away from you. \n{1} is selling : {2}. \n{1} is curently at : {3}  ".format(dis,seller,s_sell,adr):image_file}
                    sellers.update({seller:s_sellers})
                    lat = float(loc.latitude)
                    lng = float(loc.longitude)
    return render_template('the_sellers.html',sellers=sellers,far_sellers=far_sellers,
        mylat=mylat,mylng=mylng )




@app.route("/get_customer/<string:username>")
@login_required
def get_customer(username):
    user = User.query.filter_by(username=username).first_or_404()
    p_descrptn = user.profile[-1:]
    location = user.location
    location = location[-1:][0]
    lat = float(location.latitude)
    lng = float(location.longitude)
    myloc = current_user.location
    myloc = myloc[-1:][0]
    mylat = float(myloc.latitude)
    mylng = float(myloc.longitude)
    bought = user.buy_select
    return render_template('customer.html',user=user,lat=lat,lng=lng,
        mylat=mylat,mylng=mylng ,bought=bought ,p_descrptn=p_descrptn)



@app.route("/get_seller/<string:username>")
@login_required
def get_seller(username):
    user = User.query.filter_by(username=username).first_or_404()
    p_descrptn = user.profile[-1:]
    location = user.location
    location = location[-1:][0]
    lat = float(location.latitude)
    lng = float(location.longitude)
    myloc = current_user.location
    myloc = myloc[-1:][0]
    mylat = float(myloc.latitude)
    mylng = float(myloc.longitude)
    sold = user.sell_select
    return render_template('seller.html',user=user,lat=lat,lng=lng,
        mylat=mylat,mylng=mylng ,sold=sold ,p_descrptn=p_descrptn)



@app.route("/get_profesional/<string:username>")
@login_required
def get_profesional(username):
    user = User.query.filter_by(username=username).first_or_404()
    p_descrptn = user.profesional[-1:]
    location = user.location
    location = location[-1:][0]
    lat = float(location.latitude)
    lng = float(location.longitude)
    myloc = current_user.location
    myloc = myloc[-1:][0]
    mylat = float(myloc.latitude)
    mylng = float(myloc.longitude)
    sold = user.sell_select
    return render_template('profesional.html',user=user,lat=lat,lng=lng,
        mylat=mylat,mylng=mylng ,sold=sold ,p_descrptn=p_descrptn)




def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    output_size = (500, 500)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


# Uploads settings the config that not taken into a init.py file
app.config['UPLOADED_PHOTOS_DEST'] = os.getcwd() + 'static/profile_pics'
photos = UploadSet('photos', IMAGES)
configure_uploads(app, photos)
patch_request_class(app)  # set maximum file size, default is 16MB
photos = UploadSet('photos', IMAGES)


class Profileform(FlaskForm):
    content = TextAreaField('Type here', validators=[DataRequired()])
    photo = FileField(validators=[FileAllowed(photos, u'Image only!'),FileRequired(u'File was empty!')])
    submit = SubmitField(u'Upload')

class Profesionalform(FlaskForm):
    title = TextAreaField('Your skill eg: Photographer', validators=[DataRequired()])
    content = TextAreaField('Short description about your skill', validators=[DataRequired()])
    photo = FileField(validators=[FileAllowed(photos, u'Image only!'),FileRequired(u'File was empty!')])
    submit = SubmitField(u'Submit')



@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        username = form.username.data
        lower_name = username.lower()
        current_user.username = lower_name
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('update_acc.html', title='Account',
                           image_file=image_file, form=form)



@app.route('/profile_fill', methods=['GET', 'POST'])
@login_required
def profile_fill():
    user = User.query.filter_by(username=current_user.username).first_or_404()
    p_descrptn = user.profile[-1:]
    form = Profileform()
    if form.validate_on_submit():
        filename = photos.save(form.photo.data)
        file_url = photos.url(filename)
        new_file = file_url
        message = Profile(content=form.content.data,author=current_user, image_file=new_file)
        db.session.add(message)
        db.session.commit()
        flash('Your profile has been created!', 'success')
        return redirect(url_for('profile_fill'))
    else:
        file_url = None
    return render_template('profile.html', form=form ,p_descrptn=p_descrptn)



@app.route('/profesional_fill', methods=['GET', 'POST'])
@login_required
def profesional_fill():
    user = User.query.filter_by(username=current_user.username).first_or_404()
    p_descrptn = user.profesional[-1:]
    form = Profesionalform()
    if form.validate_on_submit():
        filename = photos.save(form.photo.data)
        file_url = photos.url(filename)
        new_file = file_url
        message = Profesional(title=form.title.data,content=form.content.data,author=current_user,
                 image_file=new_file)
        db.session.add(message)
        db.session.commit()
        flash('Your profile has been created!', 'success')
        return redirect(url_for('profesional_fill'))
    else:
        file_url = None
    return render_template('profesional_form.html', form=form ,p_descrptn=p_descrptn)





@app.route('/send_message/<recipient>', methods=['GET', 'POST'])
@login_required
def send_message(recipient):
    if request.method == "POST":
        message = request.form['msg']
        recipient = request.form['thename']
        user = User.query.filter_by(username=recipient).first_or_404()
        user.add_notification('unread_message_count', user.new_messages())
        msg = Pvtmessage(author=current_user, recipient=user,body=message)
        db.session.add(msg)
        db.session.commit()
        flash('Your message has been sent to {}'.format(recipient),'success')
        # chat
        user = User.query.filter_by(username=recipient).first_or_404()
        sent_message = current_user.messages_sent.filter_by(recipient=user).all()
        received_message = current_user.messages_received.filter_by(author=user).all()
        msg_list_array = []
        for themsg in received_message:
            msg = "msg"
            date = "date"
            user = "user"
            theid = "theid"
            value = {user:themsg.author.username,theid:themsg.id, msg:themsg.body , date:str(themsg.timestamp)}
            msg_list_array.append(value)
        for themsg1 in sent_message:
            msg = "msg"
            date = "date"
            user = "user"
            theid = "theid"
            value2 = {user:themsg1.author.username ,theid:themsg1.id, msg:themsg1.body ,date:str(themsg1.timestamp)}
            msg_list_array.append(value2)

        sorted_list = sorted(msg_list_array,key=lambda x: x['date'], reverse=True) 
        return redirect(url_for('send_message', recipient=recipient))
    else:
        user = User.query.filter_by(username=recipient).first_or_404()
        sent_message = current_user.messages_sent.filter_by(recipient=user).all()
        received_message = current_user.messages_received.filter_by(author=user).all()
        msg_list_array = []
        for themsg in received_message:
            msg = "msg"
            date = "date"
            user = "user"
            theid = "theid"
            value = {user:themsg.author.username,theid:themsg.id, msg:themsg.body , date:str(themsg.timestamp)}
            msg_list_array.append(value)
        for themsg1 in sent_message:
            msg = "msg"
            date = "date"
            user = "user"
            theid = "theid"
            value2 = {user:themsg1.author.username ,theid:themsg1.id, msg:themsg1.body ,date:str(themsg1.timestamp)}
            msg_list_array.append(value2)

        sorted_list = sorted(msg_list_array,key=lambda x: x['date'], reverse=True) 
    return render_template('chat_message.html', recipient=recipient, sorted_list=sorted_list)



@app.route('/send_message2', methods=['GET', 'POST'])
@login_required
def send_message2():
    if request.method == "POST":
        message = request.form['msg']
        recipient = request.form['thename']
        user = User.query.filter_by(username=recipient).first_or_404()
        user.add_notification('unread_message_count', user.new_messages())
        msg = Pvtmessage(author=current_user, recipient=user,body=message)
        db.session.add(msg)
        db.session.commit()
        flash('Your message has been sent to {}'.format(recipient),'success')
        #return redirect(url_for('pvtmessages'))
        sent_message = current_user.messages_sent.filter_by(recipient=user).all()
        received_message = current_user.messages_received.filter_by(author=user).all()
        msg_list_array = []
        for themsg in received_message:
            msg = "msg"
            date = "date"
            user = "user"
            theid = "theid"
            value = {user:themsg.author.username,theid:themsg.id, msg:themsg.body , date:str(themsg.timestamp)}
            msg_list_array.append(value)
        for themsg1 in sent_message:
            msg = "msg"
            date = "date"
            user = "user"
            theid = "theid"
            value2 = {user:themsg1.author.username ,theid:themsg1.id, msg:themsg1.body ,date:str(themsg1.timestamp)}
            msg_list_array.append(value2)

        sorted_list = sorted(msg_list_array,key=lambda x: x['date'], reverse=True)
    else:
        flash("Send message","success")
        sent_message = current_user.messages_sent.filter_by(recipient=user).all()
        received_message = current_user.messages_received.filter_by(author=user).all()
        msg_list_array = []
        for themsg in received_message:
            msg = "msg"
            date = "date"
            user = "user"
            theid = "theid"
            value = {user:themsg.author.username,theid:themsg.id, msg:themsg.body , date:str(themsg.timestamp)}
            msg_list_array.append(value)
        for themsg1 in sent_message:
            msg = "msg"
            date = "date"
            user = "user"
            theid = "theid"
            value2 = {user:themsg1.author.username ,theid:themsg1.id, msg:themsg1.body ,date:str(themsg1.timestamp)}
            msg_list_array.append(value2)

        sorted_list = sorted(msg_list_array,key=lambda x: x['date'], reverse=True)     
    return render_template('chat_message.html',sorted_list=sorted_list)




@app.route('/pvtmessages')
@login_required
def pvtmessages():
    current_user.last_message_read_time = datetime.utcnow()
    current_user.add_notification('unread_message_count', 0)
    db.session.commit()
    page = request.args.get('page', 1, type=int)
    messages = current_user.messages_received.order_by(
    Pvtmessage.timestamp.desc()).paginate(page=page, per_page=25)
    return render_template('pvtmessages2.html', messages=messages.items)



@app.route('/notifications')
@login_required
def notifications():
    since = request.args.get('since', 0.0, type=float)
    notifications = current_user.notifications.filter(
        Notification.timestamp > since).order_by(Notification.timestamp.asc())
    return jsonify([{
        'name': n.name,
        'data': n.get_data(),
        'timestamp': n.timestamp
    } for n in notifications])



@app.route("/post/new", methods=['GET', 'POST'])
@login_required
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('show_posts'))
    return render_template('create_post.html', title='New Post',
                           form=form, legend='New Post')




@app.route('/show_posts' ,methods=['GET', 'POST'])
@login_required
def show_posts():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=25)
    return render_template('show_post.html', posts=posts)




@app.route("/post/<int:post_id>", methods=['GET', 'POST'])
@login_required
def post(post_id):
    if request.method == "POST":
        message = request.form['msg'] 
        comment = Comment(content=message, author=current_user, post_id=post_id)
        db.session.add(comment)
        db.session.commit()
        flash('Your comment has been aded!', 'success')
        return redirect(url_for('post', post_id=post_id))
    post = Post.query.get_or_404(post_id)
    comments = post.comments
    return render_template('post_comment.html', content=post.content, post=post ,
        comments=comments, post_id=post_id)



@app.route("/post/<int:post_id>/delete", methods=['GET','POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('show_posts'))



@app.route("/delete_comment/<int:post_id>/<int:comment_id>", methods=['GET','POST'])
@login_required
def delete_comment(post_id,comment_id):
    post = Comment.query.get_or_404(comment_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your comment has been deleted!', 'success')
    return redirect(url_for('post',post_id=post_id))





@app.route("/pub_post/new", methods=['GET', 'POST'])
@login_required
def new_pub_post():
    form = PubpostForm()
    if form.validate_on_submit():
        post = Pubpost(title=form.title.data, content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('show_pub_posts'))
    return render_template('create_pub_post.html', title='New Post',
                           form=form, legend='New Post')




@app.route('/show_pub_posts' ,methods=['GET', 'POST'])
@login_required
def show_pub_posts():
    page = request.args.get('page', 1, type=int)
    posts = Pubpost.query.order_by(Pubpost.date_posted.desc()).paginate(page=page, per_page=25)
    return render_template('show_pub_post.html', posts=posts)




@app.route("/pub_post/<int:post_id>", methods=['GET', 'POST'])
@login_required
def pub_post(post_id):
    if request.method == "POST":
        message = request.form['msg'] 
        comment = Pubcomment(content=message, author=current_user, post_id=post_id)
        db.session.add(comment)
        db.session.commit()
        flash('Your comment has been aded!', 'success')
        return redirect(url_for('pub_post', post_id=post_id))
    post = Pubpost.query.get_or_404(post_id)
    comments = post.comments
    return render_template('pub_post_comment.html', content=post.content, post=post,
         comments=comments,post_id=post_id )



@app.route("/pub_post/<int:post_id>/delete", methods=['GET','POST'])
@login_required
def delete_pub_post(post_id):
    post = Pubpost.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('show_pub_posts'))



@app.route("/delete_pub_comment/<int:post_id>/<int:comment_id>", methods=['GET','POST'])
@login_required
def delete_pub_comment(post_id,comment_id):
    post = Pubcomment.query.get_or_404(comment_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your comment has been deleted!', 'success')
    return redirect(url_for('pub_post',post_id=post_id))






@app.route("/del_sell_selected/<int:post_id>", methods=['GET','POST'])
@login_required
def del_sell_selected(post_id):
    post = Sell_select.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your item has been deleted!', 'success')
    return redirect(url_for('sell_selected'))


@app.route("/del_buy_selected/<int:post_id>", methods=['GET','POST'])
@login_required
def del_buy_selected(post_id):
    post = Buy_select.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your item has been deleted!', 'success')
    return redirect(url_for('buy_selected'))


@app.route("/delete_descrptn/<int:post_id>", methods=['GET','POST'])
@login_required
def delete_descrptn(post_id):
    post = Profesional.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your item has been deleted!', 'success')
    return redirect(url_for('profesional_fill'))


@app.route("/delete_p_descrptn/<int:post_id>", methods=['GET','POST'])
@login_required
def delete_p_descrptn(post_id):
    post = Profile.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your item has been deleted!', 'success')
    return redirect(url_for('profile_fill'))


#delete private messages for chating
@app.route("/pvtmsgs_delete/<int:post_id>", methods=['GET','POST'])
@login_required
def pvtmsgs_delete(post_id):
    post = Pvtmessage.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your message has been deleted!', 'success')
    return redirect(url_for('pvtmessages'))


#delete attachments sent for download
@app.route("/attach_delete/<int:post_id>", methods=['GET','POST'])
@login_required
def attach_delete(post_id):
    post = Uploaded_items.query.get_or_404(post_id)
    user = current_user.username
    #if post.author == current_user:
        #abort(403)
    db.session.delete(post)
    db.session.commit()
    flash(' Attachment has been deleted!', 'success')
    return redirect(url_for('download_file',recipient=user))





@app.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('index'))
    if user == current_user:
        flash('You cannot follow yourself!','warning')
        return redirect(url_for('user_posts', username=username))
    current_user.follow(user)
    db.session.commit()
    flash('You are following {}! and becoming a seller'.format(username),'success')
    return redirect(url_for('get_seller', username=username))




@app.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('index'))
    if user == current_user:
        flash('You cannot unfollow yourself!','warning')
        return redirect(url_for('user_posts', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash('You are not following {}.'.format(username),'success')
    return redirect(url_for('get_seller', username=username))



@app.route('/c_follow/<username>')
@login_required
def c_follow(username):
    # c stand for customer
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('index'))
    if user == current_user:
        flash('You cannot follow yourself!','warning')
        return redirect(url_for('user_posts', username=username))
    current_user.follow(user)
    db.session.commit()
    flash('You are following {}! and now is your good customer'.format(username),'success')
    return redirect(url_for('get_customer', username=username))




@app.route('/c_unfollow/<username>')
@login_required
def c_unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('index'))
    if user == current_user:
        flash('You cannot unfollow yourself!','warning')
        return redirect(url_for('user_posts', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash('You are not following {}.'.format(username),'success')
    return redirect(url_for('get_customer', username=username))




@app.route('/payment_acc', methods=['GET', 'POST'])
@login_required
def payment_acc():  
    if request.method == "POST":
        #admin = User.query.filter_by(username=username).first()
        amount = request.form['mypay']
        transct_id = request.form['thename']
        my_amount = current_user.acc_amounts
        old_trans = Transactions.query.all()
        list_old_trans = [t.transactions for t in old_trans]
        if transct_id in list_old_trans:
            flash("You aready have {}".format(transct_id), "danger")
        else:
            transc = Transactions(transactions=transct_id, amounts=amount ,author=current_user)
            db.session.add(transc)
            db.session.commit()
            flash("Thanks for deposting your fund will be available soon here! ","success")
            balance = current_user.acc_amounts + int(amount)
            message = "{0} has deposted {1} Tshs in his account.\n Now has unapproved balance of  {2} Tsh with ID of : {3}".format(
                current_user.username,amount,balance ,transct_id)
            msg = Admin_fund_depost(fund_depost=message ,author=current_user)
            db.session.add(msg)
            db.session.commit()
            return redirect(url_for("fund_account"))
    else:
        my_amount = current_user.acc_amounts
    return render_template("payment_acc.html",my_amount=my_amount)



@app.route('/fund_account', methods=['GET', 'POST'])
@login_required
def fund_account():
    user = User.query.filter_by(username=current_user.username).first()
    transct_list = user.transactions
    last_one = transct_list[-1:][0]
    amount = last_one.amounts
    transct_id = last_one.transactions
    withdraw_users = user.withdraws
    withdraw_last_one = withdraw_users[-1:][0]
    withdraw_amount = withdraw_last_one.amounts
    withdraw_id = withdraw_last_one.transactions
    #Now query for withdrawing and funding ids also amounts
    same_transaction = Same_transactions.query.all()
    withdraw_same_trans = Withdraw_same_trans.query.all()
    same_transactions = [t.same_transactions for t in same_transaction]
    withdraw_same_trans2 = [t.same_transactions for t in withdraw_same_trans]
    if transct_id in same_transactions:
        amount = int(amount)
        current_user.acc_amounts = current_user.acc_amounts + amount
        db.session.commit()
        amounts = current_user.acc_amounts
        del_trans =Same_transactions.query.filter_by(same_transactions=transct_id).first()
        db.session.delete(del_trans)
        db.session.commit()
        flash("Your deposts has been successful","success")

    elif withdraw_id in withdraw_same_trans2:
        withdraw_amount = int(withdraw_amount)
        remained = current_user.acc_amounts - withdraw_amount
        current_user.acc_amounts = remained
        db.session.commit()
        amounts = current_user.acc_amounts
        del_trans =Withdraw_same_trans.query.filter_by(same_transactions=withdraw_id).first()
        db.session.delete(del_trans)
        db.session.commit()
        transct_id = withdraw_id
        flash("Your withdrawing has been successful","success")
    else:
        amounts = current_user.acc_amounts
    return render_template("fund_account.html",amounts=amounts)






@app.route('/confirm_trans', methods=['GET', 'POST'])
@login_required
def confirm_trans():  
    if request.method == "POST":
        trans = request.form['thename']
        old_trans = Same_transactions2.query.all()
        list_old_trans = [t.same_transactions2 for t in old_trans]
        if trans in list_old_trans:
            flash("You have aready added {} ".format(trans),"danger")
            confirmed_ids = Transactions.query.filter_by(transactions=trans).first()

        else:
            the_id = Same_transactions(same_transactions=trans, author=current_user)
            db.session.add(the_id)
            db.session.commit()
            confirmed_ids = Transactions.query.filter_by(transactions=trans).first()
            #same id that will be remained
            the_id2 = Same_transactions2(same_transactions2=trans, author=current_user)
            db.session.add(the_id2)
            db.session.commit()
            flash("successful confirmed","success")
            return redirect(url_for("fund_account"))
    else:
        flash("You should confirm transaction id from payments messages","success")
        confirmed_ids = "Choose the transaction id to confirm"
    return render_template("confirm_transct.html",confirmed_ids=confirmed_ids)





@app.route('/confirm_withdraw', methods=['GET', 'POST'])
@login_required
def confirm_withdraw():  
    if request.method == "POST":
        trans = request.form['thename']
        old_trans = Withdraw_same_trans2.query.all()
        list_old_trans = [t.same_transactions2 for t in old_trans]
        if trans in list_old_trans:
            flash("You have aready added {} ".format(trans),"danger")
            confirmed_ids = Withdraw_trans.query.filter_by(transactions=trans).first()
        else:
            the_id = Withdraw_same_trans(same_transactions=trans, author=current_user)
            db.session.add(the_id)
            db.session.commit()
            confirmed_ids = Withdraw_trans.query.filter_by(transactions=trans).first()
            #same id that will be remained
            the_id2 = Withdraw_same_trans2(same_transactions2=trans, author=current_user)
            db.session.add(the_id2)
            db.session.commit()
            flash("successful confirmed","success")
            confirmed_ids = Withdraw_same_trans.query.all()
            return redirect(url_for("fund_account"))
    else:
        flash("You should confirm transaction id from withdraws messages","success")
        confirmed_ids = "Choose the transaction id to confirm"
    return render_template("confirm_withdraw_id.html",confirmed_ids=confirmed_ids)




@app.route('/send_fund', methods=['GET', 'POST'])
@login_required
def send_fund():  
    if request.method == "POST":
        recipient = request.form['thename']
        admin = User.query.filter_by(phone="0766332164").first()
        user = User.query.filter_by(username=recipient).first()
        amount = request.form['mypay']
        amount = int(amount)
        remained_amount = current_user.acc_amounts - amount
        if remained_amount > 0:
            if user == current_user:
                flash("You can't send money to yourself !","danger")
                amounts = current_user.acc_amounts
            elif not user:
                flash("Sorry we have no member registered as {} !".format(recipient),"danger")
                amounts = current_user.acc_amounts               
            else:
                user.acc_amounts = user.acc_amounts + amount
                current_user.acc_amounts = remained_amount
                db.session.commit()
                amounts = current_user.acc_amounts
                flash("{} Tshs sent to {}".format(amount,user.username),"success")
                message = "{0} is sending {1} Tsh to {2}.\n Now sender has {3} Tsh and recipient has {4} Tsh ".format(current_user.username,
                    amount,user.username,amounts,user.acc_amounts)
                msg = Admin_fund_sent(fund_sent=message)
                db.session.add(msg)
                db.session.commit()
                #user notification
                the_msg = "You have received {0} Tsh from {1} ,your balance now is {2} Tsh".format(amount,
                    current_user.username,user.acc_amounts)
                user.add_notification('unread_message_count', user.new_messages())
                msg = Pvtmessage(author=admin, recipient=user,body=the_msg)
                db.session.add(msg)
                db.session.commit()
                return redirect(url_for("fund_account"))
        else:
            flash("You have no enough balance to send {} Tshs".format(amount),"danger")
            amounts = current_user.acc_amounts
    else:
        amounts = current_user.acc_amounts
    return render_template("send_fund.html",amounts=amounts)




@app.route('/withdraw_fund', methods=['GET', 'POST'])
@login_required
def withdraw_fund(): 
    if request.method == "POST":
        amount = request.form['mypay']
        trans_id = request.form['thename']
        amount = int(amount)
        remained_amount = current_user.acc_amounts - 0#amount
        #the_withdraws = Withdraw_trans.query.all()
        #withdraws_list = [t.transactions for t in the_withdraws]
        if remained_amount > 0:
            trans =Withdraw_trans(transactions=trans_id,amounts=amount ,author=current_user)
            db.session.add(trans)
            db.session.commit()
            #update the user account
            current_user.acc_amounts = remained_amount
            db.session.commit()
            message = "{0} has been withdrawn from {1}'s account.\n The remained balance is {2} \n The secret word is:  {3}".format(
                amount,current_user.username,current_user.acc_amounts,trans_id)
            msg = Admin_fund_withdraw(fund_withdraw=message)
            db.session.add(msg)
            db.session.commit()
            amounts = current_user.acc_amounts
            flash("You have successful made a withdrawing request!,your request will be confirmed soon","success")
            return redirect(url_for("fund_account"))
        else:
            flash("You have no enough balance to withdraw {} Tsh".format(amount),"danger")
            amounts = current_user.acc_amounts
    else:
        flash("You can now withdaw fund with some charges","success")
        amounts = current_user.acc_amounts
    return render_template("withraw_fund.html",amounts=amounts)



@app.route('/admin_show_deposted', methods=['GET', 'POST'])
@login_required
def admin_show_deposted():
    page = request.args.get('page', 1, type=int)
    deposts = Admin_fund_depost.query.order_by(Admin_fund_depost
        .date_posted.desc()).paginate(page=page, per_page=25)
    return render_template("admin_deposted.html" ,deposts=deposts)



@app.route('/admin_show_withdraw', methods=['GET', 'POST'])
@login_required
def admin_show_withdraw():
    page = request.args.get('page', 1, type=int)
    withdrawn = Admin_fund_withdraw.query.order_by(Admin_fund_withdraw
        .date_posted.desc()).paginate(page=page, per_page=25)
    return render_template("admin_withdraw.html", withdrawn=withdrawn)


@app.route('/admin_show_sent', methods=['GET', 'POST'])
@login_required
def admin_show_sent():
    page = request.args.get('page', 1, type=int)
    sents = Admin_fund_sent.query.order_by(Admin_fund_sent
        .date_posted.desc()).paginate(page=page, per_page=25)
    return render_template("admin_sent.html", sents=sents)



@app.route('/user/<username>/popup')
@login_required
def user_popup(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('user_popup.html', user=user)



#uploads and download documents os.getcwd()

#UPLOAD_FOLDER = '/static/profile_pics'
UPLOAD_FOLDER = join(dirname(realpath(__file__)), 'static/up_download/pics/..')
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg','mp4', 'jpeg', 'gif'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
#cheach for allowed file





def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/myupload/<recipient>', methods=['GET', 'POST'])
@login_required
def myupload(recipient):
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        msgs = request.form['msg']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            random_hex = secrets.token_hex(8)
            _, f_ext = os.path.splitext(file.filename)
            picture_fn = random_hex + f_ext
            filename = secure_filename(picture_fn)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            myfile = Uploaded_items(message=msgs,the_file=filename ,author=current_user,recipient=recipient)
            db.session.add(myfile)
            db.session.commit()
            return redirect(url_for('download_file',recipient=recipient))           
    return render_template("upload_items.html", recipient=recipient)
 

@app.route('/download_file/<recipient>', methods=['GET', 'POST'])
@login_required
def download_file(recipient):
    filenames = Uploaded_items.query.order_by(Uploaded_items.date_posted.desc()).all()
    return render_template("upload_items.html",filenames=filenames ,recipient=recipient)



@app.route('/uploaded_file/<filename>', methods=['GET', 'POST'])
@login_required
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename ,as_attachment=True)



@app.errorhandler(404)
def error_404(error):
    return render_template('404.html'), 404


@app.errorhandler(403)
def error_403(error):
    return render_template('403.html'), 403


@app.errorhandler(500)
def error_500(error):
    return render_template('500.html'), 500