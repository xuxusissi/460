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
from flask import Flask, Response, request, render_template, redirect, url_for, session
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
app.config['MYSQL_DATABASE_PASSWORD'] = '0000'
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
            session['logged_in'] = True
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
    session['logged_in'] = False
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
        print(cursor.execute("INSERT INTO USER (EMAIL, PASSWORD, FNAME, LNAME, DOB, HOMETOWN, GENDER, CONTRIBUTION) "
                             "VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}', 0)".
                             format(email, password, first_name, last_name, dob, hometown, gender)))
        conn.commit()
        # log user in
        user = User()
        user.id = email
        flask_login.login_user(user)
        return render_template('hello.html', name=email, message='Account Created!')
    else:
        print("couldn't find all tokens")
        return render_template('register.html', message='Already Exists!')



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
    return cursor.fetchall()[0][0]

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
    if cursor.execute("SELECT HASHTAG FROM TAG WHERE HASHTAG = '{0}'".format(tag)):
        return False
    else:
        return True


def getAllPhoto():
    cursor = conn.cursor()
    cursor.execute("SELECT P.DATA,P.CAPTION,P.PID,COUNT(L.DOC) FROM PHOTO P LEFT OUTER JOIN LIKETABLE L ON P.PID=L.PID GROUP BY P.PID")
    return cursor.fetchall()

def getUserLike(pid):
    cursor = conn.cursor()
    print("SELECT DISTINCT L.UID FROM LIKETABLE L WHERE L.PID = {0}".format(pid))
    cursor.execute("SELECT DISTINCT L.UID FROM LIKETABLE L WHERE L.PID = {0} ".format(pid))
    return cursor.fetchall()

def getAllFriendsName(uid):
    cursor=conn.cursor()
    print("SELECT FNAME FROM USER WHERE UID IN (SELECT UID2 FROM FRIENDSHIP WHERE UID1={0})".format(uid))
    cursor.execute("SELECT FNAME FROM USER WHERE UID IN (SELECT UID2 FROM FRIENDSHIP WHERE UID1={0})".format(uid))
    return cursor.fetchall()

def getAllTagPhoto(tag):
    cursor=conn.cursor()
    print("SELECT DATA,CAPTION FROM PHOTO WHERE PID IN (SELECT PID FROM ASSOCIATE WHERE HASHTAG='{0}')".format(tag))
    cursor.execute("SELECT DATA,CAPTION FROM PHOTO WHERE PID IN (SELECT PID FROM ASSOCIATE WHERE HASHTAG='{0}')".format(tag))
    return cursor.fetchall()

def getAllTagsPhoto(tags):
    list
    for t in tags:
        photo = getAllTagPhoto(t)
        list.add(photo)


def mostTag():
    cursor=conn.cursor()
    cursor.execute("SELECT HASHTAG FROM TAG GROUP BY HASHTAG ORDER BY COUNT(*) DESC LIMIT 5")
    return cursor.fetchall()

def getPhotowithMostTag(): # need to be modified
    cursor = conn.cursor()
    most = mostTag() #list
    cursor.execute("SELECT PID FROM ASSOCIATE WHERE HASHTAG IN most") # a string = list
    return cursor.fetchall()

def getYourTagPhoto(tag,uid):
    cursor=conn.cursor()
    print("SELECT P.CAPTION FROM PHOTO P,ALBUM A WHERE P.AID=A.AID AND A.UID={0} AND PID IN (SELECT PID FROM ASSOCIATE WHERE HASHTAG='{1}')".format(uid,tag))
    cursor.execute("SELECT DATA,CAPTION FROM PHOTO P,ALBUM A WHERE P.AID=A.AID AND A.UID={0} AND PID IN (SELECT PID FROM ASSOCIATE WHERE HASHTAG='{1}')".format(uid,tag))
    return cursor.fetchall()

def getAIDFromPID(pid):
    cursor=conn.cursor()
    print(cursor.execute("SELECT AID FROM PHOTO WHERE PID={0}".format(pid)))
    cursor.execute("SELECT AID FROM PHOTO WHERE PID={0}".format(pid))
    return cursor.fetchall()[0][0]

def getUIDFromPID(pid):
    aid=getAIDFromPID(pid)
    print(cursor.execute("SELECT UID FROM ALBUM WHERE AID={0}".format(aid)))
    cursor.execute("SELECT UID FROM ALBUM WHERE AID={0}".format(aid))
    return cursor.fetchall()[0][0]

