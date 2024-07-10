# BRDF マテリアル推定　1月10日　

import mitsuba as mi
import drjit as dr
import numpy as np
import matplotlib.pyplot as plt
import colour as colour
from colour.models import RGB_COLOURSPACE_BT2020
import json

#利用可能なバリアントを表示
variants = mi.variants()
print(variants)

#cudaバリアントをセット
mi.set_variant('cuda_ad_rgb')
print(mi.variant())

# ファイルからデータを読み込み
def read_sample(file_path):
    with open(file_path, 'r') as file:
        data = file.readlines()
    data_list = [line.strip().split(',') for line in data[14:] if line.strip()]
    return data_list

file_name = input('file name : ')
file_path = 'Results/' + file_name + '.astm'  #データパスの指定
sample_data = read_sample(file_path)
#print(data[0][4])

measure_rgb = [0.12314769063117968, 0.0090968396951767, 0.007679417458095666]

# 最適化対象のBSDFを定義（Principled BRDF）
bsdf = mi.load_dict({
    'type': 'principled',
    'base_color': {
            'type': 'rgb',
            'value': [0.0,0.0,0.0]
    },
    'metallic': 0.5,
    'specular': 0.5,
    'roughness': 0.5,
    'spec_tint': 0.0,
    'anisotropic': 0.0,
    'sheen': 0.0,
    'sheen_tint': 0.0,
    'clearcoat': 1.0,
    'clearcoat_gloss': 1.0,
    'spec_trans': 0.0
})

keys = [
    'base_color.value',
    'metallic.value',
    'roughness.value',
    'specular',
    #'spec_tint.value',
    #'anisotropic.value',
    #'sheen.value',
    'clearcoat.value',
    'clearcoat_gloss.value',  
    #'spec_trans.value'  
]
    
class Samples:

    def __init__(self,samples_data):
        self.samples = samples_data #サンプルの所持
        self.wi_theta = [] #入射光の極角(θ)
        self.wi_phi = [] #入射光の方位角(φ)
        self.wo_theta = [] #反射光の極角
        self.wo_phi = [] #反射光の方位角
        self.rgb_ref_soa= [] #青緑赤の反射
        self.set_parameter() #パラメータをセット
        self.wi_xyz = self.sph_to_dir(self.wi_theta,self.wi_phi) #入射光を球面座標から三次元ベクトルに変換
        self.wo_xyz = self.sph_to_dir(self.wo_theta,self.wo_phi) #反射光を球面座標から三次元ベクトルに変換
        self.specular_xyz = self.calculate_specular_vec(self.wi_xyz)
        #print(self.wi_xyz)

    #パラメータをセット
    def set_parameter(self):
        for row in self.samples:
            self.wi_theta.append(float(row[0]))
            self.wi_phi.append(float(row[1]))
            self.wo_theta.append(float(row[2]))
            self.wo_phi.append(float(row[3]))
            self.rgb_ref_soa.append(float(row[6]))
            self.rgb_ref_soa.append(float(row[5]))
            self.rgb_ref_soa.append(float(row[4]))
        
        self.rgb_ref_soa = dr.unravel(dr.cuda.ad.Array3f, dr.cuda.ad.Float(self.rgb_ref_soa))
        #self.bgr_ref_soa = np.array(self.bgr_ref_soa)

    #球面座標から三次元ベクトルに変換
    def sph_to_dir(self,theta_list,phi_list):
        t = dr.cuda.ad.Float(theta_list)
        p = dr.cuda.ad.Float(phi_list)
        st, ct = dr.sincos(t)
        sp, cp = dr.sincos(p)
            #print(mi.Vector3f(cp * st, sp * st, ct))
            #w.append(mi.Vector3f(cp * st, sp * st, ct))
            #print(w[0][0])
        return mi.Vector3f(cp * st, sp * st, ct)
    
    #正反射のベクトルを計算
    def calculate_specular_vec(self,wi_xyz, n = np.array([0,0,1])):
        dir = []
        d = dr.dot(n, wi_xyz) 
        for i in range(len(d)):
            h = 2 * n * d[i]
            h_list = h.tolist()
            for j in range(len(h_list)):
                dir.append(h_list[j])
        xyz = dr.unravel(dr.cuda.ad.Array3f, dr.cuda.ad.Float(dir))
        specular_vec = xyz - wi_xyz; 
        return specular_vec
    
    #loss関数
    def loss(self, bsdf, all_lossFlag):
        if all_lossFlag == True:
            #print("all")
            return self.all_loss(bsdf)
        else:
            #print("light")
            return self.lightLoss(bsdf)
    
    #rgbloss関数
    def all_loss(self,bsdf):
        values = createBRDFSample(bsdf, self.wi_xyz, self.wo_xyz)
        #print(self.rgb_ref_soa)
        #print(values)
        er = dr.sqr(self.rgb_ref_soa[0] - values[0])
        eg = dr.sqr(self.rgb_ref_soa[1] - values[1])
        eb = dr.sqr(self.rgb_ref_soa[2] - values[2])
        cosWoSpecular = dr.dot(self.wo_xyz, self.specular_xyz)
        loss = dr.sqrt(er + eg + eb) * cosWoSpecular
        return dr.mean(dr.mean(loss))
    
    #loss関数（輝度のみ）
    def lightLoss(self, bsdf):
        values = createBRDFSample(bsdf,self.wi_xyz, self.wo_xyz)
        illuminant_XYZ = np.array([0.31270, 0.32900])
        xyz = colour.RGB_to_XYZ(values,RGB_COLOURSPACE_BT2020,illuminant_XYZ)
        xyz_soa = colour.RGB_to_XYZ(self.rgb_ref_soa,RGB_COLOURSPACE_BT2020,illuminant_XYZ)
        loss = dr.mean(dr.sqr(xyz_soa[1] - xyz[1]))
        return loss
    
