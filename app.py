######################################
# author ben lawson <balawson@bu.edu> 
# Edited by: Baichuan Zhou (baichuan@bu.edu) and Craig Einstein <einstein@bu.edu>
######################################
# Some code adapted from 
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
import flask.ext.login as flask_login

# for image uploading
# from werkzeug import secure_filename
import os, base64

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!

# These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'xuxu'
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

# begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT EMAIL FROM USER")
users = cursor.fetchall()


def getUserList():
    cursor = conn.cursor()
    cursor.execute("SELECT EMAIL FROM USER")
    return cursor.fetchall()


class User(flask_login.UserMixin):
    pass


@login_manager.user_loader
def user_loader(email):
    users = getUserList()
    if not (email) or email not in str(users):
        return
    user = User()
    user.id = email
    return user


@login_manager.request_loader
def request_loader(request):
    users = getUserList()
    email = request.form.get('email')
    if not (email) or email not in str(users):
        return
    user = User()
    user.id = email
    cursor = mysql.connect().cursor()
    cursor.execute("SELECT PASSWORD FROM USER WHERE EMAIL = '{0}'".format(email))
    data = cursor.fetchall()
    pwd = str(data[0][0])
    user.is_authenticated = request.form['password'] == pwd
    return user


'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''


@app.route('/login', methods=['GET', 'POST'])
def login():
    if flask.request.method == 'GET':
        return '''
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   '''
    # The request method is POST (page is recieving data)
    email = flask.request.form['email']
    cursor = conn.cursor()
    # check if email is registered
    if cursor.execute("SELECT PASSWORD FROM USER WHERE EMAIL = '{0}'".format(email)):
        data = cursor.fetchall()
        pwd = str(data[0][0])
        if flask.request.form['password'] == pwd:
            user = User()
            user.id = email
            flask_login.login_user(user)  # okay login in user
            return flask.redirect(flask.url_for('protected'))  # protected is a function defined in this file

    # information did not match
    return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"


@app.route('/logout')
def logout():
    flask_login.logout_user()
    return render_template('hello.html', message='Logged out')


@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template('unauth.html')


# you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=['GET'])
def register():
    return render_template('register.html', supress='True')


@app.route("/register", methods=['POST'])
def register_user():
    try:
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        dob = request.form.get('dob')
        hometown = request.form.get('hometown')
        gender = request.form.get('gender')
    except:
        print(
            "couldn't find all tokens")  # this prints to shell, end users will not see this (all print statements go to shell)
        return flask.redirect(flask.url_for('register'))
    cursor = conn.cursor()
    test = isEmailUnique(email)
    if test:
        print(cursor.execute("INSERT INTO USER (EMAIL, PASSWORD, FNAME, LNAME, DOB, HOMETOWN, GENDER) "
                             "VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}')".
                             format(email, password, first_name, last_name, dob, hometown, gender)))
        conn.commit()
        # log user in
        user = User()
        user.id = email
        flask_login.login_user(user)
        return render_template('hello.html', name=email, message='Account Created!')
    else:
        print("couldn't find all tokens")
        return flask.redirect(flask.url_for('register'),message="already exists")






def getUIDS():
    cursor = conn.cursor()
    cursor.execute("SELECT UID FROM USER")
    return cursor.fetchall()

def getPhotosFromAlbum(aid):
    cursor = conn.cursor()
    cursor.execute("SELECT DATA, PID, CAPTION FROM PHOTO WHERE AID = {0}".format(aid))
    return cursor.fetchall()  # NOTE list of tuples, [(imgdata, pid), ...]

def getUsersPhotos(uid):
    cursor = conn.cursor()
    aid = getUsersAlbums(uid)
    cursor.execute("SELECT DATA, PID, CAPTION FROM PHOTO WHERE AID = {0}".format(aid))
    return cursor.fetchall()

def getPID(aid):
    cursor = conn.cursor()
    cursor.execute("SELECT PID FROM PHOTO WHERE AID = {0}".format(aid))
    return cursor.fetchall()

