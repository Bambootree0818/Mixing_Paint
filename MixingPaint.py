import os
import numpy as np
from scipy.interpolate import interp1d
from datetime import datetime

def read_sample(file_path):
    with open(file_path, 'r') as file:
        data = file.readlines()
    data_list = [line.strip().split(',') for line in data[14:] if line.strip()]
    return data_list

paint_name = input("paint name : ")

sample_data = {}
directory = "measured_BRDF/"

for file_name in os.listdir(directory):
    if file_name.split("_")[0] == paint_name:
        file_path = directory + file_name 
        file_name = file_name.replace(".astm", "")
        print(file_name)
        sample_data[file_name] = read_sample(file_path)

#raito = input("raito : ")

#print(sample_data[paint_name + "_" + raito][0])

wi_theta = {}
wi_phi = {}
wo_theta = {}
wo_phi = {}
ref_b ={}
ref_g = {}
ref_r = {}

#パラメータをセット
def set_parameter(sample_data):
    for raito in sample_data:
        print(raito)
        for row in sample_data[raito]:
            
            if raito not in wi_theta:
                wi_theta[raito] = []
            wi_theta[raito].append(float(row[0]))

            if raito not in wi_phi:
                wi_phi[raito] = []
            wi_phi[raito].append(float(row[1]))

            if raito not in wo_theta:
                wo_theta[raito] = []
            wo_theta[raito].append(float(row[2]))

            if raito not in wo_phi:
                wo_phi[raito] = []
            wo_phi[raito].append(float(row[3]))

            if raito not in ref_b:
                ref_b[raito] = []
            ref_b[raito].append(float(row[4]))

            if raito not in ref_g:
                ref_g[raito] = []
            ref_g[raito].append(float(row[5]))

            if raito not in ref_r:
                ref_r[raito] = []
            ref_r[raito].append(float(row[6]))

set_parameter(sample_data)

#print(ref_b["B&R_1&9"])

def linear_interpolation(sample_data, target_raito):
    #使用する比率
    ratios = [1, 3, 5, 7, 9]
    ratios.sort() 
    target_ratio = float(target_raito)

    interpolated_data = []

    #データポイントの数を取得
    num_data_points = len(sample_data[next(iter(sample_data))])
    print(num_data_points)

    #各データポイントに対する補完
    for i in range(num_data_points):
        print(i)
        #各比率に対するBRDFの値をリストに格納
        brdf_b = [float(sample_data[f'{paint_name}_{r}&{10-r}'][i][4]) for r in ratios]
        brdf_g = [float(sample_data[f'{paint_name}_{r}&{10-r}'][i][5]) for r in ratios]
        brdf_r = [float(sample_data[f'{paint_name}_{r}&{10-r}'][i][6]) for r in ratios]

        #線形補完を実行
        interp_b = interp1d(ratios, brdf_b, kind='linear')
        interp_g = interp1d(ratios, brdf_g, kind='linear')
        interp_r = interp1d(ratios, brdf_r, kind='linear')

        interpolated_b = interp_b(target_ratio)
        interpolated_g = interp_g(target_ratio)
        interpolated_r = interp_r(target_ratio)

        # 補完されたデータを格納
        interpolated_data.append([
            wi_theta[next(iter(sample_data))][i],
            wi_phi[next(iter(sample_data))][i],
            wo_theta[next(iter(sample_data))][i],
            wo_phi[next(iter(sample_data))][i],
            interpolated_b,
            interpolated_g,
            interpolated_r
        ])

    return interpolated_data
    

# 補完する比率をユーザーから入力
target_ratio = input("Enter the target ratio (e.g., 4 for 4:6): ")
interpolated_results = linear_interpolation(sample_data, target_ratio)

# 補完された結果をCSVファイルに保存
result_directory = "Result"
output_file_name = f'{paint_name}_{target_ratio}&{10 - int(target_ratio)}'
output_file = os.path.join(result_directory, f'{output_file_name}.astm')

current_date = datetime.now().strftime("%Y/%m/%d")
current_time = datetime.now().strftime("%H:%M:%S")

# ヘッダー情報を設定
header = f"""LAB_NAME MIYATA_LAB SASAKI

SYSTEM_NAME MixingPaint.py
APERTURE Circular

SAMPLE_NAME "{output_file_name}"

MEAS_NAME BRDF
FILE_NAME "{output_file_name}.astm"
MEAS_DATE {current_date}
MEAS_TIME {current_time}
NUM_POINTS 12964
VARS theta_i,phi_i,theta_s,465nm,525nm,630nm
"""

with open(output_file, 'w') as f:
    f.write(header + '\n')  # ヘッダー情報を追加
    for row in interpolated_results:
        f.write(','.join(map(str, row)) + '\n')

print(f"Interpolated data has been saved to {output_file}")