def selfComment(uid,pid):
    uid_p=getUIDFromPID(pid)
    print(uid_p)
    print(uid)
    print(pid)
    if uid==uid_p:
        return True
    else:
        return False

def activeUsers():
    cursor=conn.cursor()
    cursor.execute("SELECT FNAME,LNAME FROM USER ORDER BY CONTRIBUTION DESC LIMIT 10")
    return cursor.fetchall()

def isCommentUnique(comment):
    cursor = conn.cursor()
    if cursor.execute("SELECT CONTENT FROM COMMENT WHERE CONTENT = '{0}'".format(comment)):
        return False
    else:
        return True

def user_by_comment(content):
    cursor=conn.cursor()
    cursor.execute("SELECT FNAME,LNAME FROM USER WHERE UID IN (SELECT UID FROM COMMENT WHERE CONTENT='{0}') GROUP BY UID ORDER BY COUNT(*) DESC".format(content))
    return cursor.fetchall()
# end login code

@app.route('/profile')
@flask_login.login_required
def protected():
    uid=getUserIdFromEmail(flask_login.current_user.id)
    return render_template('hello.html', name=flask_login.current_user.id, message="Here's your profile",
                           photos=getAllPhoto(),activities=activeUsers())


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
        tag = request.form.get('tag')
        tag_list = tag.split(' ')
        print(tag_list)
        photo_data = base64.standard_b64encode(imgfile.read())
        cursor = conn.cursor()
        print("INSERT INTO PHOTO (DATA, AID, CAPTION) VALUES ('{0}', {1}, '{2}' )".format(photo_data, aid, caption))
        cursor.execute(
            "INSERT INTO PHOTO (DATA, AID, CAPTION) VALUES ('{0}', {1}, '{2}' )".format(photo_data, aid, caption))
        cursor.execute("UPDATE USER SET CONTRIBUTION=CONTRIBUTION+1 WHERE UID={0}".format(uid))
        conn.commit()
        for i in range(0,len(tag_list)):
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
                             photos=getAllPhoto(),tags=mostTag(),activities=activeUsers())
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
                               photos=getAllPhoto(), albums=getUsersAlbumName(uid), tags=mostTag(),activities=activeUsers())
    else:
        return render_template('create.html', name=flask_login.current_user.id,
                               albums=getUsersAlbumName(getUserIdFromEmail(flask_login.current_user.id)))

@app.route('/deletealbum', methods=['GET', 'POST'])
@flask_login.login_required
def delete_album():
    if request.method == 'POST':
        uid=getUserIdFromEmail(flask_login.current_user.id)
        aname = request.form.get('name')
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM ALBUM WHERE NAME = '{0}' AND UID = {1}".format(aname, uid))
        conn.commit()
        return render_template('hello.html', name=flask_login.current_user.id, message='Album Deleted if you are the owner of the album!',
                                   photos=getAllPhoto(),tags=mostTag(),activities=activeUsers())
    else:
        return render_template('create.html', name=flask_login.current_user.id,
                                albums=getUsersAlbumName(getUserIdFromEmail(flask_login.current_user.id))
                               )

@app.route('/deletephoto', methods=['GET', 'POST'])
@flask_login.login_required
def delete_photo():
    if request.method == 'POST':
        uid=getUserIdFromEmail(flask_login.current_user.id)
        caption = request.form.get('caption')
        cursor = conn.cursor()
        pid = getPIDbycaption(caption)
        cursor.execute(
            "DELETE FROM PHOTO WHERE CAPTION='{0}' AND AID IN (SELECT AID FROM ALBUM WHERE UID = {1})".format(caption, uid))
        conn.commit()
        return render_template('hello.html', name=flask_login.current_user.id, message='Photo Deleted if you are the owner of the photo!',
                                   photos=getAllPhoto(),tags=mostTag(),activities=activeUsers())
    else:
        return render_template('upload.html')



@app.route('/viewy', methods=['POST'])
@flask_login.login_required
def view_your_photo():
    tag = request.form.get('tag')
    uid=getUserIdFromEmail(flask_login.current_user.id)
    return render_template('viewyour.html', tag_photo_your=getYourTagPhoto(tag,uid))


@app.route('/viewall', methods=['POST'])
def view_all_photo():
    tag = request.form.get('tag')
    if isTagUnique(tag):
        return render_template('hello.html', name=flask_login.current_user.id, message='No photo with this tag!',
                                  photos=getAllPhoto(),tags=mostTag(),activities=activeUsers())
    else:
        return render_template('viewall.html', tag_photo_all=getAllTagPhoto(tag))

