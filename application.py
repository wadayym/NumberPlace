import os
import sys
import time
import datetime
import glob
import base64
import numpy as np
import cv2
from flask import Flask, render_template, request, redirect, url_for, send_from_directory

from subOCRProcessing import find_square
from subNumberPlace import subNP

print(sys.version)
app = Flask(__name__)

app.config.update(
    UPLOADED_PATH='./uploads'
)

class ProcessSettings:
    def __init__(self):
        self.filename_input = ""
        self.process_name = ""
    
    def set(self, request):
        self.process_name = request.form['process']

    def get_process_name(self):
        return self.process_name

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
PlaceName = [['00'] * 9 for i in range(9)]
for i in range(9):
    for j in range(9):
        PlaceName[i][j] = str(i * 10 + j)
bComplete = False

@app.route('/', methods=['POST', 'GET'])
def index():
    ac = request.endpoint
    print("endpoint:"+ac)
    if request.method == 'POST': 
        ps.set(request)
        if ps.get_process_name() =='手入力':
            return redirect('/numberplace')

        if ps.get_process_name() == "カメラ撮影":
            return render_template('camera.html')
        
    return render_template('index.html')

@app.route('/numberplace', methods=['POST', 'GET'])
def numberplace():
    bComplete = False
    return render_template('numberplace.html', PlaceName = PlaceName, bComplete = bComplete)

@app.route('/resolve', methods=['GET', 'POST'])
def send():
    if request.method == 'POST':
        numberPlace = subNP()
        for i in range(9):
            for j in range(9):
                numberPlace.set(i, j, int(request.form[PlaceName[i][j]]))
        numberPlace.check_all()
        outTable, inTable = numberPlace.get()
        bComplete = True
        return render_template('numberplace.html', PlaceName = PlaceName, IN_Table = inTable, NP_Table = outTable, bComplete = bComplete)
    else:
        return redirect(url_for('numberplace'))

@app.route("/camera", methods=['POST', 'GET'])
def capture():
    if request.method == 'POST':
        ps.save_capture_image()
        return redirect('/result')
    return render_template('camera.html')

@app.route('/result')
def result():
    result_file_name = ps.process()
    return render_template('result.html', result_url = result_file_name)

if __name__ == '__main__':
    for p in glob.glob(app.config['UPLOADED_PATH']+'/**', recursive=True):
        if os.path.isfile(p):
            #os.remove(p)
            #print('not removed : '+p)
            pass
    app.run(debug=True)    