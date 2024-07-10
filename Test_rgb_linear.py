import json
import numpy as np
from scipy.interpolate import interp1d

# ファイル名とファイルパスのリストを作成します
file_names = ["R&Blue_1&9", "R&Blue_3&7", "R&Blue_5&5", "R&Blue_7&3", "R&Blue_9&1"]
file_path = "Results_json/"

# ファイルからRGB値を読み込みます
rgb_values = {}
for file_name in file_names:
    with open(f"{file_path}{file_name}.json", "r") as f:
        data = json.load(f)
        rgb_values[file_name] = data["base_color.value"]

# 比率とその位置の対応を定義します
ratios = {
    "2&8": 2,
    "4&6": 4,
    "6&4": 6,
    "8&2": 8
}

# x軸の値を定義します
x = np.array([1, 3, 5, 7, 9])

# RGBの線形補完関数を作成します
def interpolate_rgb_values(ratio, rgb_values):
    interpolated_values = []
    for i in range(3):  # RGBの各成分について
        y = np.array([rgb_values[f"R&Blue_{x_pos}&{10-x_pos}"][i] for x_pos in x])
        f = interp1d(x, y, kind='linear')
        interpolated_values.append(f(ratio).item())  # array() を外すために item() を使う
    return interpolated_values

# 結果をテキストファイルに書き込みます
output_file = "interpolated_rgb_values.txt"
with open(output_file, "w") as f:
    # 既存の比率のRGB値をまず記述します
    for file_name in file_names:
        f.write(f"{file_name}: {rgb_values[file_name]}\n")
    
    # 補間された値を書き込みます
    for ratio_name, ratio in ratios.items():
        interpolated_value = interpolate_rgb_values(ratio, rgb_values)
        f.write(f"Ratio {ratio_name}: {interpolated_value}\n")

print(f"Interpolated RGB values have been written to {output_file}.")