@app.route('/searchtags', methods=['GET','POST'])
def search_by_tags():
    if request.method=='POST':
        tag = request.form.get('tag')
        tag = tag.split(" ")
        print(tag)
        list_photos = []
        for t in tag:
            if isTagUnique(t):
                list_photos += getPhotosByTags(t)
        print(list_photos)
        if list_photos != []:
            return render_template("searchtags.html", message="Here are all photos with tags", listphotos=list_photos)
        else:
            return render_template("hello.html", name=flask_login.current_user.id, message='No photo with this tag!',
                                      photos=getAllPhoto(),tags=mostTag(),activities=activeUsers())
    else:
        return render_template("hello.html", name=flask_login.current_user.id, photos=getAllPhoto(),tags=mostTag(),activities=activeUsers())




@app.route("/addfriends", methods=['GET', 'POST'])
@flask_login.login_required
def add_friends():
    if request.method == 'POST':
        email = request.form.get('email')
        if isEmailUnique(email):
            uid1 = getUserIdFromEmail(flask_login.current_user.id)
            return render_template('friends.html',friends=getAllFriendsName(uid1), message = 'User does not exist.')
        else:
            uid2 = getUserIdFromEmail(email)
            uid1 = getUserIdFromEmail(flask_login.current_user.id)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO FRIENDSHIP (UID1, UID2) VALUES ({0}, {1})".format(uid1, uid2))
            conn.commit()
            return render_template('friends.html',friends=getAllFriendsName(uid1),message='Friends added!')
    # The method is GET so we return a  HTML form to upload the a photo.
    else:
        return render_template('friends.html',friends=getAllFriendsName(getUserIdFromEmail(flask_login.current_user.id)))


# default page

@app.route('/comment', methods=['POST'])
def add_comment():
    pid=request.form.get('pid')
    content=request.form.get('comment')
    date=request.form.get('date')
    if session.get('logged_in'):
        uid = getUserIdFromEmail(flask_login.current_user.id)
        if selfComment(uid,pid):
            return render_template('hello.html',message='you cannot leave comments to your own photo',photos=getAllPhoto(),name=flask_login.current_user.id,tags=mostTag(),activities=activeUsers())
        else:
            uid = getUserIdFromEmail(flask_login.current_user.id)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO COMMENT(UID,PID,DOC,CONTENT) VALUES({0},{1},'{2}','{3}')".format(uid, pid, date, content))
            cursor.execute("UPDATE USER SET CONTRIBUTION=CONTRIBUTION+1 WHERE UID={0}".format(uid))
            conn.commit()
            return render_template('hello.html', message='Your comment is added!', photos=getAllPhoto(),
                                   name=flask_login.current_user.id, tags=mostTag(), activities=activeUsers())
    else:
        print("not logged in")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO COMMENT (UID,PID,DOC,CONTENT) VALUES ({0}, {1}, '{2}','{3}')".format(0, pid, date, content))
        conn.commit()
        return render_template('hello.html', message='Your comment is added anonymously!', photos=getAllPhoto(), tags=mostTag(), activities=activeUsers())



@app.route('/searchcomment', methods=['POST'])
@flask_login.login_required
def search_comment():
    content=request.form.get('content')
    if isCommentUnique(content):
        return render_template("hello.html",message="comments do not exist")
    else:
        return render_template("hello.html",message="users found!",contributors=user_by_comment(content))

@app.route('/like', methods=['POST'])
@flask_login.login_required
def likephoto():
    uid=getUserIdFromEmail(flask_login.current_user.id)
    pid=request.form.get('pid')
    doc=request.form.get('date')
    cursor=conn.cursor()
    print(uid)
    cursor.execute("INSERT INTO LIKETABLE(UID,PID,DOC) VALUES({0},{1},'{2}')".format(uid,pid,doc))
    conn.commit()
    return render_template('hello.html',message='You liked this photo!',photos=getAllPhoto(), ulikes=getUserLike(pid), name=flask_login.current_user.id,tags=mostTag(),activities=activeUsers())



@app.route("/", methods=['GET'])
def hello():
    return render_template('hello.html', message='Welcome to Photoshare!', photos = getAllPhoto(),tags=mostTag(),activities=activeUsers())


if __name__ == "__main__":
    # this is invoked when in the shell  you run
    # $ python app.py
    app.run(port=5000, debug=True)
