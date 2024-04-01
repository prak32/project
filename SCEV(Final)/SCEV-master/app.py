from flask import Flask, render_template, request, Response, jsonify, session, redirect, url_for
import os
import cv2
from werkzeug.utils import secure_filename
import json
import FaceDetect
import random
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "password123"

reqDict = {"status": 0, "name": "", "mail": "", "profile": ""}
otpValue = 0
ft = {"status": 0, "index": 0}
voted_users = set()  # Set to keep track of users who have voted

def sendMail(otpdata, mail):
    try:
        mail_content = f'''Hello,
        Your OTP is : {otpdata}
        Thank You
        '''
        # The mail addresses and password
        sender_address = 'sthaprak24241@gmail.com'
        sender_pass = 'ijym okyd obyo aenx'
        receiver_address = mail
        # Setup the MIME
        message = MIMEMultipart()
        message['From'] = sender_address
        message['To'] = receiver_address
        message['Subject'] = 'OTP for voting'  # The subject line
        # The body and the attachments for the mail
        message.attach(MIMEText(mail_content, 'plain'))
        # Create SMTP session for sending the mail
        session = smtplib.SMTP('smtp.gmail.com', 587)  # use gmail with port
        session.starttls()  # enable security
        session.login(sender_address, sender_pass)  # login with mail_id and password
        text = message.as_string()
        session.sendmail(sender_address, receiver_address, text)
        session.quit()
        print('Mail Sent')
    except Exception as e:
        print(e)

def profileDb(name, info):
    m_path = os.getcwd()
    j_path = os.path.join(m_path, 'profileDb.json')
    data = ""
    try:
        with open(j_path, "r") as f:
            data = json.load(f)
    except:
        data = {}
    data[name] = info
    with open(j_path, 'w') as j_file:
        json.dump(data, j_file, indent=4)

def save_file(name, path, obj):
    f_path = os.path.join(path, name)
    if not os.path.exists(f_path):
        os.makedirs(f_path)
    for file in obj:
        filename = secure_filename(file.filename)
        f_path1 = f_path
        f_path1 = os.path.join(f_path1, filename)
        if not os.path.exists(f_path1):
            file.save(f_path1)

def save_voted_user(name):
    try:
        voted_users.add(name)  # Add the user to the set of voted users
        with open("voted_users.json", "w") as f:
            json.dump(list(voted_users), f)  # Save the set to a JSON file
    except Exception as e:
        print("Error saving voted user:", e)

app = Flask(__name__, template_folder='templates')

@app.route('/', methods=["GET", "POST"])
def server_app():
    global reqDict
    global st
    ft["status"] = 0
    if request.method == "GET":
        return render_template("index.html")
    else:
        data = request.data.decode('utf-8')
        print(data)
        return ""

@app.route('/main', methods=["GET", "POST"])
def main():
    global reqDict
    if request.method == "GET":
        reqDict = {"status": 0, "name": "", "mail": "", "profile": ""}
        return render_template("main.html")
    else:
        return reqDict