def getPIDbycaption(caption):
    cursor = conn.cursor()
    cursor.execute("SELECT PID FROM PHOTO WHERE CAPTION = '{0}'".format(caption))
    return cursor.fetchall()

def getPIDByTags(tag):
    cursor = conn.cursor()
    cursor.execute("SELECT PID FROM ASSOCIATE WHERE HASHTAG = '{0}'".format(tag))
    return cursor.fetchall()

def getPhotosByTags(tag):
    cursor = conn.cursor()
    pid = getPIDByTags(tag)
    cursor.execute("SELECT DATA, PID, CAPTION FROM PHOTO WHERE PID = {0}".format(pid))
    return cursor.fetchall()

def getUsersAlbums(uid):
    cursor = conn.cursor()
    cursor.execute("SELECT AID FROM ALBUM WHERE UID = {0}".format(uid))
    return cursor.fetchall()  # NOTE list of tuples, [(imgdata, pid), ...]

def getUsersAlbumName(uid):
    cursor = conn.cursor()
    cursor.execute("SELECT AID, NAME FROM ALBUM WHERE UID = {0}".format(uid))
    return cursor.fetchall()

def getUsersAlbumsWithName(uid, name):
    cursor = conn.cursor()
    print("SELECT AID FROM ALBUM WHERE UID = {0} AND NAME = '{1}'".format(uid, name))
    cursor.execute("SELECT AID FROM ALBUM WHERE UID = {0} AND NAME = '{1}'".format(uid, name))
    return cursor.fetchall()[0][0]

def getUserIdFromEmail(email):
    cursor = conn.cursor()
    cursor.execute("SELECT UID FROM USER WHERE EMAIL = '{0}'".format(email))
    return cursor.fetchone()[0]


def isEmailUnique(email):
    # use this to check if a email has already been registered
    cursor = conn.cursor()
    if cursor.execute("SELECT EMAIL FROM USER WHERE EMAIL = '{0}'".format(email)):
        # this means there are greater than zero entries with that email
        return False
    else:
        return True

def isTagUnique(tag):
    cursor = conn.cursor()
    if cursor.execute("SELECT HASHTAG FROM TAG WHERE TAG = '{0}'".format(tag)):
        return False
    else:
        return True


def getAllPhoto():
    cursor = conn.cursor()
    cursor.execute("SELECT DATA FROM PHOTO")
    return cursor.fetchall()






# end login code

@app.route('/profile')
@flask_login.login_required
def protected():
    return render_template('hello.html', name=flask_login.current_user.id, message="Here's your profile")


# begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML 
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
    if request.method == 'POST':
        uid = getUserIdFromEmail(flask_login.current_user.id)
        name = request.form.get('name')
        aid = getUsersAlbumsWithName(uid, name)
        imgfile = request.files['photo']
        caption = request.form.get('caption')
        tags = request.form.get('tag')
        tag_list = tags.split(' ')
        print(caption)
        photo_data = base64.standard_b64encode(imgfile.read())
        cursor = conn.cursor()
        print("INSERT INTO PHOTO (DATA, AID, CAPTION) VALUES ('{0}', {1}, '{2}' )".format(photo_data, aid, caption))
        cursor.execute(
            "INSERT INTO PHOTO (DATA, AID, CAPTION) VALUES ('{0}', {1}, '{2}' )".format(photo_data, aid, caption))
        conn.commit()
        for i in range(0,len(tag_list)-1):
            if isTagUnique(tag_list[i]):
                cursor.execute(
                    "INSERT INTO TAG (HASHTAG) VALUES ('{0}')".format(tag_list[i]))
                conn.commit()
                pid = getPIDbycaption(caption)
                cursor.execute(
                    "INSERT INTO ASSOCIATE (HASHTAG, PID) VALUES ('{0}', {1})".format(tag_list[i], pid))
                conn.commit()
            else:
                pid = getPIDbycaption(caption)
                cursor.execute(
                    "INSERT INTO ASSOCIATE (HASHTAG, PID) VALUES ('{0}', {1})".format(tag_list[i], pid))
                conn.commit()
        return render_template('hello.html', name=flask_login.current_user.id, message='Photo uploaded!',
                             photos=getAllPhoto())
        # The method is GET so we return a  HTML form to upload the a photo.
    else:
        return render_template('upload.html')