#BRDFのサンプルを作成
def createBRDFSample(brdf,wi,wo):
    si = mi.SurfaceInteraction3f()
    si.wi = wi
    values = brdf.eval(mi.BSDFContext(),si,wo)
    return values

#マテリアルプレビュー
def material_preview(opt_bsdf, scene_params):
    for key in keys:
        if 'metallic' in key:
            scene_params["bsdf-matpreview.metallic.value"] = opt_bsdf[key]
        elif 'roughness' in key:
            scene_params["bsdf-matpreview.roughness.value"] = opt_bsdf[key]
        elif 'clearcoat.value' in key:
            scene_params["bsdf-matpreview.clearcoat.value"] = opt_bsdf[key]
        elif 'clearcoat_gloss.value' in key:
            scene_params["bsdf-matpreview.clearcoat_gloss.value"] = opt_bsdf[key]
        elif 'specular' in key:
            scene_params["bsdf-matpreview.specular"] = opt_bsdf[key]
        elif 'base_color' in key:
            scene_params["bsdf-matpreview.base_color.value"] = measure_rgb
        #else:
            #mtParams["bsdf-matpreview." + key] = opt_bsdf[key]
        
    scene_params.update()
    material_image = mi.render(scene,scene_params,spp = 516)
    #print(scene_params)
    mi.util.convert_to_bitmap(material_image)
    mi.util.write_bitmap("Fitting_Results_linear/" + file_name + ".png", material_image)
    
    # matplotlibの設定と画像表示
    plt.axis("off")  # 軸を非表示
    plt.imshow(material_image ** (1.0 / 2.2))  # 画像を表示（sRGBトーンマッピングを近似）
    plt.show()  # 画像を表示