def gen():
    global reqDict
    global st
    face_detector = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
    cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    count = 0
    last = ""
    while True:
        try:
            _, image = cam.read()
            image = cv2.flip(image, 1)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            faces = face_detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=7)
            if len(faces):
                for (left, top, width, height) in faces:
                    detected_name = FaceDetect.recog(gray[top:top + height, left:left + width], 55)
                    cv2.rectangle(image, (left, top), (left + width, top + height), (10, 0, 255), 7)
                    image = cv2.putText(image, detected_name, (left, top - 5), cv2.FONT_HERSHEY_TRIPLEX, 2.4, (255, 0, 0), 2, cv2.LINE_AA)
                    with open("profileDb.json", "r") as f:
                        data = json.load(f)
                    if not "Unknown" in detected_name:
                        if detected_name in voted_users:
                            reqDict = {"status": 0, "name": "", "mail": "", "profile": ""}
                            message = f"{detected_name} has already voted!"
                            cv2.putText(image, message, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
                        else:
                            if detected_name == "admin":
                                reqDict["status"] = 2
                            else:
                                reqDict["mail"] = data[detected_name]["mail"]
                                reqDict["profile"] = data[detected_name]["profile"]
                                reqDict["status"] = 1
                                reqDict["name"] = detected_name
            else:
                reqDict = {"status": 0, "name": "", "mobile": "", "profile": ""}
            ret, jpeg = cv2.imencode('.jpg', image)
            frame = jpeg.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
        except Exception as e:
            print("Error : ", e)

@app.route('/video_feed')
def video_feed():
    return Response(gen(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/form', methods=["GET", "POST"])
def form():
    try:
        if request.method == 'POST':
            if 'face files[]' not in request.files or 'profile files[]' not in request.files:
                print('No file part')
                return render_template("form.html")
            face_files = request.files.getlist('face files[]')
            profile_files = request.files.getlist('profile files[]')
            name = request.form.get("uname")
            mail = request.form.get("mail")
            m_path = os.getcwd()
            f_path = os.path.join(m_path, 'faces')
            a_path = os.path.join(m_path, 'static\\images')
            i_path = os.path.join('static\\images\\' + name, secure_filename(profile_files[0].filename))
            save_file(name, f_path, face_files)
            save_file(name, a_path, profile_files)
            FaceDetect.face_processing()
            profileDb(name, {"mail": mail, "profile": i_path, "hasVoted": False})
    except Exception as e:
        print(e)
    return render_template("form.html")


@app.route('/profile', methods=["GET", "POST"])
def profile():
    global reqDict
    ft["status"] = 6
    if request.method == "GET":
        return render_template("profile.html")
    else:
        data = request.data.decode('utf-8')
        if "party" in data:
            party = data.split("=")[1]
            print(party)
            m_path = os.getcwd()
            j_path = os.path.join(m_path, 'result.json')
            data = ""
            try:
                with open(j_path, "r") as f:
                    data = json.load(f)
            except:
                data = {"result": []}
            data["result"].append(party)
            with open(j_path, 'w') as j_file:
                json.dump(data, j_file, indent=4)
            save_voted_user(reqDict["name"])  # Save the name of the user who voted
        return reqDict

@app.route('/otp', methods=["GET", "POST"])
def otp():
    global otpValue
    global reqDict
    if request.method == "GET":
        otpValue = random.randint(1000, 9999)
        sendMail(otpValue, reqDict["mail"])
        print(otpValue)
        ft["status"] = 8
        return render_template('otpcheck.html')
    if request.method == "POST":
        try:
            otp = int(request.data.decode("utf-8"))
            print('Got OTP :', otp)
            print("Generated OTP :", otpValue)
            if otp == otpValue:
                return {"data": 1}
            else:
                ft["status"] = 7
                return {"data": 0}
        except Exception as e:
            print(e)
            return {"data": 0}
    return ""

@app.route('/admin', methods=["GET", "POST"])
def admin():
    if request.method == "GET":
        return render_template("admin_login.html")
    elif request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            # Authentication successful, store user session
            session['admin_logged_in'] = True
            # Redirect the admin to the result page after successful login
            return redirect(url_for('result'))
        else:
            # Authentication failed, redirect back to login page with error message
            return render_template("admin_login.html", error="Invalid username or password")

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        # If user is not authenticated, redirect to admin login page
        return redirect(url_for('admin'))
    else:
        # User is authenticated, redirect to the result page
        return redirect(url_for('result'))

# Add this line to enable sessions in your Flask app
app.secret_key = os.urandom(24)

@app.route('/result', methods=["GET", "POST"])
def result():
    if not session.get('admin_logged_in'):
        # If user is not authenticated, redirect to admin login page
        return redirect(url_for('admin'))
    elif request.method == "GET":
        return render_template("result.html")
    else:
        data = request.data.decode("utf-8")
        print(data)
        if data == "clear":
            with open("result.json", "w") as f:
                json.dump({"result": []}, f)

        if data == "get":
            try:
                resList = []
                with open("result.json", "r") as f:
                    resList = json.load(f)
                resList = resList["result"]
                print(resList)
                resData = []
                names = []
                for i in resList:
                    if i not in names:
                        resData.append([i, resList.count(i)])
                        names.append(i)
                print(names)
                return jsonify(resData)
            except:
                pass
        session.pop('admin_logged_in', None)
        return jsonify([["Party Names", "Votes"], []])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
