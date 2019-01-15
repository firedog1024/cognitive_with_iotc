import cv2
import requests
from pprint import pprint
from iothub_client import IoTHubClient, IoTHubTransportProvider, IoTHubMessage
import time
import sys
import random

if len(sys.argv) > 1 and len(sys.argv) < 4:
    print('Error in command arguments.  Command arguments are:\r\n\tpython3 cognitive.py <debug True/False> <frame time in seconds> <use Haas Cascade: True/False> <threshold: 0.1 -> 0.99>\r\nExample:\r\n\tpython3 cognitive.py True 5 True 0.85\r\n')
    exit(0)

CONNECTION_STRING = "<IoT Hub/Central connection string goes here>"
PROTOCOL = IoTHubTransportProvider.MQTT

def send_confirmation_callback(message, result, user_context):
    if debug:
        print('<--- Confirmation received for message with result = {0}\r\n'.format(result))

face_uri = 'http://localhost:5000/face/v1.0/detect?returnFaceAttributes=*'

# adjustable parameters 
imagefile = '' #"faces.jpg"  # if file provided then the file is processed, else camera is used
outputImageFile = 'marked_up_image.jpg' # output frame for debugging
debug = True
use_haar_cascade = True  # if true a Haar cascade test is done on the edge to determine if the frame should be processed by Azure Cognitive
threshold = 0.85  # threshold for positive hit
frame_wait_time = 5  # time between images in seconds

if len(sys.argv) > 1:
    debug = sys.argv[1].lower() == 'true'
    frame_wait_time = int(sys.argv[2])
    use_haar_cascade = sys.argv[3].lower() == 'true'
    threshold = float(sys.argv[4])

# telemetry data
kid = 0
young = 0
middle_age = 0
mature = 0
old = 0
male = 0
female = 0
glasses = 0
bald = 0
beard = 0
happy = False
sad = False
neutral = False
happy_count = 0
neutral_count = 0
sad_count = 0
sales_person_id = 0

# create the haar cascade
faceCascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

# connect to the IoT Hub
client = IoTHubClient(CONNECTION_STRING, PROTOCOL)

while True:
    vc = cv2.VideoCapture(0)

    if imagefile == "":
        if vc.isOpened(): # try to get the first frame
            rval, frame = vc.read()
            if debug:
                cv2.imwrite('debug_capture_image.jpg', frame)
        else:
            rval = False

        vc.release()
    else:
        rval = True

    if rval:
        sales_person_id = random.randint(10001, 10007)

        # check to see if we have any faces with Haar Cascade
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # detect faces in the image
        haar_faces = faceCascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
            flags = cv2.CASCADE_SCALE_IMAGE
        )

        if len(haar_faces) > 0 or not use_haar_cascade:
            if use_haar_cascade:
                print('Found faces in the image with Haar Cascade face detection at Edge.  Performing Azure Cognitive Services face detection\r\n')            
            if imagefile == "":
                jpeg = cv2.imencode(".jpg", frame)[1].tostring()
                newimg = frame
            else:
                with open(imagefile, 'rb' ) as f:
                    jpeg = f.read()
                newimg = cv2.imread(imagefile)

            headers = { 'Content-Type': 'image/jpeg' }
            response = requests.post(face_uri, headers=headers, data=jpeg)
            faces = response.json()

            if debug:
                if len(faces) > 0:
                    print('Azure Cognative Face response:')
                    pprint(faces)
                    print('')
                else:
                    print('No faces found in the image\r\n')

            for face in faces:
                facerect = face['faceRectangle']
                cv2.rectangle(newimg, (facerect['left'], facerect['top']), (facerect['width'] + facerect['left'], facerect['top'] + facerect['height']), (0,255,0), 3)

                faceAttr = face['faceAttributes']

                # age brackets
                # 0 - 17    - kid
                # 18 - 34   - young
                # 35 - 50   - middle_age
                # 50 - 70   - mature
                # 70 - dead - old
                if 0 <= faceAttr['age'] <= 17:
                    kid = kid + 1
                elif 18 <= faceAttr['age'] <= 34:
                    young = young + 1
                elif 35 <= faceAttr['age'] <= 50:
                    middle_age = middle_age + 1
                elif 51 <= faceAttr['age'] <= 70:
                    mature = mature + 1
                elif 71 <= faceAttr['age'] <= 999:
                    old = old + 1

                if faceAttr['gender'] == 'male':
                    male = male + 1
                else:
                    female = female + 1

                if faceAttr['glasses'] != 'NoGlasses':
                    glasses = glasses + 1

                if faceAttr['hair']['bald'] > threshold:
                    bald = bald + 1

                if faceAttr['facialHair']['beard'] > threshold:
                    beard = beard + 1

                emotion = faceAttr['emotion']
                emo_data = ''
                if emotion['happiness'] > threshold:
                    emo_data = '"happy": true'
                    happy_count = happy_count + 1
                elif emotion['sadness'] > 0.33: #threshold:
                    emo_data = '"sad": true'
                    sad_count = sad_count + 1
                else:
                    emo_data = '"neutral": true'
                    neutral_count = neutral_count + 1 

                template = '{{ "kid": {0}, "young": {1}, "middle_age": {2}, "mature": {3}, "old": {4}, "male": {5}, "female": {6}, "glasses": {7}, "bald": {8}, "beard": {9}, "happy_count": {10}, "neutral_count": {11}, "sad_count": {12}, "sales_person_id": {13}, {14} }}'
                msg_data = template.format(kid, young, middle_age, mature, old, male, female, glasses, bald, beard, happy_count, neutral_count, sad_count, sales_person_id, emo_data)
                if debug:
                    print('Telemetry data: {0}\r\n'.format(msg_data))

                cv2.imwrite(outputImageFile, newimg)

                message = IoTHubMessage(msg_data)
                client.send_event_async(message, send_confirmation_callback, None)
                print('---> Message transmitted to Azure IoT Central\r\n')
        else:
            print('No faces found in the image using Haas Cascade face detection at Edge\r\n')

        time.sleep(frame_wait_time)