def optimize(targetBRDF, measures, scene_params, steps, keys, lr = 0.001):
    base_color_flag = True
    
    #オプティマイザーを定義
    opt = mi.ad.Adam(lr = lr)
    #errf_prev = 0.
    
    param_clamp = True
    
    #シーンをトラバースし、最適化パラメータをリストアップ
    params = mi.traverse(targetBRDF)
    #params_init = dict(params)
    print(params)
    for key in keys:
        opt[key] = params[key]
    
    #初期値のセット
    params.update(opt)
    
    #最適化スタート
    for step in range(steps):
        
        #loss関数を計算
        loss= 0.
        #print(base_color_flag)
        loss = measures.loss(targetBRDF,base_color_flag)

        
        penalty = 0
        for key in keys:
            penalty += dr.sqr(opt[key] - 0.3824)
        loss = loss + penalty
        #print(loss)
        #lossf = dr.sum(loss)[0] / len(loss)
        
        dr.backward(loss)
        
        opt.step()
        if param_clamp:
            for key in keys:
                if 'metallic' in key:
                    #opt[key] = dr.clamp(opt[key],0.0,1.0)
                    pass
                elif 'roughness' in key:
                    #opt[key] = dr.clamp(opt[key],0.0,1.0)
                    pass
                elif 'clearcoat' in key:
                    #opt[key] = dr.clamp(opt[key],0.0,1.0)
                    pass
                elif 'specular' in key:
                    opt[key] = dr.clamp(opt[key],0.0,1.0)
                    #pass
                elif 'base_color' in key:
                    opt[key] = dr.clamp(opt[key],0.0,1.0)
                    #pass
                else:
                    opt[key] = dr.clamp(opt[key],0.0,1.0)

        #errf_prev = lossf
        params.update(opt)
        
        print('Iteration:', step)
        for key in keys:
            print(key,  opt[key])
        print("loss:", loss)
        print()
        
    
        
    material_preview(params, scene_params)

    
    #セーブするデータを登録
    data_to_save = {'name': file_name}
    for key in keys:
        data_to_save[key] = params[key]
        if type(data_to_save[key]) == mi.cuda_ad_rgb.Color3f:
            data_to_save[key] = measure_rgb
        if type(data_to_save[key]) == mi.cuda_ad_rgb.Float:
            data_to_save[key] = float(data_to_save[key][0])
    
    #jsonfileに書き込み
    with open('Results_json_linear/' + file_name + ".json", 'w') as json_file:
        json.dump(data_to_save, json_file, indent=4)
    
    #b = []
    #for i in range(4):
    #    b.append(params['base_color.value'][i]) 
    #b= dr.unravel(mi.cuda_ad_spectral.Spectrum, dr.cuda.ad.Float(b))
    #w = mi.cuda_ad_spectral.Spectrum(465.0, 525.0, 630.0, 700.0)
    #srgb = mi.cuda_ad_spectral.spectrum_to_xyz(values=b,wavelengths=w)
    #print(b)
    

scene = mi.load_file("Scene/Material-Ball.xml")
#シーンをトラバースし、最適化パラメータをリストアップ
scene_params = mi.traverse(scene)

#測定データクラスのインスタンスを作成
s = Samples(sample_data)


optimize(bsdf, s, scene_params,3000,keys)

'''

#画像と参照画像との間の平均二乗誤差を計算する関数
def mse_image(image, image_ref):
    #print(dr.mean(dr.sqr(image - image_ref)))
    return dr.mean(dr.sqr(image - image_ref))

#base_colorの最適化
def optimize_bc(scene_params, steps, lr = 0.01):
    
    bitmap_ref = mi.Bitmap('basecolor_ref_another/'+ file_name + '_ref.png').convert(mi.Bitmap.PixelFormat.RGB, mi.Struct.Type.Float32, srgb_gamma=False)
    image_ref = dr.cuda.ad.TensorXf(bitmap_ref)
    
    opt = mi.ad.Adam(lr = lr)
    
    #初期値のセット
    opt['bsdf-matpreview.base_color.value'] = scene_params['bsdf-matpreview.base_color.value']
    #scene_params.keep(["bsdf-matpreview.base_color.value"])
    scene_params.update(opt)
    
    for step in range(steps):
        
        image = mi.render(scene, scene_params, spp=4)
        
        loss = mse_image(image, image_ref)
        
        dr.backward(loss)
        
        opt.step()
        
        opt['bsdf-matpreview.base_color.value'] = dr.clamp(opt['bsdf-matpreview.base_color.value'], 0.0, 1.0)
        
        scene_params.update(opt)
        
        print('Iteration:', step)
        print('bsdf-matpreview.base_color.value',  opt['bsdf-matpreview.base_color.value'])
        print("loss:", loss)
        print()
        
    #scene_params.update(opt)
    
    image_final = mi.render(scene, spp=512)
    mi.util.convert_to_bitmap(image_final)

    # matplotlibの設定と画像表示
    plt.axis("off")  # 軸を非表示
    plt.imshow(image_final ** (1.0 / 2.2))  # 画像を表示（sRGBトーンマッピングを近似）
    plt.show()  # 画像を表示
    
    mi.util.write_bitmap("Fitting_Results_another/" + file_name + ".png", image_final)
    
#optimize_bc(scene_params, 120)

'''