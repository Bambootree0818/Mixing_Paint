import os

def read_sample(file_path):
    with open(file_path, 'r') as file:
        data = file.readlines()
    data_list = [line.strip().split(',') for line in data[14:] if line.strip()]
    return data_list

paint_name = input("paint name : ")

sample_data = {}
directory = "measured_BRDF/"

for file_name in os.listdir(directory):
    if paint_name in file_name:
        file_path = directory + file_name 
        file_name = file_name.replace(".astm", "")
        print(file_name)
        sample_data[file_name] = read_sample(file_path)

raito = input("raito : ")

print(sample_data[paint_name + "_" + raito])