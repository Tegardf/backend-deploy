from gtts import gTTS
import cv2
import pytesseract
import base64
import numpy
from flask_cors import CORS,cross_origin
from io import BytesIO
from pytesseract import Output
from PIL import Image
from flask import Flask,render_template, request

pytesseract.pytesseract.tesseract_cmd = r"/app/.apt/usr/bin/tesseract"

app = Flask(__name__)
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

@app.route('/')
@cross_origin()
def home():
    return "home"

@app.route('/submit', methods = ['POST'])
@cross_origin()
def submit():
    PIL_image = get_image()
    image = cv2.cvtColor(numpy.array(PIL_image), cv2.COLOR_RGB2BGR)
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) #gray image
    threshold_img = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    custom_config = r'--oem 3 --psm 6'
    details = pytesseract.image_to_data(threshold_img, output_type=Output.DICT, config=custom_config, lang='eng')
    total_boxes = len(details['text'])
    for sequence_number in range(total_boxes):
        if int(float(details['conf'][sequence_number])) >30:
            (x, y, w, h) = (details['left'][sequence_number], details['top'][sequence_number], details['width'][sequence_number],  details['height'][sequence_number])
            threshold_img = cv2.rectangle(threshold_img, (x, y), (x + w, y + h), (0, 255, 0), 2)
    last_word = ''
    myText = ""
    for word in details['text']:
        if word!='':
            myText += ' ' + word
            last_word = word
        if (last_word!='' and word == '') or (word==details['text'][-1]):
            myText += '\n'
    language = 'en'
    output = gTTS(text=myText, lang=language, slow=False)
    fp = BytesIO()
    output.write_to_fp(fp)
    fp.seek(0)
    audio_output = base64.b64encode(fp.getvalue())
    audio_content = audio_output.decode('UTF-8')
    response = {
        'audio_out':audio_content,
        'text_out':myText
    }
    return response

def get_image():
    data_img = request.json['value_base64']
    data_with_padding = f"{data_img}{'=' * ((4 - len(data_img) % 4) % 4)}"
    return Image.open(BytesIO(base64.b64decode(data_with_padding)))

#start server & app
if __name__ == "__main__":
    app.run(debug=True)