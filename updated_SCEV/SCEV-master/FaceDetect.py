
import os
import numpy as np
import cv2
import json

cascPathface = os.path.dirname(cv2.__file__) + "/data/haarcascade_frontalface_default.xml"
#cascPathface = os.path.dirname(cv2.__file__) + "/data/haarcascade_frontalface_alt2.xml"
FACE_DB = "faces"
LIST_OF_PEOPLE = [x for x in os.listdir(FACE_DB) if x!=".DS_Store"]
#print(LIST_OF_PEOPLE)
scalefactor = 1.1
minneighbors = 7
cropped_face_location = "cropped_faces.npy"
cropped_label_location = "cropped_labels.npy"

def train(cropped_face_location,cropped_label_location):
    train_faces = np.load(cropped_face_location,allow_pickle=True)
    train_labels = np.load(cropped_label_location,allow_pickle=True)
    face_recogniser=cv2.face.LBPHFaceRecognizer_create()
    face_recogniser.train(train_faces,np.array(train_labels))
    return face_recogniser

def load(ls):
    dct = {}
    for i in ls:
        dct[ls.index(i)]=i
    dct = json.dumps(dct,indent=4)
    with open("FaceLabels.json",'w') as f:
        f.write(dct)
def getFaceLabel(ind):
    try:
        with open("FaceLabels.json","r") as f:
            dct = json.load(f)
        return dct[str(ind)]
    except:
        return 'Unknown'

face_detector=cv2.CascadeClassifier(cascPathface)
def face_processing():
    train_faces = []
    train_label = []
    LIST_OF_PEOPLE = [x for x in os.listdir(FACE_DB) if x!=".DS_Store"]
    load(LIST_OF_PEOPLE)
    for index,person_folder in enumerate(LIST_OF_PEOPLE):
        for face_file in os.listdir(os.path.join(FACE_DB,person_folder)): 
            try:
                image = cv2.imread(os.path.join(FACE_DB,person_folder,face_file))
                gray=cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
                faces=face_detector.detectMultiScale(gray,scaleFactor=scalefactor,minNeighbors=minneighbors)
                for face in faces:
                    left,top,width,height=face
                    cropped_face = gray[top:top+height,left:left+width]
                    train_faces.append(cropped_face)
                    train_label.append(index)
            except Exception as e:
                print(f"Error occured: {e}")
                os.remove(os.path.join(FACE_DB,person_folder,face_file))
    np.save("cropped_faces.npy",np.array(train_faces,dtype=object),allow_pickle=True)
    np.save("cropped_labels.npy",np.array(train_label),allow_pickle=True)
    


def recog(cropped_face,threshold):
    label = face_recognizer.predict(cropped_face)
    if(label[1] < threshold):
        return f'{getFaceLabel(label[0])}'
    else:
        return "Unknown"


face_processing()
face_recognizer = train(cropped_face_location,cropped_label_location)

#recog(gray)

def track_faces():       
    k=65
    last = ""
    count = 0
    cam=cv2.VideoCapture(0)
    while(k not in (27,ord('q'),ord('Q'))):
        ret, frames = cam.read()
        frames = cv2.flip(frames, 1)
        gray = cv2.cvtColor(frames, cv2.COLOR_BGR2GRAY)
        faces = face_detector.detectMultiScale(gray,scaleFactor=scalefactor,minNeighbors=minneighbors)
        if len(faces):
            for (left,top,width,height) in faces:
                detected_name = recog(gray[top:top+height,left:left+width],65)
                #detected_name = "sai"
                cv2.rectangle(frames, (left, top), (left+width, top+height), (10, 0, 255), 5)
                frames=cv2.putText(frames,detected_name,(left,top-5), cv2.FONT_HERSHEY_SIMPLEX,1.7,(10, 0, 255))
                #cv2.FONT_HERSHEY_SIMPLEX, 0.7, 
        cv2.imshow('img',frames)
        k=cv2.waitKey(1)
    cv2.destroyAllWindows()
def testFace():
    k=65
    last = ""
    count = 0
    cam=cv2.VideoCapture(0)
    while(k not in (27,ord('q'),ord('Q'))):
        ret, frames = cam.read()
        gray = cv2.cvtColor(frames, cv2.COLOR_BGR2GRAY)
        faces = face_detector.detectMultiScale(gray,scaleFactor=scalefactor,minNeighbors=minneighbors)
        if len(faces):
            for (left,top,width,height) in faces:
                detected_name = recog(gray[top:top+height,left:left+width],75)
                if last == detected_name:count +=1
                else : count = 0
                last = detected_name
                if count > 10:
                    count = 0
                    print("Detected : ",detected_name)
                cv2.rectangle(frames, (left, top), (left+width, top+height), (10, 0, 255), 5)
                frames=cv2.putText(frames,detected_name,(left,top-5), cv2.FONT_HERSHEY_SIMPLEX,1.7,(10, 0, 255))
        cv2.imshow('img',frames)
        k=cv2.waitKey(1)
    cv2.destroyAllWindows()

if __name__ == "__main__":

    #retrain_completely()
    track_faces()
    #face_processing()
    print("training completed")