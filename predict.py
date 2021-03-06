# REF: This was adapted from https://github.com/experiencor/keras-yolo2

# intialization
from keras.models import Sequential, Model
from keras.layers import Reshape, Activation, Conv2D, Input, MaxPooling2D, BatchNormalization, Flatten, Dense, Lambda
from keras.layers.advanced_activations import LeakyReLU
from keras.callbacks import EarlyStopping, ModelCheckpoint, TensorBoard
from keras.optimizers import SGD, Adam, RMSprop
from keras.layers.merge import concatenate
from keras import initializers
import matplotlib.pyplot as plt
import keras.backend as K
import tensorflow as tf
import imgaug as ia
from tqdm import tqdm
from imgaug import augmenters as iaa
import numpy as np
import pickle
import os, cv2
from utils import WeightReader, decode_netout, draw_boxes
from keras.models import load_model
from custom_loss import custom_loss
from config import my_parameters

# define parameters from config.py
LABELS = my_parameters.LABELS
IMG_H, IMG_W = my_parameters.IMG_H, my_parameters.IMG_W
GRID_H, GRID_W = my_parameters.GRID_H, my_parameters.GRID_W
BOX = my_parameters.BOX
CLASS = my_parameters.CLASS
CLASS_WEIGHTS = my_parameters.CLASS_WEIGHTS
OBJ_THRESHOLD    = my_parameters.OBJ_THRESHOLD
NMS_THRESHOLD    = my_parameters.NMS_THRESHOLD
ANCHORS          = my_parameters.ANCHORS

NO_OBJECT_SCALE  = my_parameters.NO_OBJECT_SCALE
OBJECT_SCALE     = my_parameters.OBJECT_SCALE
COORD_SCALE      = my_parameters.COORD_SCALE
CLASS_SCALE      = my_parameters.CLASS_SCALE

BATCH_SIZE       = my_parameters.BATCH_SIZE
WARM_UP_BATCHES  = my_parameters.WARM_UP_BATCHES
TRUE_BOX_BUFFER  = my_parameters.TRUE_BOX_BUFFER

input_image = my_parameters.input_image
true_boxes  = my_parameters.true_boxes

# load new model from training
model = load_model('new_model_6.h5', custom_objects={
    	'tf':tf,
    	'custom_loss':custom_loss
})

# load image
folder_path = "data/test_img/"
save_path = "data/test_predicted_img/" 
for fn in os.listdir(folder_path):
    full_folder_path = folder_path + fn
    image = cv2.imread(full_folder_path)
    dummy_array = np.zeros((1,1,1,1,TRUE_BOX_BUFFER,4))
    input_image = cv2.resize(image, (416, 416))
    input_image = input_image / 255.
    input_image = input_image[:,:,::-1]
    input_image = np.expand_dims(input_image, 0)

    netout = model.predict([input_image, dummy_array])

    boxes = decode_netout(netout[0], 
	                      obj_threshold=OBJ_THRESHOLD,
	                      nms_threshold=NMS_THRESHOLD,
	                      anchors=ANCHORS, 
	                      nb_class=CLASS)

    image = draw_boxes(image, boxes, labels=LABELS)
    full_save_path = save_path + fn
    cv2.imwrite(full_save_path,image)

# load video
video_inp = 'data/videos/Street - 5025.mp4'
video_out = 'data/videos/Street - 5025_bbox.mp4'

dummy_array = np.zeros((1,1,1,1,TRUE_BOX_BUFFER,4))

video_reader = cv2.VideoCapture(video_inp)

nb_frames = int(video_reader.get(cv2.CAP_PROP_FRAME_COUNT))
frame_h = int(video_reader.get(cv2.CAP_PROP_FRAME_HEIGHT))
frame_w = int(video_reader.get(cv2.CAP_PROP_FRAME_WIDTH))

video_writer = cv2.VideoWriter(video_out,
                               cv2.VideoWriter_fourcc(*'XVID'), 
                               50.0, 
                               (frame_w, frame_h))

for i in tqdm(range(nb_frames)):
    ret, image = video_reader.read()
    
    input_image = cv2.resize(image, (416, 416))
    input_image = input_image / 255.
    input_image = input_image[:,:,::-1]
    input_image = np.expand_dims(input_image, 0)

    netout = model.predict([input_image, dummy_array])

    boxes = decode_netout(netout[0], 
                          obj_threshold=0.3,
                          nms_threshold=NMS_THRESHOLD,
                          anchors=ANCHORS, 
                          nb_class=CLASS)
    image = draw_boxes(image, boxes, labels=LABELS)

    video_writer.write(np.uint8(image))
    
video_reader.release()
video_writer.release()
