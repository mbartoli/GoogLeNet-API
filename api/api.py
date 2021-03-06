from flask import Flask, request
from flask_restful import Resource, Api

import shutil
import requests
import tempfile
import os
caffe_root = '/opt/caffe/'
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

pd.set_option('display.mpl_style', 'default')

import sys
sys.path.insert(0, caffe_root + 'python')

import caffe
plt.rcParams['figure.figsize'] = (4, 4)
plt.rcParams['image.interpolation'] = 'nearest'
plt.rcParams['image.cmap'] = 'gray'

app = Flask(__name__)
api = Api(app)

todos = {}

imagenet_labels_filename = caffe_root + '/data/ilsvrc12/synset_words.txt'
try:
    labels = np.loadtxt(imagenet_labels_filename, str, delimiter='\t')
except:
    labels = np.loadtxt(imagenet_labels_filename, str, delimiter='\t')
    
caffe.set_mode_cpu()

BATCH_SIZE = 1
net = caffe.Net('/opt/caffe/models/bvlc_googlenet/deploy.prototxt',
                '/models/bvlc_googlenet.caffemodel',
                caffe.TEST)

shape = list(net.blobs['data'].data.shape)
shape[0] = BATCH_SIZE
net.blobs['data'].reshape(*shape)
net.blobs['prob'].reshape(BATCH_SIZE, )
net.reshape() 

transformer = caffe.io.Transformer({'data': net.blobs['data'].data.shape})
transformer.set_transpose('data', (2,0,1))
transformer.set_raw_scale('data', 255)
transformer.set_channel_swap('data', (2,1,0)) 

def get_png_image(url):
    fd, path = tempfile.mkstemp()
    tmpfile = os.fdopen(fd, "wb")
    response = requests.get(url, stream=True)
    shutil.copyfileobj(response.raw, tmpfile)
    if 'png' in url:
        os.system("mv "+path+" "+path+".png")
    else:
        os.system("convert "+path+" "+path+".png")
    path = path + ".png"
    return transformer.preprocess('data', caffe.io.load_image(path))
    
def display(data):
    plt.imshow(transformer.deprocess('data', data))

def get_label_name(num):
    options = labels[num].split(',')
    options[0] = ' '.join(options[0].split(' ')[1:])
    return ','.join(options[:2])
    
def predict(data, n_preds=6, display_output=True):
    net.blobs['data'].data[...] = data
    if display_output:
        display(data)
    prob = net.forward()['prob']
    probs = prob[0]
    prediction = probs.argmax()
    top_k = probs.argsort()[::-1]
    for pred in top_k[:n_preds]:
        percent = round(probs[pred] * 100, 2)
        pred_formatted = "%03d" % pred
        if n_preds == 1:
            format_string = "label: {cls} ({label})\ncertainty: {certainty}%"
        else:
            format_string = "label: {cls} ({label}), certainty: {certainty}%"
        if display_output:
            print format_string.format(
                cls=pred_formatted, label=get_label_name(pred), certainty=percent)
    return [percent, get_label_name(pred), prediction]
    

class detection(Resource):
    def get(self, todo_id):
        return {todo_id: todos[todo_id]}

    def put(self, todo_id):
        url = request.form['data']
        image_data = get_png_image(url)
        probs = predict(image_data, n_preds=1, display_output=False)
        return probs 

api.add_resource(detection, '/<string:todo_id>')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=3001)
