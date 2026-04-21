import os
import cv2
import numpy as np

import subImageProcessClass as subIP
import subNumberPlace as subNP
import subONNX as subOnnx

def find_square(s_file, r_file, w_file):
    number_table = np.zeros((9, 9), dtype=np.int32)
    value_table = np.zeros((9, 9), dtype=np.float32)
    number_table2 = np.zeros((9, 9), dtype=np.int32)
    value_table2 = np.zeros((9, 9), dtype=np.float32)

    IPClass = subIP.ImageProcess(s_file)

    # 輪郭の抽出
    contours = IPClass.getContours()

    # 輪郭をなめらかな多角形に変換
    polies = IPClass.getSmoothContours(contours)

    # 多角形から矩形の抽出
    square = IPClass.getRectangle(polies)

    # 各グリッドの頂点を元画像にフィットさせる
    rect = square.astype(np.float32)
    imgTrandformed, grayTransformed = IPClass.transformedImage(rect)
    cross_points, grays, results, candidates_img, templates = IPClass.fitGrid(grayTransformed)

    # 十字の中心点を元の画像に変換
    gridImages = IPClass.getGridImages(cross_points, rect)

    # ONNXモデルを読み込む
    ONNXClass = subOnnx.Onnx('./net/model.onnx')
    # 画像から数字を推論し、タイル状画像を作成 (9行9列)
    tile_image = np.full((9*70, 9*70, 3), 100, dtype=np.uint8)
    NPClass = subNP.NumberPlace()
    for j in range(9):
        for i in range(9):
            # 画像を推論
            im = gridImages[i,j]
            im = np.clip(im, 0, 255).astype(np.uint8)
            im = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
            im = cv2.bitwise_not(im)
            # ONNXモデルで推論
            max_idx, max_value, second_idx, second_value = ONNXClass.predict(im)
            number_table[j][i] = max_idx
            value_table[j][i] = max_value
            number_table2[j][i] = second_idx
            value_table2[j][i] = second_value
            # タイル状画像に配置
            tile_image[j*70+3:(j+1)*70-3, i*70+3:(i+1)*70-3] = gridImages[i,j]

    result_table, input_table = NPClass.set(number_table)

    if np.any(result_table == 0):
        print("ゼロサプレスを実行")
        # 30未満の値を0に置き換える
        indices = np.where(value_table < 30)        
        number_table[indices] = 0
        result_table, input_table = NPClass.set(number_table)

    if np.any(result_table == 0):
        # 第一候補と第二候補の評価値の比が1.5未満の値を第二候補のインデックスに置き換える
        ratio_table = value_table / (value_table2 + 1e-6)  # ゼロ割り防止のために小さな値を加算
        threshold = 1.5
        mask = ratio_table <= threshold
        # マスクされた値を1次元化し、argsort
        flat_idx = np.argsort(ratio_table[mask])

        # マスクされた部分の元の2次元インデックス
        rows, cols = np.where(mask)

        # 小さい順に並べ替えた2次元インデックス
        sorted_rows = rows[flat_idx]
        sorted_cols = cols[flat_idx]
        target_rows = []
        target_cols = []
        for i in range(len(sorted_rows)):
            r = sorted_rows[i]
            c = sorted_cols[i]
            if number_table[r][c] == 0:
                continue  # すでにゼロになっている場合はスキップ
            target_rows.append(r)
            target_cols.append(c)
        n = len(target_rows)
        if n > 0:
            print("第二候補との入れ替えを実行")
            for mask in range(1, 2**n):
                B = number_table.copy()
                for bit in range(n):
                    if (mask >> bit) & 1:
                        r, c = target_rows[bit], target_cols[bit]
                        B[r, c] = number_table2[r, c]
                result_table, input_table = NPClass.set(B)
                if not np.any(result_table == 0):
                    break            

    # タイル状画像を描画
    for j in range(9):
        for i in range(9):
            if input_table[j][i] == 0:
                cv2.putText(tile_image, str(result_table[j][i]), tuple([i*70+17, j*70+55]), cv2.FONT_HERSHEY_SIMPLEX, 1.8, (0, 64, 0), 5)
            else:
                cv2.putText(tile_image, str(result_table[j][i]), tuple([i*70+50, j*70+65]), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (128, 0, 0), 3)
    cv2.imwrite(r_file, tile_image)    

    for j in range(10):
        for i in range(10):
            blended = cv2.addWeighted(imgTrandformed[j*64+15:j*64+49, i*64+15:i*64+49], 0.7, candidates_img[i,j], 0.3, 0)
            imgTrandformed[j*64+15:j*64+49, i*64+15:i*64+49] =blended
    color = (0, 255, 0)
    for j in range(10):
        for i in range(10):
            if j < 9:
                cv2.line(imgTrandformed, cross_points[j][i], cross_points[j+1][i], color, thickness=1, lineType=cv2.LINE_AA, shift=0)
            if i < 9:
                cv2.line(imgTrandformed, cross_points[j][i], cross_points[j][i+1], color, thickness=1, lineType=cv2.LINE_AA, shift=0)
    for j in range(9):
        for i in range(9):
            if input_table[j][i] != 0:
                cv2.putText(imgTrandformed, str(input_table[j][i]), tuple([i*64+64, j*64+48]), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (128, 0, 0), 2) 
                cv2.putText(imgTrandformed, format(value_table[j][i], ".3f"), tuple([i*64+64, j*64+64]), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 128), 1) 
                cv2.putText(imgTrandformed, str(number_table2[j][i]), tuple([i*64+64, j*64+80]), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (128, 0, 0), 2) 
                cv2.putText(imgTrandformed, format(value_table2[j][i], ".3f"), tuple([i*64+64, j*64+96]), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 128), 1) 

    cv2.imwrite(w_file, imgTrandformed)

    print("Processing completed. Result saved to:", r_file)
    return result_table, input_table
