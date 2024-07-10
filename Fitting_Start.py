import subprocess
import colour as colour
from colour.models import RGB_COLOURSPACE_BT2020
from colour.models import RGB_COLOURSPACE_sRGB
from colour.models import RGB_COLOURSPACE_ADOBE_RGB1998
import numpy as np

fitting_script = 'All_BRDF_Fitting_OptColor.py'

# Lab値を取得
def load_data(file_path):
    keys = []  # キーを格納するリスト
    data = {}  # キーとRGB値のマッピングを格納する辞書

    # テキストファイルを開いて読み込む
    with open(file_path, 'r') as file:
        for line in file:
            # 各行を":"で分割してキーとXYZ値を取得
            key, value = line.strip().split(':')
            # キーをリストに追加
            keys.append(key)
            # Lab値をカンマで分割してリストとして辞書に格納
            data[key] = list(map(float, value.split(',')))

    return keys, data

def get_Lab_value(data, name):
    # 指定された名前に対応するXYZ値を辞書から取得
    return data.get(name)

def get_XYZ_value(Lab_value):
    XYZ_value = colour.Lab_to_XYZ(Lab_value)
    XYZ_value_list = XYZ_value.tolist()
    return XYZ_value_list

def get_rgb_value(xyz_value):
    illuminant_XYZ = np.array([0.31270, 0.32900])
    rgb_value = colour.XYZ_to_RGB(xyz_value,RGB_COLOURSPACE_sRGB,illuminant_XYZ)
    rgb_value_list = rgb_value.tolist()
    return rgb_value_list

# ファイルパスと名前を指定
file_path = 'measures_Color/sample_Lab_data.txt'  # テキストファイルのパスを指定

# データを読み込み、キーとRGB値のマッピングを取得
keys, data = load_data(file_path)

# キーを表示
print("利用可能なキー:", keys)

#name = input("名前を入力してください (例: C1_White): ")

# rgb 0~255 -> 0~1 
def inverse_gamma_correction(value):
    """Apply inverse gamma correction to a normalized value (0-1 range)."""
    if value <= 0.04045:
        return value / 12.92
    else:
        return ((value + 0.055) / 1.055) ** 2.4

# Normalize and apply inverse gamma correction


# 各ファイル名についてスクリプト2を実行
for file_name in keys:

    # Lab値を取得
    Lab_value = get_Lab_value(data, file_name)

    # XYZ値を取得
    XYZ_value = get_XYZ_value(Lab_value)

    # RGB値を取得
    rgb_value = get_rgb_value(XYZ_value)

    if rgb_value:   
        print(f"{file_name} のLav値: {Lab_value}")
        print(f"{file_name} のXYZ値: {XYZ_value}")
        print(f"{file_name} のRGB値: {rgb_value}")
    else:
        print(f"{file_name} に対応するRGB値が見つかりませんでした。")
    
    # Normalize and apply inverse gamma correction
    #linear_rgb = [inverse_gamma_correction(c / 255.0) for c in rgb_value]
    #print(linear_rgb)

    # 文字列に変換
    linear_rgb_str = ' '.join(map(str, rgb_value))

    # subprocess.runを使用してscript2を実行
    # スクリプト2への入力としてファイル名と追加の引数をコマンドライン引数として渡す
    subprocess.run(['python', fitting_script, file_name, linear_rgb_str])