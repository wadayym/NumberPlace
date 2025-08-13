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

if not os.path.exists(app.config['UPLOADED_PATH']):
    os.makedirs(app.config['UPLOADED_PATH'])
    print('Created directory: ' + app.config['UPLOADED_PATH'])

# Initialize PlaceName with 9x9 grid of strings
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
    filename = os.path.join(app.config['UPLOADED_PATH'], datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    filename_input = filename + '_input.jpg'
    filename_result = filename + '_result.png'
    filename_work = filename + '_work.png'

    base64_img = request.form['image']
    if not base64_img.startswith('data:image/jpeg;base64,'):
        print("Invalid base64 image format")
        return  render_template('error.html', message="エラーが発生しました。")
    print("type & size of base64_img:"+str(type(base64_img))+", "+str(sys.getsizeof(base64_img)))
    code = base64.b64decode(base64_img.split(',')[1])  # remove header 
    nparray = np.frombuffer(code, np.uint8)
    image_decoded = cv2.imdecode(nparray, cv2.IMREAD_COLOR)
    cv2.imwrite(filename_input, image_decoded)

    start_time = time.perf_counter()
    outTable, inTable = subOCR.find_square(filename_input, filename_result, filename_work)
    current_time = time.perf_counter()
    print("processing time = {:.3f}sec".format(current_time - start_time))

    if 0 in outTable:
        print("Processing failed. Result contains zero.")
        return render_template('error.html', message="解けませんでした。", work_file=filename_work)
    
    print("Processing completed successfully.")
    os.remove(filename_input)
    print(f"{filename_input} を削除しました。")
    os.remove(filename_result)
    print(f"{filename_result} を削除しました。")
    os.remove(filename_work)
    print(f"{filename_work} を削除しました。")
    
    return render_template('solution.html', PlaceName = PlaceName, IN_Table = inTable, NP_Table = outTable)

if __name__ == '__main__':
    for p in glob.glob(app.config['UPLOADED_PATH']+'/**', recursive=True):
        if os.path.isfile(p):
            #os.remove(p)
            #print('not removed : '+p)
            pass
    app.run(debug=True)    