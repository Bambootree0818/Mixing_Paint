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