import os
import sys
import time
import uuid
import datetime
import glob
import base64
import numpy as np
import cv2
from flask import Flask, render_template, request, redirect, url_for, send_from_directory

from subOCRProcessing import find_square

print(sys.version)
app = Flask(__name__)

app.config.update(
    UPLOADED_PATH='./uploads'
)

class ProcessSettings:
    def __init__(self):
        self.filename_input = ""

    def save_capture_image(self):
        self.filename_input = os.path.join(app.config['UPLOADED_PATH'], datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')) + '_input.jpg'
        #aram_dict['file_name'] = filename
        base64_img = request.form['image']
        #print(type(base64_png))
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        if not base64_img.startswith('data:image/jpeg;base64,'):
            print("Invalid base64 image format")
            return
        print("type & size of base64_img:"+str(type(base64_img))+", "+str(sys.getsizeof(base64_img)))
        code = base64.b64decode(base64_img.split(',')[1])  # remove header 
        nparr = np.frombuffer(code, np.uint8)
        image_decoded = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        cv2.imwrite(self.filename_input, image_decoded)

    def process(self):
        start_time = time.perf_counter()
        filename_result = os.path.join(app.config['UPLOADED_PATH'], datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')) + '_result.png'
        # ここで処理する
        find_square(self.filename_input, filename_result)
        current_time = time.perf_counter()
        print("processing time = {:.3f}sec".format(current_time - start_time))
        return filename_result
    
ps = ProcessSettings()

@app.route('/', methods=['POST', 'GET'])
def index():
    ac = request.endpoint
    print("endpoint:" + ac)
    ps.save_capture_image()
    return redirect('/result')

@app.route('/result')
def result():
    filename_result = ps.process()
    return render_template('result.html', result_url = filename_result)

if __name__ == '__main__':
    for p in glob.glob(app.config['UPLOADED_PATH']+'/**', recursive=True):
        if os.path.isfile(p):
            #os.remove(p)
            #print('not removed : '+p)
            pass
    app.run(debug=True)    