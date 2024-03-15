from flask import Flask, render_template, send_file, request, redirect, flash, session, url_for
import sqlite3
import hashlib
from PIL import Image
import datetime
import jwt
from io import BytesIO
import base64
import random
import string
import os
from moviepy.editor import *

N = 7

app = Flask(__name__)

app.config['SECRET_KEY'] = 'FHDJAKLFJIEWAFNA'
app.config['SESSION_COOKIE_PERMANENT'] = True


UPLOAD_FOLDER = 'timeline'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def generate_jwt_token(username):
    payload = {
        'username': username,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)  # Token expires in 30 minutes
    }
    token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')  # Use encode function from jwt module
    return token

def verify_jwt_token(token):
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])  # Use decode function from jwt module
        return payload['username']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

salt = "krish"

def create_video():
    clips = []
    image_folder = 'timeline'
    for f in os.listdir(image_folder):
        if os.path.isfile(os.path.join(image_folder, f)):
            clips.append(ImageClip(os.path.join(image_folder, f)).set_duration(2))


    # clip1 = ImageClip("uploads/slide_down.png").set_duration(2)
    # clip2 = ImageClip("uploads/slide_up.png").set_duration(2)
    # clip4 = ImageClip("uploads/slide_right.png").set_duration(2)
    # clip3 = ImageClip("uploads/slide_left.png").set_duration(2)

    print(type("uploads/slide_up.png"))
    # print(type(clip1))

    # clips.append(clip1)
    # clips.append(clip2)
    # clips.append(clip3)
    # clips.append(clip4)

    video_clips = concatenate_videoclips(clips, method="compose")

    print(type(video_clips))

    video_clips.write_videofile("static/video/output_video.mp4", codec="libx264", fps=24, remove_temp=True)


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # connect to the database
        connection = sqlite3.connect('user_data.db')
        cursor = connection.cursor()
        
        # retrieve data from the form
        name = request.form['name']
        password = request.form['password']
        # print it on the terminal(for debugging)
        print(name, password)
        
        hashed_password = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
        
        # check if the user is correct by running the query, if the user is valid then go to the user index page else show an alert
        query = "SELECT username, password FROM users where username= '"+name+"' and password='"+hashed_password+"' "
        cursor.execute(query)
        
        results = cursor.fetchall()
        
        if len(results) == 0:
            # print("Incorrent credentials, Try again")
            # flash("Invalid Credentials")
            return render_template('login.html', error = True)
        else:
            # session['username'] = name
            session['token'] = generate_jwt_token(name)
            return redirect("/home ")
        
    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # connect to the server
        connection = sqlite3.connect('user_data.db')
        cursor = connection.cursor()
        
        # get data from the html form
        firstName = request.form['firstn']
        lastName = request.form['lastn']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        #hash the password before storing 
        password_hash = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
        
        #print the data in terminal for debugging
        print(firstName, lastName, username, email, password_hash)
        
        # insert the data into the database
        query = " INSERT INTO users VALUES ('"+firstName+"' , '"+lastName+"' , '"+username+"', '"+email+"', '"+password_hash+"') "
        cursor.execute(query)
        connection.commit()
        
        return redirect("/upload")
        
    return render_template('signup.html')

@app.route("/upload",methods=["POST","GET"])
def upload():
    token = session.get('token')
    if not token:
        return redirect('/login')
    username = verify_jwt_token(token)
    if not username:
        return redirect('/login')
    
    if request.method == 'POST':
        
        connection = sqlite3.connect('user_data.db')
        cursor = connection.cursor()
        
        files = request.files.getlist('images[]')
        # store the images into sql database
        for file in files:
            imageFile = file.read()
            filename = file.filename
            
            myName = username
            
            query = "INSERT INTO images (username, image, imageName) VALUES (?, ?, ?)"
            
            cursor.execute(query, (myName, sqlite3.Binary(imageFile), filename))
            
        connection.commit()
        return redirect("/home")
        
    return render_template('/upload.html')


@app.route("/home")
def home():
    token = session.get('token')
    if not token:
        return redirect('/login')
    username = verify_jwt_token(token)
    if not username:
        return redirect('/login')
    
    connection = sqlite3.connect("user_data.db")
    cursor = connection.cursor()
    
    query_1 = "SELECT * FROM users WHERE username = '"+username+"'" # for user data
    query_2 = "SELECT imageName FROM images WHERE username = '"+username+"'" # for getting all the images uploaded by the user 
    query_3 = "SELECT image FROM images WHERE username = '"+username+"'" # for getting all the images uploaded by the user 

    

    cursor.execute(query_1)
    user_data = cursor.fetchall()

    cursor.execute(query_2)
    imageNames = cursor.fetchall()

    cursor.execute(query_3)
    images = cursor.fetchall()

    connection.close()  
    
    name = user_data[0][0]
    lastname = user_data[0][1]
    email = user_data[0][3]

    images_base64 = []
    image_names = []

    # print(image)

    for image in images:
        image = image[0]
        # print(type(image))
        # binData = bytes.fromhex(image)
        # print(image_name[0])
        # image_names.append(image_name[0])
        image_base64 = base64.b64encode(image).decode('utf-8')
        images_base64.append((image_base64))

    for image_name in imageNames:
        image_names.append(image_name[0])

    # return render_template('index.html',images_data = images_base64)
    # print(image_names)
    # convert the image data into a format that can be displayed on the html page
    # print(len(images_base64))

    return render_template("home.html", username = name, lastname = lastname, email = email, images_data = images_base64, image_names = image_names, total_images = len(images_base64))
    
    # return render_template("home.html", username = name)

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/video')
def video():
    return render_template('video.html')


@app.route('/edit',methods=["POST","GET"])
def edit():
    token = session.get('token')
    if not token:
        return redirect('/login')
    
    username = verify_jwt_token(token)

    if not username:
        return redirect('/login')   
    
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()

    cursor.execute("SELECT image FROM images WHERE username='"+username+"'")

    image_data = cursor.fetchall()
    images_base64 = []

    conn.close()

    for image in image_data:
        image = image[0]
        image_base64 = base64.b64encode(image).decode('utf-8')
        images_base64.append((image_base64))

    if request.method == 'POST':
        if 'files[]' not in request.files:
            return 'No file part'

        files = request.files.getlist('files[]')

        for file in files:
            # give it a random filename
            print(type(file))
            res = ''.join(random.choices(string.ascii_uppercase +
                                string.digits, k=N))

            if file.filename == '':
                return 'No selected file'

            if file:
                filename = str(res) + ".png"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            # make the video and save it
        create_video()
        print("video is succesfully made")
        return redirect(url_for(video))

    
    

    return render_template('editor.html', images = images_base64)

@app.route('/logout')
def logout():
    session.pop('token', None) 
    return redirect('/login')

@app.route('/image/<int:image_id>')
def get_image(image_id):
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()
    username = session['username']
    cursor.execute("SELECT * FROM images WHERE username='"+username+"'")
    image_data = cursor.fetchall()
    conn.close()
    return send_file(BytesIO(image_data[0][1]), mimetype='image/jpeg')

if __name__ == '__main__':
    app.run(debug=True)

