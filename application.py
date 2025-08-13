import os
import sys
import time
import datetime
import glob
import base64
import numpy as np
import cv2
from flask import Flask, render_template, request, redirect, url_for, send_from_directory

import subOCRProcessing as subOCR
import subNumberPlace as subNP

print(sys.version)
app = Flask(__name__)

app.config.update(
    UPLOADED_PATH='./uploads'
)

class ProcessSettings:
    def __init__(self):
        self.process_name = ""

        self.filename_input = ""
        self.filename_result = ""
        self.filename_work = ""
    
    def get_filename_input(self):
        return self.filename_input
    
    def get_filename_result(self):
        return self.filename_result
    
    def get_filename_work(self):
        return self.filename_work
    
    def save_capture_image(self):
        filename = os.path.join(app.config['UPLOADED_PATH'], datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
        self.filename_input  = filename + '_input.jpg'
        self.filename_result = filename + '_result.png'
        self.filename_work   = filename + '_work.png'
        base64_img = request.form['image']
        #print(type(base64_png))
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        if not base64_img.startswith('data:image/jpeg;base64,'):
            print("Invalid base64 image format")
            return
        print("type & size of base64_img:"+str(type(base64_img))+", "+str(sys.getsizeof(base64_img)))
        code = base64.b64decode(base64_img.split(',')[1])  # remove header 
        nparray = np.frombuffer(code, np.uint8)
        image_decoded = cv2.imdecode(nparray, cv2.IMREAD_COLOR)
        cv2.imwrite(self.filename_input, image_decoded)
    
ps = ProcessSettings()
PlaceName = [['00'] * 9 for i in range(9)]
for i in range(9):
    for j in range(9):
        PlaceName[i][j] = str(i * 10 + j)

@app.route('/', methods=['POST', 'GET'])
def index():
    ac = request.endpoint
    print("endpoint:"+ac)
    if request.method == 'POST': 
        if request.form['process'] =='手入力':
            print("process:"+"手入力")
            return redirect('/numberplace')

        if request.form['process'] == "画像入力":
            print("process:"+"画像入力")
            ps.save_capture_image()
            return redirect('/result')
        
    return render_template('index.html')

@app.route('/numberplace', methods=['POST', 'GET'])
def numberplace():
    return render_template('numberplace.html', PlaceName = PlaceName)

@app.route('/solution', methods=['GET', 'POST'])
def solution():
    if request.method == 'POST':
        NPClass = subNP.NumberPlace()
        for i in range(9):
            for j in range(9):
                NPClass.set(i, j, int(request.form[PlaceName[i][j]]))
        NPClass.check_all()
        outTable, inTable = NPClass.get()
        if 0 in outTable:
            print("Processing failed. Result contains zero.")
            return render_template('error.html', message="解けませんでした。")
        return render_template('solution.html', PlaceName = PlaceName, IN_Table = inTable, NP_Table = outTable)
    return redirect(url_for('numberplace'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOADED_PATH'], filename)

@app.route('/result')
def result():
    start_time = time.perf_counter()
    outTable, inTable = subOCR.find_square(ps.get_filename_input(), ps.get_filename_result(), ps.get_filename_work())
    current_time = time.perf_counter()
    print("processing time = {:.3f}sec".format(current_time - start_time))
    if 0 in outTable:
        print("Processing failed. Result contains zero.")
        return render_template('error.html', message="解けませんでした。", work_file=ps.get_filename_work())
    print("Processing completed successfully.")

    os.remove(ps.get_filename_input())
    print(f"{ps.get_filename_input()} を削除しました。")
    os.remove(ps.get_filename_result())
    print(f"{ps.get_filename_result()} を削除しました。")
    os.remove(ps.get_filename_work())
    print(f"{ps.get_filename_work()} を削除しました。")
    
    return render_template('solution.html', PlaceName = PlaceName, IN_Table = inTable, NP_Table = outTable)

if __name__ == '__main__':
    for p in glob.glob(app.config['UPLOADED_PATH']+'/**', recursive=True):
        if os.path.isfile(p):
            #os.remove(p)
            #print('not removed : '+p)
            pass
    app.run(debug=True)    