# end photo uploading code


@app.route('/create', methods=['GET', 'POST'])
@flask_login.login_required
def creat_album():
    if request.method == 'POST':
        uid = getUserIdFromEmail(flask_login.current_user.id)
        aname = request.form.get('name')
        time = request.form.get('time')
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO ALBUM (NAME, UID, DOC) VALUES ('{0}', {1}, '{2}' )".format(aname, uid, time))
        conn.commit()
        return render_template('hello.html', name=flask_login.current_user.id, message='Album Created!',
                               photos=getAllPhoto())
    else:
        return render_template('create.html', name=flask_login.current_user.id,
                               albums=getUsersAlbumName(getUserIdFromEmail(flask_login.current_user.id)))

@app.route('/deletealbum', methods=['GET', 'POST'])
@flask_login.login_required
def delete_album():
    if request.method == 'POST':
        uid = getUserIdFromEmail(flask_login.current_user.id)
        aname = request.form.get('Album_name')
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM ALBUM WHERE (NAME) VALUES ('{0}')".format(aname))
        conn.commit()
        return render_template('hello.html', name=flask_login.current_user.id, message='Album Deleted!',
                                   photos=getAllPhoto())
    else:
        return render_template('create.html', name=flask_login.current_user.id,
                                albums=getUsersAlbumName(getUserIdFromEmail(flask_login.current_user.id)))

@app.route('/deletephoto', methods=['GET', 'POST'])
@flask_login.login_required
def delete_photo():
    if request.method == 'POST':
        caption = request.form.get('caption')
        cursor = conn.cursor()
        pid = getPIDbycaption(caption)
        cursor.execute(
            "DELETE FROM PHOTO WHERE (CAPTION) VALUES ('{0}')".format(caption))
        conn.commit()
        return render_template('hello.html', name=flask_login.current_user.id, message='Photo Deleted!',
                                   photos=getAllPhoto())
    else:
        return render_template('upload.html')



@app.route('/viewy', methods=['POST'])
@flask_login.login_required
def view_your_photo():
    tags = request.form.get('tag')
    list_tag = tags.split(' ')
    return render_template('hello.html', name=flask_login.current_user.id, message='Photo searched!',
                               photos=getAllPhoto())


@app.route('/viewall', methods=['POST'])
def view_all_photo():
    tags = request.form.get('tag')
    list_tag = tags.split(' ')
    return render_template('hello.html', name=flask_login.current_user.id, message='Photo searched!',
                            photos=getAllPhoto())





@app.route("/addfriends", methods=['GET', 'POST'])
@flask_login.login_required
def add_friends():
    if request.method == 'POST':
        email = request.form.get('email')
        if isEmailUnique(email):
            return render_template('hello.html', name=flask_login.current_user.id, message='Friend does not exist!',
                                  photos=getAllPhoto())
        else:
            uid2 = getUserIdFromEmail(email)
            uid1 = getUserIdFromEmail(flask_login.current_user.id)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO FRIENDSHIP (UID1, UID2) VALUES ({0}, {1})".format(uid1, uid2))
            conn.commit()
            return render_template('hello.html', name=flask_login.current_user.id, message='Friend added!',
                                   photos=getAllPhoto())
    # The method is GET so we return a  HTML form to upload the a photo.
    else:
        return render_template('friends.html')
# default page
@app.route("/", methods=['GET'])
def hello():
    return render_template('hello.html', message='Welecome to Photoshare', photos = getAllPhoto())


if __name__ == "__main__":
    # this is invoked when in the shell  you run
    # $ python app.py
    app.run(port=5000, debug=True)
