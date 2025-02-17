import sys, os
sys.path.append(os.path.realpath(".."))
from sacred.observers import MongoObserver
import pickle as pkl
from addict import Dict
from sklearn.pipeline import Pipeline
import clinical_text_analysis as cta
import pandas as pd
import numpy as np
import numpy.random as random
from os import path
import data_reader as read
from keras import backend as K

# from multiprocessing import Process
import constants
import util_funcs
import functools
from sklearn.model_selection import PredefinedSplit, GridSearchCV
from sklearn.metrics import f1_score, make_scorer, accuracy_score, roc_auc_score, matthews_corrcoef, classification_report, log_loss, confusion_matrix, mean_squared_error
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
import wf_analysis.datasets as wfdata
from keras_models.dataGen import EdfDataGenerator, DataGenMultipleLabels, RULEdfDataGenerator, RULDataGenMultipleLabels
from keras_models.cnn_models import vp_conv2d, conv2d_gridsearch, inception_like_pre_layers, conv2d_gridsearch_pre_layers
from keras import optimizers
from keras.layers import Dense, TimeDistributed, Input, Reshape, Dropout, LSTM, Flatten, Concatenate, CuDNNLSTM, GaussianNoise, BatchNormalization
from keras.layers import Conv2D, MaxPool2D, TimeDistributed, Dense
import keras.layers as layers
from keras.models import Model, load_model
from keras.utils import multi_gpu_model
import pickle as pkl
import sacred
import keras
import ensembleReader as er
from keras.utils import multi_gpu_model
from keras_models import train
import constants
from imblearn.over_sampling import SMOTE
from imblearn.under_sampling import RandomUnderSampler
from keras_models.metrics import f1
import random
import string
from keras.callbacks import ModelCheckpoint, EarlyStopping, LearningRateScheduler
from keras.utils import multi_gpu_model
from time import time
from keras_models.homeoschedastic import HomeoschedasticMultiLossLayer, RelativeHomeoschedasticMultiLossLayer
from keras.losses import categorical_crossentropy, binary_crossentropy

from addict import Dict
ex = sacred.Experiment(name="seizure_conv_exp_domain_adapt_v5")

ex.observers.append(MongoObserver.create(client=util_funcs.get_mongo_client()))

# https://pynative.com/python-generate-random-string/
def randomString(stringLength=16):
    """Generate a random string of fixed length """
    letters = string.ascii_uppercase
    return ''.join(random.choice(letters) for i in range(stringLength))

@ex.named_config
def no_lin_pre_layer():
    num_lin_layer = 0

@ex.named_config
def no_stride_channels():
    '''
    Don't stride on channels
    '''
    max_pool_stride = (1,1)

@ex.named_config
def use_extra_layers():
    num_lin_layer = 2
    pre_layer_h = 22
    linear_dropout = 0.5
    num_post_cnn_layers = 2

@ex.named_config
def MLP():
    num_post_cnn_layers = 2
    linear_dropout=0.5
    num_post_lin_h=200


@ex.named_config
def knn():
    train_pkl = "/home/msaqib/train_multiple_labels_sessions_seizure_data_4.pkl"
    valid_pkl = "/home/msaqib/valid_multiple_labels_sessions_seizure_data_4.pkl"
    test_pkl = "/home/msaqib/test_multiple_labels_sessions_seizure_data_4.pkl"
    include_seizure_type = True
    session_instead_patient = True
    max_bckg_samps_per_file = None
    max_bckg_samps_per_file_test = None

@ex.named_config
def debug():
    train_pkl = "/home/ms994/debug_train_multiple_labels_seizure_data_4.pkl"
    valid_pkl = "/home/ms994/debug_valid_multiple_labels_seizure_data_4.pkl"
    test_pkl = "/home/ms994/debug_test_multiple_labels_seizure_data_4.pkl"
    max_bckg_samps_per_file = 5 #limits number of samples we grab that are bckg to increase speed and reduce data size
    max_bckg_samps_per_file_test = 5
    max_samples=10000
    include_seizure_type=True
    session_instead_patient = True

@ex.named_config
def use_patient_dbmi():
    train_pkl = "/n/scratch2/ms994/train_multiple_labels_seizure_data_4.pkl"
    valid_pkl = "/n/scratch2/ms994/valid_multiple_labels_seizure_data_4.pkl"
    test_pkl = "/n/scratch2/ms994/test_multiple_labels_seizure_data_4.pkl"
    session_instead_patient = False

@ex.named_config
def debug_knn():
    train_pkl = "/home/msaqib/debug_train_multiple_labels_seizure_data_4.pkl"
    valid_pkl = "/home/msaqib/debug_valid_multiple_labels_seizure_data_4.pkl"
    test_pkl = "/home/msaqib/debug_test_multiple_labels_seizure_data_4.pkl"
    max_bckg_samps_per_file = 5 #limits number of samples we grab that are bckg to increase speed and reduce data size
    max_bckg_samps_per_file_test = 5
    max_samples=10000
    include_seizure_type=True
    session_instead_patient = True

@ex.named_config
def full_data():
    max_samples=None
    max_bckg_samps_per_file=None
    max_bckg_samps_per_file_test=None
    train_pkl = "/n/scratch2/ms994/full_train_multiple_labels_sessions_seizure_data_4.pkl"
    valid_pkl = "/n/scratch2/ms994/full_valid_multiple_labels_sessions_seizure_data_4.pkl"
    test_pkl = "/n/scratch2/ms994/test_multiple_labels_sessions_seizure_data_4.pkl"
    session_instead_patient = True
    include_seizure_type = True



@ex.named_config
def use_session_dbmi():
    train_pkl = "/n/scratch2/ms994/train_multiple_labels_sessions_seizure_data_4.pkl"
    valid_pkl = "/n/scratch2/ms994/valid_multiple_labels_sessions_seizure_data_4.pkl"
    test_pkl = "/n/scratch2/ms994/test_multiple_labels_sessions_seizure_data_4.pkl"
    session_instead_patient = True
    max_bckg_samps_per_file_test=None
    include_seizure_type = True
    max_bckg_samps_per_file = 100
    max_bckg_samps_per_file_test = -1


@ex.named_config
def use_session_montage_dbmi():
    train_pkl = "/n/scratch2/ms994/train_multiple_labels_sessions_montage_seizure_data_4.pkl"
    valid_pkl = "/n/scratch2/ms994/valid_multiple_labels_sessions_montage_seizure_data_4.pkl"
    test_pkl = "/n/scratch2/ms994/test_multiple_labels_sessions_montage_seizure_data_4.pkl"
    session_instead_patient = True
    max_bckg_samps_per_file_test=None
    include_montage_channels = True
    include_seizure_type = True
    max_bckg_samps_per_file = 100
    max_bckg_samps_per_file_test = -1

@ex.named_config
def use_session_knn():
    train_pkl = "/home/msaqib/train_multiple_labels_sessions_seizure_data_4.pkl"
    valid_pkl = "/home/msaqib/valid_multiple_labels_sessions_seizure_data_4.pkl"
    test_pkl = "/home/msaqib/test_multiple_labels_sessions_seizure_data_4.pkl"
    session_instead_patient = True
    include_seizure_type = True
    max_bckg_samps_per_file = 100
    max_bckg_samps_per_file_test = -1


@ex.named_config
def most_common_seiz_types():
    seizure_classes_to_use=["bckg", "gnsz", "fnsz", "cpsz"]
    train_pkl = "/n/scratch2/ms994/gnfncp_train_multiple_labels_sessions_seizure_data_4.pkl"
    valid_pkl = "/n/scratch2/ms994/gnfncp_valid_multiple_labels_sessions_seizure_data_4.pkl"
    test_pkl = "/n/scratch2/ms994/gnfncp_test_multiple_labels_sessions_seizure_data_4.pkl"
    session_instead_patient = True
    max_bckg_samps_per_file_test=None
    include_seizure_type = True
    max_bckg_samps_per_file = 100
    max_bckg_samps_per_file_test = -1


@ex.named_config
def gnsz_fnsz():
    seizure_classes_to_use=["bckg", "gnsz", "fnsz"]

@ex.named_config
def gnsz():
    seizure_classes_to_use=["bckg", "gnsz"]

@ex.named_config
def fnsz():
    seizure_classes_to_use=["bckg", "fnsz"]

@ex.named_config
def measure_patient_bias():
    test_patient_model_after_train = True
    train_patient_model_after_train = True
    valid_patient_model_after_train = True

@ex.config
def config():
    model_name = "/n/scratch2/ms994/out/" + randomString() + ".h5" #set to rando string so we don't have to worry about collisions
    mode=er.EdfDatasetSegmentedSampler.DETECT_MODE
    max_samples=None
    max_pool_size = (2,2)
    max_pool_stride = (2,2)
    steps_per_epoch = None
    separate_seizure_classification_weight =None
    session_instead_patient=False

    conv_spatial_filter=(3,3)
    conv_temporal_filter=(1,3)
    num_gpus=1
    num_conv_temporal_layers=1

    imbalanced_resampler = "rul"
    pre_cooldown=4
    use_inception = False
    post_cooldown=None
    sample_time=4
    num_seconds=4
    n_process=20
    mode = er.EdfDatasetSegmentedSampler.DETECT_MODE
    cnn_dropout = 0
    linear_dropout = 0.5
    optimizer_name="adam"
    lstm_h = 128
    lstm_return_sequence = False
    reduce_lr_on_plateau = False
    change_batch_size_over_time = None
    add_gaussian_noise = None
    use_relative = False

    precache = True
    regenerate_data = False
    train_pkl = "/n/scratch2/ms994/train_multiple_labels_seizure_data_4.pkl"
    valid_pkl = "/n/scratch2/ms994/valid_multiple_labels_seizure_data_4.pkl"
    test_pkl = "/n/scratch2/ms994/test_multiple_labels_seizure_data_4.pkl"
    batch_size = 32

    # seizure_type = None

    pre_layer_h = 128
    num_lin_layer = 1

    patience=5
    early_stopping_on="val_loss"
    fit_generator_verbosity = 2
    num_layers = 3
    num_filters = 1
    num_temporal_filter=1
    num_post_cnn_layers = 2
    hyperopt_run = False
    make_model_in_parallel = False
    randomly_reorder_channels = False #use if we want to try to mess around with EEG order
    random_channel_ordering = get_random_channel_ordering()
    include_seizure_type = False
    attach_seizure_type_to_seizure_detect = False
    seizure_classification_only = False
    seizure_classes_to_use = None
    update_seizure_class_weights = False
    min_seizure_weight = 0
    model_type = None

    patient_weight = -1
    seizure_weight = 1

    num_post_lin_h = 5

    use_batch_normalization = True

    max_bckg_samps_per_file = 50 #limits number of samples we grab that are bckg to increase speed and reduce data size
    max_bckg_samps_per_file_test = -1 #reflect the full imbalance in the dataset
    max_samples=None
    use_standard_scaler = False
    use_filtering = True
    ref = "01_tcp_ar"
    combined_split = None
    lr = 0.005
    lr_decay = 0

    use_lstm = False
    use_time_layers_first = False
    max_pool_size_time = None
    validation_f1_score_type = None



    balance_valid_dataset = False

    epochs=100
    seizure_weight_decay = None
    # measure_train_patient_bias = False

    test_patient_model_after_train = False
    train_patient_model_after_train = False
    valid_patient_model_after_train = False
    random_rearrange_each_batch = False
    random_rescale = False
    rescale_factor = 1.3
    include_montage_channels = False
    attach_patient_layer_to_cnn_output = False
    remove_outlier_by_std_thresh = None
    zero_center_over_channel = False #attempts to use the relative mean of each channel over the entire segment and center the record on that
    zero_center_over_time = False #attempts to solve for drift of the entire record

    use_montage_channels_instead_of_montage_num = False # the montage signal aren't per channel, but are from a linear combination of 2 channels.
    separate_out_mlp = False
    use_homeoschedastic = False # https://github.com/yaringal/multi-task-learning-example/blob/master/multi-task-learning-example.ipynb


@ex.capture
def valid_dataset_class(balance_valid_dataset):
    if balance_valid_dataset:
        return RULDataGenMultipleLabels
    else:
        return DataGenMultipleLabels
@ex.capture
def getImbResampler(imbalanced_resampler):
    if imbalanced_resampler is None:
        return None
    elif imbalanced_resampler == "SMOTE":
        return SMOTE()
    elif imbalanced_resampler == "rul":
        return RandomUnderSampler()


def get_random_channel_ordering():
    channel_ordering = [i for i in range(len(util_funcs.get_common_channel_names()))]
    np.random.shuffle(channel_ordering)
    return channel_ordering


@ex.capture
def resample_x_y(x, y, imbalanced_resampler):
    if imbalanced_resampler is None:
        return x, y
    else:
        oldShape = x.shape
        resampleX, resampleY = getImbResampler().fit_resample(x.reshape(x.shape[0], -1), y)
        return resampleX.reshape(resampleX.shape[0], *oldShape[1:]), resampleY


@ex.capture
def getDataSampleGenerator(pre_cooldown, post_cooldown, sample_time, num_seconds, n_process):
    return er.EdfDatasetSegments(pre_cooldown=pre_cooldown, post_cooldown=post_cooldown, sample_time=sample_time, num_seconds=num_seconds, n_process=n_process)


@ex.capture
def get_data(mode, max_samples, n_process, max_bckg_samps_per_file, num_seconds, max_bckg_samps_per_file_test, include_seizure_type, include_montage_channels, ref="01_tcp_ar", num_files=None):
    if max_bckg_samps_per_file_test is None:
        max_bckg_samps_per_file_test = max_bckg_samps_per_file
    if max_bckg_samps_per_file_test == -1:
        max_bckg_samps_per_file_test = None
    eds = getDataSampleGenerator()
    train_label_files_segs = eds.get_train_split()
    test_label_files_segs = eds.get_test_split()
    valid_label_files_segs = eds.get_valid_split()

    #increased n_process to deal with io processing

    train_edss = er.EdfDatasetSegmentedSampler(segment_file_tuples=train_label_files_segs, mode=mode, num_samples=max_samples, max_bckg_samps_per_file=max_bckg_samps_per_file, n_process=int(n_process), gap=num_seconds*pd.Timedelta(seconds=1), include_seizure_type=include_seizure_type, include_montage_channels=include_montage_channels)
    valid_edss = er.EdfDatasetSegmentedSampler(segment_file_tuples=valid_label_files_segs, mode=mode, num_samples=max_samples, max_bckg_samps_per_file=max_bckg_samps_per_file_test, n_process=int(n_process), gap=num_seconds*pd.Timedelta(seconds=1), include_seizure_type=include_seizure_type, include_montage_channels=include_montage_channels)
    test_edss = er.EdfDatasetSegmentedSampler(segment_file_tuples=test_label_files_segs, mode=mode, num_samples=max_samples, max_bckg_samps_per_file=max_bckg_samps_per_file_test, n_process=int(n_process), gap=num_seconds*pd.Timedelta(seconds=1), include_seizure_type=include_seizure_type, include_montage_channels=include_montage_channels)
    pkl.dump((train_edss, valid_edss, test_edss), open("/n/scratch2/ms994/seizure_multi_labels_edss_info.pkl", "wb"))
    ex.add_artifact("/n/scratch2/ms994/seizure_multi_labels_edss_info.pkl")
    return train_edss, valid_edss, test_edss
@ex.capture
def get_homeo_layer(use_relative):
    if use_relative:
        return RelativeHomeoschedasticMultiLossLayer
    return HomeoschedasticMultiLossLayer

@ex.capture
def get_optimizer(optimizer_name):
    if optimizer_name == "adam":
        return optimizers.Adam
    elif optimizer_name == "sgd":
        return optimizers.SGD

@ex.capture
def get_model(
    num_patients,
    num_seconds,
    lr,
    pre_layer_h,
    num_lin_layer,
    num_post_cnn_layers,
    num_post_lin_h,
    num_layers,
    num_filters,
    max_pool_stride,
    use_inception,
    cnn_dropout,
    linear_dropout,
    num_gpus,
    max_pool_size,
    conv_spatial_filter,
    conv_temporal_filter,
    num_conv_temporal_layers,
    num_temporal_filter,
    use_batch_normalization,
    use_lstm,
    use_time_layers_first,
    max_pool_size_time,
    patient_weight,
    seizure_weight,
    include_seizure_type,
    attach_seizure_type_to_seizure_detect,
    lstm_h,
    lstm_return_sequence,
    model_type,
    add_gaussian_noise,
    include_montage_channels,
    attach_patient_layer_to_cnn_output,
    use_montage_channels_instead_of_montage_num,
    separate_out_mlp,
    use_homeoschedastic):
    input_time_size = num_seconds * constants.COMMON_FREQ
    x = Input((input_time_size, 21, 1)) #time, ecg channel, cnn channel
    if add_gaussian_noise is not None:
        y = GaussianNoise(add_gaussian_noise)(x)
    else:
        y = x
    if num_lin_layer != 0:
        y = Reshape((input_time_size, 21))(y) #remove channel dim
        for i in range(num_lin_layer):
            y = TimeDistributed(Dense(pre_layer_h, activation="relu"))(y)
            # y = TimeDistributed(Dropout(linear_dropout))(y)

        y = Reshape((input_time_size, pre_layer_h, 1))(y) #add back in channel dim
    else:
        y = x
    if use_inception:
        _, y = inception_like_pre_layers(input_shape=(input_time_size,21,1), x=y, dropout=cnn_dropout, max_pool_size=max_pool_size, max_pool_stride=max_pool_stride, num_layers=num_layers, num_filters=num_filters)
    elif model_type=="time_distributed_dense":
        for i in range(num_conv_temporal_layers):
            y = Conv2D(num_conv_temporal_layers, conv_temporal_filter, activation="relu")(y)
            y = MaxPool2D(max_pool_size)(y)

        for i in range(2):
            if use_batch_normalization:
                y = layers.BatchNormalization()(y)
            y = Conv2D(num_filters, conv_spatial_filter, activation="relu")(y)
            y = MaxPool2D(max_pool_size)(y)
            y = TimeDistributed(Dense(y.get_shape()[2].value, activation="relu"))(y)
            y = TimeDistributed(Dropout(cnn_dropout))(y)
            y = TimeDistributed(Dense(y.get_shape()[2].value, activation="relu"))(y)
    elif model_type=="cnn1d":
        y = layers.Reshape((input_time_size, 21))(y)
        for i in range(num_layers):
            if use_batch_normalization:
                y = layers.BatchNormalization()(y)
            y = layers.Conv1D(num_filters, (4), activation="relu")(y)
            y = layers.MaxPool1D((2))(y)
        y = layers.Reshape((y.shape[1].value, y.shape[2].value, 1))(y)
    elif model_type=="lstm_only":
        y = layers.Reshape((50, int(input_time_size/50 * 21)))(y)
        for i in range(num_layers):
            y = layers.CuDNNLSTM(lstm_h, return_sequences=True)(y)
        y = layers.Reshape((y.shape[1].value, y.shape[2].value, 1))(y)
    else:
        _, y = conv2d_gridsearch_pre_layers(input_shape=(input_time_size,21,1),
                                            x=y,
                                            conv_spatial_filter=conv_spatial_filter,
                                            conv_temporal_filter=conv_temporal_filter,
                                            num_conv_temporal_layers=num_conv_temporal_layers,
                                            max_pool_size=max_pool_size,
                                            max_pool_stride=max_pool_stride,
                                            dropout=cnn_dropout,
                                            num_conv_spatial_layers=num_layers,
                                            num_spatial_filter=num_filters,
                                            num_temporal_filter=num_temporal_filter,
                                            use_batch_normalization=use_batch_normalization,
                                            max_pool_size_time=max_pool_size_time,
                                            time_convolutions_first=use_time_layers_first)
    # y = Dropout(0.5)(y)
    if not use_lstm:
        y_flatten = Flatten()(y)
        y = y_flatten
    else:
        y = Reshape((int(y.shape[1]), int(y.shape[2]) * int(y.shape[3])))(y)
        y = CuDNNLSTM(lstm_h, return_sequences=lstm_return_sequence)(y)
        if lstm_return_sequence:
            y = Flatten()(y)
        y_flatten = y


    for i in range(num_post_cnn_layers):
        y = Dense(num_post_lin_h, activation='relu')(y)
        y = Dropout(linear_dropout)(y)

    if separate_out_mlp:
        y1 = y_flatten
        for i in range(num_post_cnn_layers):
            y1 = Dense(num_post_lin_h, activation='relu')(y1)
            y1 = Dropout(linear_dropout)(y1)
    else:
        y1 = y

    y_seizure_subtype = Dense(len(constants.SEIZURE_SUBTYPES), activation="softmax", name="seizure_subtype")(y1)
    if include_seizure_type and attach_seizure_type_to_seizure_detect:
        y = Concatenate()([y, y_seizure_subtype])
    y_seizure = Dense(2, activation="softmax", name="seizure")(y)
    if not attach_patient_layer_to_cnn_output:
        y_patient = Dense(num_patients, activation="softmax", name="patient")(y)
    else:
        y_patient = Dense(num_patients, activation="softmax", name="patient")(y_flatten)

    if separate_out_mlp:
        y2 = y_flatten
        for i in range(num_post_cnn_layers):
            y2 = Dense(num_post_lin_h, activation='relu')(y2)
            y2 = Dropout(linear_dropout)(y2)
    else:
        y2 = y
    if use_montage_channels_instead_of_montage_num:
        y_montage_channel = Dense( len(util_funcs.get_common_channel_names()), activation="sigmoid", name="montage_channel")(y2)
    else:
        y_montage_channel = Dense(len(constants.MONTAGE_COLUMNS), activation="sigmoid", name="montage_channel")(y2)




    seizure_model = Model(inputs=x, outputs=[y_seizure])

    if include_seizure_type and include_montage_channels:
        seizure_patient_model = Model(inputs=[x], outputs=[y_seizure, y_patient,  y_seizure_subtype, y_montage_channel])
        val_train_model = Model(inputs=x, outputs=[y_seizure, y_seizure_subtype, y_montage_channel])
    elif include_seizure_type:
        seizure_patient_model = Model(inputs=[x], outputs=[y_seizure, y_patient,  y_seizure_subtype,])
        val_train_model = Model(inputs=x, outputs=[y_seizure, y_seizure_subtype])
    else:
        seizure_patient_model = Model(inputs=[x], outputs=[y_seizure, y_patient,])
        val_train_model = seizure_model

    patient_model = Model(inputs=[x], outputs=[y_patient])
    print(seizure_patient_model.summary())
    if num_gpus > 1:
        seizure_model = multi_gpu_model(seizure_model, num_gpus)
        seizure_patient_model = multi_gpu_model(seizure_patient_model, num_gpus)
        patient_model = multi_gpu_model(patient_model, num_gpus)

    seizure_model.compile(get_optimizer()(lr=lr), loss=["categorical_crossentropy"], metrics=["accuracy"])
    if include_seizure_type and include_montage_channels:
        loss_weights = [K.variable(seizure_weight),K.variable(patient_weight), K.variable(seizure_weight), K.variable(seizure_weight)]
        seizure_patient_model.compile(get_optimizer()(lr=lr), loss=["categorical_crossentropy", "categorical_crossentropy", "categorical_crossentropy", "binary_crossentropy"], loss_weights=loss_weights, metrics=["accuracy", tf.keras.metrics.AUC(), f1])
    elif include_seizure_type:
        loss_weights = [K.variable(seizure_weight),K.variable(patient_weight), K.variable(seizure_weight)]
        seizure_patient_model.compile(get_optimizer()(lr=lr), loss=["categorical_crossentropy", "categorical_crossentropy", "categorical_crossentropy"], loss_weights=loss_weights, metrics=["accuracy", f1])
    elif not include_seizure_type and not include_montage_channels:
        loss_weights = [K.variable(seizure_weight),K.variable(patient_weight)]
        seizure_patient_model.compile(get_optimizer()(lr=lr), loss=["categorical_crossentropy",  "categorical_crossentropy"], loss_weights=loss_weights, metrics=["categorical_accuracy", f1])
    else:
        raise Exception("Not Implemented")

    patient_model.compile(get_optimizer()(lr=lr), loss=["categorical_crossentropy"], metrics=["categorical_accuracy"])
    if use_homeoschedastic and not include_seizure_type and not include_montage_channels:
        y_seizure_true_input = Input((2,))
        y_patient_true_input = Input((num_patients,))
        y_total = get_homeo_layer()(
            nb_outputs=2,
            loss_funcs=[categorical_crossentropy, categorical_crossentropy],
            multiplier=[seizure_weight,patient_weight])([ y_seizure_true_input, y_patient_true_input, y_seizure, y_patient, ])
        homeoschedastic_model = Model(inputs=[x, y_seizure_true_input, y_patient_true_input], outputs=[y_total])
        homeoschedastic_model.compile(get_optimizer()(lr=lr), loss=None, metrics=["categorical_accuracy", f1])
        # homeoschedastic_model.
        return seizure_model, seizure_patient_model, patient_model, val_train_model, x, y, loss_weights, homeoschedastic_model
    if use_homeoschedastic:
        if not include_seizure_type or not include_montage_channels or not use_montage_channels_instead_of_montage_num:
            raise Exception("Not implemented yet")
        y_seizure_true_input = Input((2,))
        y_patient_true_input = Input((num_patients,))
        y_subtype_true_input = Input((len(constants.SEIZURE_SUBTYPES), ))
        y_montage_true_input = Input((len(util_funcs.get_common_channel_names()),))
        y_total = get_homeo_layer()(
            nb_outputs=4,
            loss_funcs=[categorical_crossentropy, categorical_crossentropy, categorical_crossentropy, binary_crossentropy],
            multiplier=[seizure_weight,patient_weight,1,1])([ y_seizure_true_input, y_patient_true_input, y_subtype_true_input, y_montage_true_input, y_seizure, y_patient,  y_seizure_subtype, y_montage_channel,])
        homeoschedastic_model = Model(inputs=[x, y_seizure_true_input, y_patient_true_input, y_subtype_true_input, y_montage_true_input], outputs=[y_total])
        homeoschedastic_model.compile(get_optimizer()(lr=lr), loss=None, metrics=["categorical_accuracy", f1])
        # homeoschedastic_model.
        return seizure_model, seizure_patient_model, patient_model, val_train_model, x, y, loss_weights, homeoschedastic_model
    return seizure_model, seizure_patient_model, patient_model, val_train_model, x, y, loss_weights

global_model = None

@ex.capture
def recompile_model(seizure_patient_model,  epoch_num, seizure_weight, min_seizure_weight, patient_weight,  loss_weights, include_seizure_type, lr, separate_seizure_classification_weight, lr_decay, seizure_weight_decay, reduce_lr_on_plateau, include_montage_channels, use_homeoschedastic):
    if lr_decay == 0 or lr_decay is None:
        new_lr = lr
    elif not reduce_lr_on_plateau:
        new_lr = lr * (lr_decay) ** ((epoch_num))
    else:
        new_lr = lr
    K.set_value(seizure_patient_model.optimizer.lr, lr)
    if use_homeoschedastic:
        seizure_patient_model.compile(seizure_patient_model.optimizer, loss=None)
        seizure_patient_model.metrics_tensors += seizure_patient_model.outputs
        return seizure_patient_model
    if separate_seizure_classification_weight is  None:
        separate_seizure_classification_weight = seizure_weight
    if seizure_weight_decay is not None:
        if seizure_weight_decay is None:
            seizure_weight_decay = 1

        # weight_decay = seizure_weight_decay ** ((epoch_num))
        # new_weight = seizure_weight * weight_decay
        if min_seizure_weight is None:
            min_seizure_weight = 0
        if min_seizure_weight is not None or min_seizure_weight != 0:
            new_weight = (seizure_weight - min_seizure_weight) * np.e ** (np.log(seizure_weight_decay) * epoch_num + 1) + min_seizure_weight * np.e
            new_weight /= np.e
        print("Epoch: {}, Seizure Weight: {}, Patient Weight: {}, lr: {}".format(epoch_num, new_weight, patient_weight, new_lr))
        if include_seizure_type and include_montage_channels:
            seizure_patient_model.compile(seizure_patient_model.optimizer, loss=["categorical_crossentropy", "categorical_crossentropy", "categorical_crossentropy", "binary_crossentropy"], loss_weights=[new_weight, patient_weight, new_weight, separate_seizure_classification_weight], metrics=["categorical_accuracy", f1])

        elif include_seizure_type and seizure_weight_decay is not None:
             # K.set_value(
             #Don't throw away old optimizer TODO: check and see if adam keeps any state in its optimizer object
            seizure_patient_model.compile(seizure_patient_model.optimizer, loss=["categorical_crossentropy", "categorical_crossentropy", "categorical_crossentropy"], loss_weights=[new_weight, patient_weight, separate_seizure_classification_weight], metrics=["categorical_accuracy", f1])
        elif seizure_weight_decay is not None:
            seizure_patient_model.compile(seizure_patient_model.optimizer, loss=["categorical_crossentropy",  "categorical_crossentropy"], loss_weights=[new_weight, patient_weight,], metrics=["categorical_accuracy", f1])
    # seizure_patient_model.metrics_tensors += seizure_patient_model.outputs #grab output!

    return seizure_patient_model



@ex.capture
def get_model_checkpoint(model_name, early_stopping_on):
    return ModelCheckpoint(model_name, monitor=early_stopping_on, save_best_only=True, verbose=1)


@ex.capture
def get_early_stopping(patience, early_stopping_on):
    return EarlyStopping(patience=patience, verbose=1, monitor=early_stopping_on)

@ex.capture
def get_cb_list():
    return [get_model_checkpoint(), get_early_stopping()]

@ex.capture
def reorder_channels(data, randomly_reorder_channels, random_channel_ordering):
    if randomly_reorder_channels:
        newData = []
        for datum_tuple in data[0]:
            datum_tuple_first = datum_tuple[0][:,random_channel_ordering]
            newData.append((datum_tuple_first, *datum_tuple[1:]))
        return (newData, *data[1:])
    else:
        return data

@functools.lru_cache(maxsize=5)
def transform_matrix():
    transform_mat = np.zeros((len(constants.MONTAGE_COLUMN_TUPLES), len(util_funcs.get_common_channel_names())))
    for i, (j, k) in enumerate(constants.MONTAGE_COLUMN_TUPLES):
        transform_mat[i,j]=1
        transform_mat[i,k]=1

    return transform_mat


@ex.capture
def update_montage_channels(sing_y_montage, use_montage_channels_instead_of_montage_num):
    if not use_montage_channels_instead_of_montage_num:
        return sing_y_montage.values
    else:
        sing_y_montage = sing_y_montage.values.reshape((1,-1))
        return np.matmul(sing_y_montage, transform_matrix()).reshape(-1) != 0



@ex.capture
def update_data(edss, seizure_classification_only, seizure_classes_to_use, include_seizure_type, include_montage_channels, remove_outlier_by_std_thresh, zero_center_over_channel, zero_center_over_time, is_eval_set=False):
    '''
    since we store the full string of the session or the patient instead of the index, we update the data to use the int index
    some of the tasks require different datasets and some filtering of the data i.e. only seizure classification or just some of the labels
    is_eval_set: for use with valid and test set, since they shouldn't have patients from the train set and therefore predicting for them is wrong
    '''

    data = [datum[0] for datum in edss]
    if is_eval_set:
        patient_labels = [0 for i in range(len(edss))]
        remove_outlier_by_std_thresh=None
    else:
        patients = [datum[1][1] for datum in edss]
        allPatient = list(set(patients))
        patient_labels = [allPatient.index(patient) for patient in patients]
    seizure_detection_labels = [datum[1][0] for datum in edss]
    if include_seizure_type:
        seizure_class_labels = [datum[1][2] for datum in edss]
    if include_montage_channels:
        montage_channel_labels = [datum[1][3] for datum in edss]
    keep_index = [True for i in range(len(data))]
    if seizure_classes_to_use is not None:
        for i, seizure_class_label in enumerate(seizure_class_labels):
            if seizure_detection_labels[i] and constants.SEIZURE_SUBTYPES[seizure_class_label] not in seizure_classes_to_use: #it's a seizure detection class and it should be excluded
                keep_index[i] = False
    if seizure_classification_only:
        for i, seizure_detect in enumerate(seizure_detection_labels):
            if not seizure_detect:
                keep_index[i] = False

    if zero_center_over_time:
        for i, datum in enumerate(data):
            data[i] = (datum.T - datum.mean(1)).T
    if zero_center_over_channel:
        for i, datum in enumerate(data):
            data[i] = datum - datum.mean(0)
    if remove_outlier_by_std_thresh is not None:
        removed = 0
        for i, datum in enumerate(data):
            if np.std(datum) > remove_outlier_by_std_thresh:
                keep_index[i] = False
                removed += 1
        print("We removed {} because unclean by std".format(removed))


    data_to_keep = []
    patient_labels_to_keep = []
    seizure_detect_to_keep = []
    seizure_class_labels_to_keep = []
    montage_channel_labels_to_keep = []

    for i, should_keep in enumerate(keep_index):
        if should_keep:
            data_to_keep.append(data[i])
            patient_labels_to_keep.append(patient_labels[i])
            seizure_detect_to_keep.append(seizure_detection_labels[i])
            if include_montage_channels:
                montage_channel_labels_to_keep.append(montage_channel_labels[i])
            if include_seizure_type:
                seizure_class_labels_to_keep.append(seizure_class_labels[i])
    if include_montage_channels and include_seizure_type:

        return [(data_to_keep[i], (seizure_detect_to_keep[i], patient_labels_to_keep[i], seizure_class_labels_to_keep[i], update_montage_channels(montage_channel_labels_to_keep[i]))) for i in range(len(data_to_keep))], seizure_detect_to_keep, patient_labels_to_keep, seizure_class_labels_to_keep, montage_channel_labels_to_keep
    elif include_montage_channels:
        raise Exception("Not implemented yet")
    elif include_seizure_type:
        return [(data_to_keep[i], (seizure_detect_to_keep[i], patient_labels_to_keep[i], seizure_class_labels_to_keep[i])) for i in range(len(data_to_keep))], seizure_detect_to_keep, patient_labels_to_keep, seizure_class_labels_to_keep
    else:
        return [(data_to_keep[i], (seizure_detect_to_keep[i], patient_labels_to_keep[i])) for i in range(len(data_to_keep))], seizure_detect_to_keep, patient_labels_to_keep

@ex.capture
def patient_func(tkn_file_paths, session_instead_patient):
    if session_instead_patient:
        return [read.parse_edf_token_path_structure(tkn_file_path)[1] + "/" + read.parse_edf_token_path_structure(tkn_file_path)[2] for tkn_file_path in tkn_file_paths]
    else:
        return [read.parse_edf_token_path_structure(tkn_file_path)[1] for tkn_file_path in tkn_file_paths]
@ex.capture
def get_data_generators(train_pkl,  valid_pkl, test_pkl, regenerate_data, use_standard_scaler, precache, batch_size, n_process, include_seizure_type, include_montage_channels, use_montage_channels_instead_of_montage_num):
    allPatients = []
    seizureLabels = []
    validSeizureLabels = []
    validPatientInd = []
    patientInd = []
    if path.exists(train_pkl) and precache:
        print("Loading data")
        test_edss = pkl.load(open(test_pkl, 'rb'))
        print("loaded test")
        train_edss = pkl.load(open(train_pkl, 'rb'))
        print("loaded train")
        valid_edss = pkl.load(open(valid_pkl, 'rb'))
        print("Loading data completed")



        # validPatientInd

        seizureLabels = [datum[1][0] for datum in train_edss]
        if include_seizure_type:
            seizureSubtypes = [datum[1][2] for datum in train_edss]
            validSeizureSubtypes = [datum[1][2] for datum in valid_edss]
        validSeizureLabels = [datum[1][0] for datum in valid_edss]
    else:
        print("(Re)generating data")
        train_edss, valid_edss, test_edss = get_data()
        # tkn_file_paths = [train_edss.sampleInfo[key].token_file_path for key in train_edss.sampleInfo.keys()]

        # allPatients = list(set(patients))
        # patientInd = [allPatients.index(patient) for patient in patients]
        seizureLabels = [train_edss.sampleInfo[key].label for key in train_edss.sampleInfo.keys()]
        train_patients = patient_func( [train_edss.sampleInfo[key].token_file_path for key in train_edss.sampleInfo.keys()])
        validSeizureLabels = [valid_edss.sampleInfo[key].label for key in valid_edss.sampleInfo.keys()]
        valid_patients = patient_func( [valid_edss.sampleInfo[key].token_file_path for key in valid_edss.sampleInfo.keys()])
        testSeizureLabels = [test_edss.sampleInfo[key].label for key in test_edss.sampleInfo.keys()]
        test_patients = patient_func( [test_edss.sampleInfo[key].token_file_path for key in test_edss.sampleInfo.keys()])


        validPatientInd = [0 for i in range(len(validSeizureLabels))]
        if not include_seizure_type:
            for i in range(len(seizureLabels)):
                train_edss.sampleInfo[i].label = (seizureLabels[i], train_patients[i])
            for i in range(len(validSeizureLabels)):
                valid_edss.sampleInfo[i].label = (validSeizureLabels[i], valid_patients[i]) #the network has too many parameters if you include validation set patients (mutually exclusive) and the neural network should never choose validation patients anyways
        else:
            for i in range(len(seizureLabels)):
                train_edss.sampleInfo[i].label = (seizureLabels[i][0], train_patients[i], constants.SEIZURE_SUBTYPES.index(seizureLabels[i][1].lower()))
            for i in range(len(validSeizureLabels)):
                valid_edss.sampleInfo[i].label = (validSeizureLabels[i][0], valid_patients[i], constants.SEIZURE_SUBTYPES.index(validSeizureLabels[i][1].lower()))
            for i in range(len(testSeizureLabels)):
                test_edss.sampleInfo[i].label = (testSeizureLabels[i][0], test_patients[i], constants.SEIZURE_SUBTYPES.index(testSeizureLabels[i][1].lower()))

        train_edss = train_edss[:]
        valid_edss = valid_edss[:]
        test_edss = test_edss[:]



        pkl.dump(train_edss[:], open(train_pkl, 'wb'))
        pkl.dump(valid_edss[:], open(valid_pkl, 'wb'))
        pkl.dump(test_edss[:], open(test_pkl, 'wb'))

    #we want to have an actual string stored in record so we can do some more dissection on the segments, but we want an integer index when we run the code
    patients = [datum[1][1] for datum in train_edss]
    allPatients = list(set(patients))
    patientInd = [allPatients.index(patient) for patient in patients]
    validPatientInd = [0 for i in range(len(valid_edss))] #we don't actually care about predicting valid patients, since the split should be patient wise


    train_edss = update_data(train_edss)
    valid_edss = update_data(valid_edss, is_eval_set=True)
    test_edss = update_data(test_edss, is_eval_set=True)



    if include_seizure_type and not include_montage_channels:
        train_edss, seizureLabels, patientInd, seizureSubtypes = reorder_channels(train_edss)
        valid_edss, validSeizureLabels, validPatientInd, validSeizureSubtypes = reorder_channels(valid_edss)
        test_edss, _, _, testSeizureSubtypes = reorder_channels(test_edss)
    elif include_seizure_type and include_montage_channels:
        train_edss, seizureLabels, patientInd, seizureSubtypes, montageLabels = reorder_channels(train_edss)
        valid_edss, validSeizureLabels, validPatientInd, validSeizureSubtypes, validMontageLabels = reorder_channels(valid_edss)
        test_edss, testSeizureLabels, testPatientInd, testSeizureSubtypes, testMontageLabels = reorder_channels(test_edss)
    elif not include_seizure_type and not include_montage_channels:
        train_edss, seizureLabels, patientInd  = reorder_channels(train_edss)
        valid_edss, validSeizureLabels, validPatientInd  = reorder_channels(valid_edss)
        test_edss, testSeizureLabels, testPatientInd  = reorder_channels(test_edss)
    else:
        raise Exception("Not implemented yet")

    if use_standard_scaler:
        print("start standard scaling")
        # start = time()
        train_edss = read.EdfStandardScaler(
            train_edss, dataset_includes_label=True, n_process=n_process)
        train_edss.use_mp=False
        # print(time-start)
        valid_edss = read.EdfStandardScaler(
            valid_edss, dataset_includes_label=True, n_process=n_process)
        valid_edss.use_mp=False

        # print(time-start)

        test_edss = read.EdfStandardScaler(
            test_edss, dataset_includes_label=True, n_process=n_process)
        test_edss.use_mp=False

        # print(time-start)

        print("completed")


    if include_seizure_type and not include_montage_channels:
        edg = RULDataGenMultipleLabels(train_edss, num_labels=3, precache=not use_standard_scaler, batch_size=batch_size, labels=[seizureLabels, patientInd, seizureSubtypes], n_classes=(2, len(allPatients), len(constants.SEIZURE_SUBTYPES)),)
        valid_edg = valid_dataset_class()(valid_edss, num_labels=3, precache=not use_standard_scaler, batch_size=batch_size*4, labels=[validSeizureLabels, validPatientInd, validSeizureSubtypes], xy_tuple_form=True, n_classes=(2, len(allPatients), len(constants.SEIZURE_SUBTYPES)), shuffle=False)
        test_edg = DataGenMultipleLabels(test_edss, num_labels=3, precache=not use_standard_scaler, n_classes=(2, len(allPatients), len(constants.SEIZURE_SUBTYPES)), batch_size=batch_size*4, shuffle=False)
    elif include_seizure_type and include_montage_channels and use_montage_channels_instead_of_montage_num:
        edg = RULDataGenMultipleLabels(train_edss, num_labels=4, precache=not use_standard_scaler, class_type=["nominal", "nominal", "nominal", "quantile"], batch_size=batch_size, labels=[seizureLabels, patientInd, seizureSubtypes, montageLabels], n_classes=(2, len(allPatients), len(constants.SEIZURE_SUBTYPES), len(util_funcs.get_common_channel_names())),)
        valid_edg = valid_dataset_class()(valid_edss, num_labels=4, precache=not use_standard_scaler, class_type=["nominal", "nominal", "nominal", "quantile"], batch_size=batch_size*4, labels=[validSeizureLabels, validPatientInd, validSeizureSubtypes, validMontageLabels], xy_tuple_form=True, n_classes=(2, len(allPatients), len(constants.SEIZURE_SUBTYPES), len(util_funcs.get_common_channel_names())), shuffle=False)
        test_edg = DataGenMultipleLabels(test_edss, num_labels=4, precache=not use_standard_scaler, class_type=["nominal", "nominal", "nominal", "quantile"], labels=[testSeizureLabels, testPatientInd, testSeizureSubtypes, testMontageLabels], n_classes=(2, len(allPatients), len(constants.SEIZURE_SUBTYPES), len(util_funcs.get_common_channel_names())), batch_size=batch_size*4, shuffle=False)

    elif include_seizure_type and include_montage_channels:
        edg = RULDataGenMultipleLabels(train_edss, num_labels=4, precache=not use_standard_scaler, class_type=["nominal", "nominal", "nominal", "quantile"], batch_size=batch_size, labels=[seizureLabels, patientInd, seizureSubtypes, montageLabels], n_classes=(2, len(allPatients), len(constants.SEIZURE_SUBTYPES), len(constants.MONTAGE_COLUMNS)),)
        valid_edg = valid_dataset_class()(valid_edss, num_labels=4, precache=not use_standard_scaler, class_type=["nominal", "nominal", "nominal", "quantile"], batch_size=batch_size*4, labels=[validSeizureLabels, validPatientInd, validSeizureSubtypes, validMontageLabels], xy_tuple_form=True, n_classes=(2, len(allPatients), len(constants.SEIZURE_SUBTYPES), len(constants.MONTAGE_COLUMNS)), shuffle=False)
        test_edg = DataGenMultipleLabels(test_edss, num_labels=4, precache=not use_standard_scaler, class_type=["nominal", "nominal", "nominal", "quantile"], labels=[testSeizureLabels, testPatientInd, testSeizureSubtypes, testMontageLabels], n_classes=(2, len(allPatients), len(constants.SEIZURE_SUBTYPES), len(constants.MONTAGE_COLUMNS)), batch_size=batch_size*4, shuffle=False)
    elif not include_seizure_type and not include_montage_channels:
        edg = RULDataGenMultipleLabels(train_edss, num_labels=2, precache=not use_standard_scaler, labels=[seizureLabels, patientInd], batch_size=batch_size, n_classes=(2, len(allPatients)),) #learning means we are more likely to be affected by batch size, both for OOM in gpu and as a hyperparamer
        valid_edg = valid_dataset_class()(valid_edss, num_labels=2, precache=not use_standard_scaler, labels=[validSeizureLabels, validPatientInd], batch_size=batch_size*4, xy_tuple_form=True, n_classes=(2, len(allPatients)), shuffle=False) #batch size doesn't matter as much when we aren't learning but we still need batches to avoid OOM
        if len(test_edss[0][1]) > 1: #we throw out the seizure type label
            data = [datum[0] for datum in test_edss]
            labels = [datum[1][0] for datum in test_edss]
            test_edss = [(data[i], labels[i]) for i in range(len(data))]
        test_edg = EdfDataGenerator(test_edss, n_classes=2, precache=not use_standard_scaler, batch_size=batch_size, shuffle=False)
    return edg, valid_edg, test_edg, len(allPatients)


@ex.capture
def false_alarms_per_hour(fp, total_samps, num_seconds):
    num_chances_per_hour = 60 * 60 / num_seconds
    return (fp / total_samps) * num_chances_per_hour

@ex.capture
def get_test_patient_edg(test_pkl, batch_size):
    test_edss = pkl.load(open(test_pkl, "rb"))
    patients = [datum[1] for datum in test_edss]
    allPatients = list(set(patients))
    patientInd = [allPatients.index(patient) for patient in patients]
    num_patients = len(allPatients)
    # x_data = [datum[0] for datum in test_edss]
    test_edg = EdfDataGenerator(test_edss, labels=patientInd, n_classes=num_patients, batch_size=batch_size, shuffle=True, precache=True)
    return test_edg, num_patients

@ex.capture
def train_patient_accuracy_after_training(x_input, cnn_y, trained_model, train_pkl):
    return test_patient_accuracy_after_training(x_input, cnn_y, trained_model, test_pkl=train_pkl)

@ex.capture
def valid_patient_accuracy_after_training(x_input, cnn_y, trained_model, valid_pkl):
    return test_patient_accuracy_after_training(x_input, cnn_y, trained_model, test_pkl=valid_pkl)



@ex.capture
def test_patient_accuracy_after_training(x_input, cnn_y, trained_model, lr, lr_decay, epochs, model_name, fit_generator_verbosity, test_pkl, num_patients=None):
    # if test_edg is None:
    test_edg, num_patients = get_test_patient_edg(test_pkl=test_pkl)
    # train_test_edg, valid_test_edg = test_edg.create_validation_train_split()
    patient_layer = Dense(num_patients, activation="softmax")(cnn_y)
    patient_model = Model(inputs=[x_input], outputs=[patient_layer])
    for i, layer in enumerate(patient_model.layers[:-1]):
        layer.set_weights(trained_model.layers[i].get_weights())
        layer.trainable = False #freeze all layers except last
    print(patient_model.summary())
    patient_model.compile(get_optimizer()(lr=lr), loss=["categorical_crossentropy"], metrics=["categorical_accuracy"])
    test_patient_history = patient_model.fit_generator(test_edg, epochs=epochs, verbose=2, callbacks=[get_model_checkpoint(model_name[:-3] + "_patient.h5"), get_early_stopping(early_stopping_on="loss"), LearningRateScheduler(lambda x, old_lr: old_lr * lr_decay) ])
    return test_patient_history

@ex.capture
def interpret_homeo_output(output, actual, num_patients, use_homeoschedastic, include_montage_channels, use_montage_channels_instead_of_montage_num, include_seizure_type):
    '''
    Since the homeo code compresses multiple layers into a single concatenated layer to avoid any explicit losses from keras, we gotta calculate all of these ourselves
    '''
    if not include_seizure_type and not include_montage_channels:
        y_seizure_pred = output[:,0:2]
        y_patient_pred = output[:,2:num_patients+2]
        seizure_f1 = f1_score(actual[0].argmax(1), y_seizure_pred.argmax(1))
        patient_f1 = f1_score(actual[1].argmax(1), y_patient_pred.argmax(1), average="weighted")
        seizure_acc = accuracy_score(actual[0].argmax(1), y_seizure_pred.argmax(1))
        patient_acc = accuracy_score(actual[1].argmax(1), y_patient_pred.argmax(1))
        patient_loss = log_loss(actual[1], y_patient_pred)
        seizure_loss = log_loss(actual[0], y_seizure_pred)
        return seizure_f1,  patient_f1, patient_acc, seizure_loss, patient_loss, seizure_acc
    assert use_homeoschedastic
    assert include_montage_channels
    assert use_montage_channels_instead_of_montage_num
    assert include_seizure_type
    assert len(output[0]) == num_patients+2+len(constants.SEIZURE_SUBTYPES)+len(util_funcs.get_common_channel_names())
    assert len(actual) == 4
    assert output != actual
    y_seizure_pred = output[:,0:2]
    y_patient_pred = output[:,2:num_patients+2]
    y_subtype_pred = output[:,num_patients+2:num_patients+2+len(constants.SEIZURE_SUBTYPES)]
    y_montage_pred = output[:,num_patients+2+len(constants.SEIZURE_SUBTYPES):]
    seizure_f1 = f1_score(actual[0].argmax(1), y_seizure_pred.argmax(1))
    subtype_f1 = f1_score(actual[2].argmax(1), y_subtype_pred.argmax(1), average='macro')
    patient_f1 = f1_score(actual[1].argmax(1), y_patient_pred.argmax(1), average="weighted")
    # montage_f1 = f1_score(actual[3], y_montage, average="macro")
    montage_f1 = 0
    patient_acc = accuracy_score(actual[1].argmax(1), y_patient_pred.argmax(1))
    seizure_loss = log_loss(actual[0], y_seizure_pred)
    subtype_loss = log_loss(actual[2], y_subtype_pred)
    try:
        patient_loss = log_loss(actual[1], y_patient_pred)
    except Exception:
        patient_loss = 0
    montage_loss = log_loss(actual[3], y_montage_pred)
    subtype_acc = accuracy_score(actual[2].argmax(1), y_subtype_pred.argmax(1))
    montage_acc = accuracy_score(actual[3].astype(np.int)==0, np.round(y_montage_pred).astype(np.int)==0)
    seizure_acc = accuracy_score(actual[0].argmax(1), y_seizure_pred.argmax(1))
    return seizure_f1, subtype_f1, montage_f1, patient_f1, patient_acc, seizure_loss, subtype_loss, patient_loss, montage_loss, seizure_acc, subtype_acc, montage_acc


@ex.main
def main(model_name, mode, num_seconds, imbalanced_resampler,  regenerate_data, epochs,
         fit_generator_verbosity, batch_size, n_process, steps_per_epoch, patience,
         include_seizure_type, max_bckg_samps_per_file_test, seizure_weight,
          seizure_weight_decay, update_seizure_class_weights, seizure_classification_only,
         validation_f1_score_type, reduce_lr_on_plateau, lr, lr_decay, change_batch_size_over_time,
         test_patient_model_after_train, train_patient_model_after_train, valid_patient_model_after_train,
         random_rearrange_each_batch, random_rescale, rescale_factor,
         include_montage_channels, use_montage_channels_instead_of_montage_num,
         use_homeoschedastic):
    seizure_class_weights = {0:1,1:1}
    edg, valid_edg, test_edg, len_all_patients = get_data_generators()
    # patient_class_weights = {}
    # for i in range(len_all_patients):
    #     patient_class_weights[i] = 1

    print("Creating models")

    if use_homeoschedastic:
        seizure_model, seizure_patient_model, patient_model, val_train_model, x_input, cnn_y, loss_weights, homeo_model = get_model(num_patients=len_all_patients)
        homeo_model.metrics_tensors += homeo_model.outputs

    else:
        seizure_model, seizure_patient_model, patient_model, val_train_model, x_input, cnn_y, loss_weights = get_model(num_patients=len_all_patients)

    if regenerate_data:
        return



    num_epochs = epochs
    training_seizure_accs = []
    valid_seizure_accs = []
    train_patient_accs = []
    training_seizure_loss = []
    train_seizure_f1s = []
    train_patient_f1s = []
    train_subtype_f1s = []
    train_montage_f1s = []
    valid_seizure_loss = []
    valid_f1_scores = []
    train_montage_loss = []
    train_montage_acc = []
    val_montage_loss = []
    val_montage_acc = []

    oldPatientWeights = patient_model.layers[-1].get_weights()
    oldNonPatientWeights = [layer.get_weights() for layer in seizure_model.layers[:-1]]
    best_model_loss = -100
    patience_left = patience
    if include_seizure_type:
        subtype_accs = []
        subtype_losses = []
        valid_seizure_subtype_accs = []
        valid_seizure_subtype_loss = []
    if reduce_lr_on_plateau:
        lrs = []
        current_lr = lr
    if change_batch_size_over_time is not None:
        batch_sizes = []
        current_batch_size = edg.batch_size
        # seizure_weights = []
        # current_seizure_weight = seizure_weight

    for i in range(num_epochs):
        if patience_left == 0:
            continue


        if use_homeoschedastic:
            # pass
            recompile_model(homeo_model, i, loss_weights=loss_weights)
        elif reduce_lr_on_plateau:
            lrs.append(current_lr)
            # seizure_weights.append(current_seizure_weight)
            recompile_model(seizure_patient_model, i, loss_weights=loss_weights, lr=current_lr)
        else:
            recompile_model(seizure_patient_model, i, loss_weights=loss_weights,)
        if change_batch_size_over_time is not None:
            batch_sizes.append(current_batch_size)


        valid_labels_full_epoch = []
        valid_labels_epoch= []
        valid_predictions_full = []
        valid_predictions = []

        if include_montage_channels:
            montage_epochs_accs = []
            montage_val_epoch_labels = []
            montage_val_predictions_epoch = []
            montage_val_epoch_labels_full = []
            montage_val_predictions_epoch_full = []

        if include_seizure_type:
            subtype_epochs_accs = []
            subtype_val_epoch_labels = []
            subtype_val_predictions_epoch = []
            subtype_val_epoch_labels_full = []
            subtype_val_predictions_epoch_full = []





        train_seizure_loss_epoch = []
        train_subtype_loss_epoch = []
        train_montage_loss_epoch = []
        train_seizure_f1_epoch = []
        train_subtype_f1_epoch = []
        train_patient_f1_epoch = []
        train_montage_f1_epoch = []

        seizure_accs = []
        patient_accs_epoch = []
        train_montage_acc_epoch = []
        # for j in range(len(edg)):
        if steps_per_epoch is None:
            steps_per_epoch_func = lambda: len(edg)
        else:
            steps_per_epoch_func = lambda: steps_per_epoch
        for j in range(steps_per_epoch_func()):

            train_batch = edg[j]
            data_x = train_batch[0]
            data_x = data_x.astype(np.float32)
            data_x = np.nan_to_num(data_x)
            labels = train_batch[1]

            if random_rearrange_each_batch:
                rearrangement = np.random.choice(21, 21, replace=False)
                data_x = data_x[:,:,rearrangement]
                if include_montage_channels and use_montage_channels_instead_of_montage_num:
                    #since montage consist of spatial info, don't lose it, instead generalize to multiple combinations of channels by using the channel-wise labels
                    montage_channel_labels = labels[3][:,rearrangement]
                    labels = [*labels[0:3], montage_channel_labels]

            if random_rescale:
                data_x = data_x * (np.random.random() * (rescale_factor - 1/rescale_factor) + 1/rescale_factor)

            if use_homeoschedastic and not include_seizure_type and not include_montage_channels:
                loss, output = homeo_model.train_on_batch([data_x, *labels], None)
                seizure_f1,  patient_f1, patient_acc, seizure_loss, patient_loss, seizure_acc = interpret_homeo_output(output, labels, num_patients=len_all_patients)

            elif use_homeoschedastic:
                loss, output = homeo_model.train_on_batch([data_x, *labels], None)
                seizure_f1, subtype_f1, montage_f1, patient_f1, patient_acc, seizure_loss, subtype_loss, patient_loss, montage_loss,  seizure_acc, subtype_acc, montage_acc = interpret_homeo_output(output, labels, num_patients=len_all_patients)
                # raise Exception()
                subtype_epochs_accs.append(subtype_acc)
                # raise Exception()
                train_subtype_f1_epoch.append(subtype_f1)
                train_montage_f1_epoch.append(montage_f1)
            elif include_seizure_type and include_montage_channels:
                loss, seizure_loss, patient_loss, subtype_loss, montage_loss, seizure_acc, seizure_f1, patient_acc, patient_f1,  subtype_acc, subtype_f1, montage_acc, montage_f1 = seizure_patient_model.train_on_batch(data_x, labels, )
                subtype_epochs_accs.append(subtype_acc)
                # raise Exception()
                train_subtype_f1_epoch.append(subtype_f1)
                train_montage_f1_epoch.append(montage_f1)
            elif include_seizure_type:
                loss, seizure_loss, patient_loss, subtype_loss, seizure_acc, seizure_f1, patient_acc, patient_f1, subtype_acc, subtype_f1 = seizure_patient_model.train_on_batch(data_x, labels, )
                subtype_epochs_accs.append(subtype_acc)
                train_subtype_f1_epoch.append(subtype_f1)
            elif not include_seizure_type and not include_montage_channels:
                loss, seizure_loss, patient_loss, seizure_acc, seizure_f1, patient_acc, patient_f1 = seizure_patient_model.train_on_batch(data_x, labels)
            seizure_accs.append(seizure_acc)
            train_seizure_f1_epoch.append(seizure_f1)
            train_patient_f1_epoch.append(patient_f1)


            #old patient weights are trying to predict for patient, try to do the prediction!
            patient_model.layers[-1].set_weights(oldPatientWeights)
            #keep the other nonpatient weights which try not to predict for patient!
            oldNonPatientWeights = [layer.get_weights() for layer in seizure_model.layers[:-1]]
            patient_loss, patient_acc = patient_model.train_on_batch(train_batch[0], train_batch[1][1])
            patient_accs_epoch.append(patient_acc)

            train_seizure_loss_epoch.append(seizure_loss)
            if include_seizure_type:
                train_subtype_loss_epoch.append(subtype_loss)
            if include_montage_channels:
                train_montage_loss_epoch.append(montage_loss)
                train_montage_acc_epoch.append(montage_acc)

            #get weights that try to predict for patient
            oldPatientWeights = patient_model.layers[-1].get_weights()

            #set weights that don't ruin seizure prediction
            for layer_num, layer in enumerate(seizure_model.layers[:-1]):
                seizure_model.layers[layer_num].set_weights(oldNonPatientWeights[layer_num])
            if (j % int(len(edg)/10)) == 0:
                printEpochUpdateString = "epoch: {} batch: {}/{}, seizure acc: {}, seizure f1: {}, patient acc: {}, loss: {}".format(i, j, len(edg), np.mean(seizure_accs), np.mean(train_seizure_f1_epoch), np.mean(patient_accs_epoch), loss)
                if include_seizure_type:
                    printEpochUpdateString += ", seizure subtype acc: {}, subtype loss: {}".format(np.mean(subtype_epochs_accs), np.mean(train_subtype_loss_epoch))
                if include_montage_channels:
                    printEpochUpdateString += ", seizure montage identification acc: {}, montage loss: {}".format(np.mean(train_montage_acc_epoch), np.mean(train_montage_loss_epoch))
                if use_homeoschedastic:
                    print("weights are now: " + str([weight[0] for weight in homeo_model.layers[-1].get_weights()]))
                print(printEpochUpdateString)
    #     valid_edg.start_background()

        assert valid_labels_epoch == []
        assert valid_predictions == []


        for j in range(len(valid_edg)):
            valid_batch = valid_edg[j]
            data_x = valid_batch[0]
            data_x = data_x.astype(np.float32)
            data_x = np.nan_to_num(data_x) #ssome weird issue with incorrect data conversion


            val_batch_predictions = val_train_model.predict_on_batch(data_x)
            if include_montage_channels and include_seizure_type:
                # montage_val_predictions_epoch.append(val_batch_predictions[2].argmax(1))
                montage_val_predictions_epoch_full.append(val_batch_predictions[2])
                # montage_val_epoch_labels.append(valid_batch[1][3].argmax(1))
                montage_val_epoch_labels_full.append(valid_batch[1][3])

            if include_seizure_type:
                subtype_val_predictions_epoch.append(val_batch_predictions[1].argmax(1))
                subtype_val_predictions_epoch_full.append(val_batch_predictions[1])
                subtype_val_epoch_labels.append(valid_batch[1][2].argmax(1))
                subtype_val_epoch_labels_full.append(valid_batch[1][2])
                valid_labels_epoch.append(valid_batch[1][0].argmax(1))
                valid_labels_full_epoch.append(valid_batch[1][0])
                valid_predictions.append(val_batch_predictions[0].argmax(1))
                valid_predictions_full.append(val_batch_predictions[0])
            else:
                valid_labels_epoch.append(valid_batch[1][0].argmax(1))
                valid_labels_full_epoch.append(valid_batch[1][0])
                valid_predictions.append(val_batch_predictions.argmax(1))
                valid_predictions_full.append(val_batch_predictions)

        def get_sum_seizures():
            num_seizures = 0
            for j in range(len(valid_edg)):
                valid_batch = valid_edg[j]
                num_seizures += valid_batch[1][0].argmax(1).sum()
            return num_seizures

        #random infinitye predictions? I'm assuming some weird type conversion issues and that nan_to_num should fix this

        valid_labels_epoch= np.nan_to_num(np.hstack(valid_labels_epoch).astype(np.float32))
        valid_predictions = np.nan_to_num(np.hstack(valid_predictions).astype(np.float32))


        print("debug: valid_labels_epoch shape {}, valid_predictions.shape {}".format(valid_labels_epoch.shape, valid_predictions.shape))
        print("We predicted {} seizures in the validation split, there were actually {}".format(valid_predictions.sum(), valid_labels_epoch.sum()))
        print("We predicted {} seizure/total in the validation split, there were actually {}".format(valid_predictions.sum()/len(valid_predictions), valid_labels_epoch.sum()/len(valid_labels_epoch)))
        print(classification_report(valid_labels_epoch, valid_predictions))

        if update_seizure_class_weights and valid_predictions.sum()/len(valid_predictions) > 0.95:
            seizure_class_weights[0] *= 1.05
            seizure_class_weights[1] /= 1.05
            print("Updating seizure classes {}".format(seizure_class_weights))
        elif update_seizure_class_weights and valid_predictions.sum()/len(valid_predictions) < 0.05:
            seizure_class_weights[1] *= 1.05
            seizure_class_weights[0] /= 1.05
            print("Updating seizure classes {}".format(seizure_class_weights))




        valid_labels_full_epoch = np.nan_to_num(np.vstack(valid_labels_full_epoch).astype(np.float32))
        valid_predictions_full = np.nan_to_num(np.vstack(valid_predictions_full).astype(np.float32))

        if include_montage_channels:
            # montage_val_epoch_labels = np.nan_to_num(np.hstack(montage_val_epoch_labels).astype(np.float32))
            # montage_val_predictions_epoch = np.nan_to_num(np.hstack(montage_val_predictions_epoch).astype(np.float32))
            montage_val_epoch_labels_full = np.nan_to_num(np.vstack(montage_val_epoch_labels_full).astype(np.float32))
            montage_val_predictions_epoch_full = np.nan_to_num(np.vstack(montage_val_predictions_epoch_full).astype(np.float32))

        if include_seizure_type:
            subtype_val_epoch_labels = np.nan_to_num(np.hstack(subtype_val_epoch_labels).astype(np.float32))
            subtype_val_predictions_epoch = np.nan_to_num(np.hstack(subtype_val_predictions_epoch).astype(np.float32))
            subtype_val_epoch_labels_full = np.nan_to_num(np.vstack(subtype_val_epoch_labels_full).astype(np.float32))
            subtype_val_predictions_epoch_full = np.nan_to_num(np.vstack(subtype_val_predictions_epoch_full).astype(np.float32))



        try:
            auc = roc_auc_score(valid_predictions, valid_labels_epoch)
        except Exception:
            auc = "undefined"
        valid_acc =  accuracy_score(valid_predictions, valid_labels_epoch)
        valid_seizure_accs.append(valid_acc)
        train_patient_accs.append(np.mean(patient_accs_epoch))
        valid_loss = log_loss(valid_labels_full_epoch, valid_predictions_full)
        training_seizure_loss.append(np.mean(train_seizure_loss_epoch))
        train_seizure_f1s.append(np.mean(train_seizure_f1_epoch))
        train_patient_f1s.append(np.mean(train_patient_f1_epoch))

        printEpochEndString = "end epoch: {}, f1: {}, auc: {}, acc: {}, loss: {}\n".format(i, f1_score(valid_predictions, valid_labels_epoch), auc, valid_acc, valid_loss)
        valid_f1_scores.append(f1_score(valid_predictions, valid_labels_epoch))
        valid_seizure_loss.append(valid_loss)
        if include_montage_channels:
            train_montage_f1s.append(np.mean(train_montage_f1_epoch))
            train_montage_loss.append(np.mean(train_montage_loss_epoch))
            train_montage_acc.append(np.mean(train_montage_acc_epoch))

            current_val_epoch_montage_acc = accuracy_score(montage_val_epoch_labels_full.astype(np.int)==0, np.round(montage_val_predictions_epoch_full).astype(np.int)==0)
            current_val_epoch_montage_loss = log_loss(montage_val_epoch_labels_full!=0, montage_val_predictions_epoch_full)
            val_montage_acc.append(current_val_epoch_montage_acc)
            val_montage_loss.append(current_val_epoch_montage_loss)
            printEpochEndString += "\t montage info: train acc: {}, train f1: {}, valid acc:{}, loss: {}\n".format(train_montage_acc[-1], train_seizure_f1s[-1], val_montage_acc[-1], val_montage_loss[-1],)

        if include_seizure_type:
            train_subtype_f1s.append(np.mean(train_subtype_f1_epoch))
            subtype_losses.append(np.mean(train_subtype_loss_epoch))
            subtype_acc = np.mean(subtype_epochs_accs)
            subtype_accs.append(subtype_acc)
            val_subtype_acc = accuracy_score(subtype_val_epoch_labels, subtype_val_predictions_epoch)
            valid_seizure_subtype_accs.append(val_subtype_acc)
            val_subtype_loss = log_loss(subtype_val_epoch_labels_full, subtype_val_predictions_epoch_full)
            valid_seizure_subtype_loss.append(val_subtype_loss)
            macro_subtype_f1 = f1_score(subtype_val_epoch_labels, subtype_val_predictions_epoch, average='macro')
            weighted_subtype_f1 = f1_score(subtype_val_epoch_labels, subtype_val_predictions_epoch, average='weighted')
            printEpochEndString += "\tsubtype info: train acc: {}, valid acc:{}, loss: {}, macro_f1: {}, weighted_f1: {}\n\n".format(subtype_acc, val_subtype_acc, val_subtype_loss, macro_subtype_f1, weighted_subtype_f1)



        print(printEpochEndString)

        if seizure_classification_only:
            new_val_f1 = weighted_subtype_f1
        elif validation_f1_score_type is None:
            new_val_f1 = f1_score(valid_predictions, valid_labels_epoch)
        else:
            new_val_f1 = f1_score(valid_predictions, valid_labels_epoch, average=validation_f1_score_type)
        if (new_val_f1 > best_model_loss):
            patience_left = patience
            best_model_loss = new_val_f1
            try:
                val_train_model.save(model_name)
                print("improved val score to {}".format(best_model_loss))
            except Exception as e:
                print("{}\n".format(e))
                print("failed saving\n")
        else:
            patience_left -= 1
            if reduce_lr_on_plateau:
                current_lr = current_lr * lr_decay
                print("changing batch size {}".format(current_batch_size))

            if patience_left == 0:
                print("Early Stopping!")
        if change_batch_size_over_time is not None:
            edg.batch_size = max(int(edg.batch_size * 3/4), change_batch_size_over_time)
            current_batch_size=edg.batch_size




        training_seizure_accs.append(np.mean(seizure_accs))

        edg.on_epoch_end()
        # valid_edg.on_epoch_end()

    del edg
    del valid_edg
    model = load_model(model_name)




    y_pred = model.predict_generator(test_edg)


    results = Dict()
    results.history = Dict({
        "binary_accuracy": training_seizure_accs,
        "val_binary_accuracy": valid_seizure_accs,
        "seizure_loss": training_seizure_loss,
        "valid_seizure_loss": valid_seizure_loss,
        "patient_acc": train_patient_accs,

    })
    if reduce_lr_on_plateau:
        results.history.lr = lrs
    if change_batch_size_over_time:
        results.history.batch_size = batch_sizes
    if train_patient_model_after_train:
        print("train patient measurement")
        results.patient_history.train = train_patient_accuracy_after_training(x_input, cnn_y, model).history
    if valid_patient_model_after_train:
        print("valid patient measurement")
        results.patient_history.valid = valid_patient_accuracy_after_training(x_input, cnn_y, model).history
    if test_patient_model_after_train:
        print("test patient measurement")
        test_patient_history = test_patient_accuracy_after_training(x_input, cnn_y, model)
        results.patient_history.test = test_patient_history.history


    results.history.seizure.valid_f1 = valid_f1_scores
    results.history.seizure.train_f1 = train_seizure_f1s


    if include_seizure_type:
        results.history.subtype.train_f1 = train_seizure_f1s
        results.history.subtype.acc = subtype_accs
        results.history.subtype.val_acc = valid_seizure_subtype_accs
        results.history.subtype.loss = subtype_losses
        results.history.subtype.val_loss = valid_seizure_subtype_loss

    if include_montage_channels:
        results.history.montage.train_f1 = train_montage_f1s
        results.history.montage.train_acc = train_montage_acc
        results.history.montage.train_loss = train_montage_loss
        results.history.montage.val_acc = val_montage_acc
        results.history.montage.val_loss = val_montage_loss

    if include_seizure_type:
        y_seizure_label =  np.array([data[1][0] for data in test_edg.dataset]).astype(int)
        y_seizure_pred = np.array([y_pred[0].argmax(1)]).astype(int)[0]
        y_subtype_label =  np.array([data[1][2] for data in test_edg.dataset]).astype(int)
        y_subtype_pred = np.array([y_pred[1].argmax(1)]).astype(int)[0]
        results.subtype.acc = accuracy_score(y_subtype_label, y_subtype_pred)
        results.subtype.f1.macro = f1_score(y_subtype_label, y_subtype_pred, average='macro')
        results.subtype.f1.micro = f1_score(y_subtype_label, y_subtype_pred, average='micro')
        results.subtype.f1.weighted = f1_score(y_subtype_label, y_subtype_pred, average='weighted')
        results.subtype.confusion_matrix = confusion_matrix(y_subtype_pred, y_subtype_label)
        results.subtype.classification_report = classification_report(y_subtype_pred, y_subtype_label, output_dict=True)
    else:
        y_seizure_label =  np.array([data[1] for data in test_edg.dataset]).astype(int)
        y_seizure_pred = np.array(y_pred.argmax(1)).astype(int)

    if include_seizure_type and include_montage_channels:
        y_montage_label =  np.array([data[1][3] for data in test_edg.dataset]).astype(int)
        y_montage_pred = np.round(y_pred[2]).astype(int)
        results.montage.acc = accuracy_score(y_montage_label, y_montage_pred)
        results.montage.f1.macro = f1_score(y_montage_label, y_montage_pred, average='macro')
        results.montage.f1.micro = f1_score(y_montage_label, y_montage_pred, average='micro')
        results.montage.f1.weighted = f1_score(y_montage_label, y_montage_pred, average='weighted')
        # results.montage.confusion_matrix = confusion_matrix(y_montage_pred, y_montage_label)
        # results.montage.classification_report = classification_report(y_montage_pred, y_montage_label, output_dict=True)


    print("We predicted {} seizures in the test split, there were actually {}".format(y_seizure_pred.sum(), y_seizure_label.astype(int).sum()))
    print("We predicted {} seizure/total in the test split, there were actually {}".format(y_seizure_pred.sum()/len(y_seizure_pred), y_seizure_label.astype(int).sum()/len(test_edg.dataset)))

    if not seizure_classification_only:
        results.seizure.acc = accuracy_score(y_seizure_pred, y_seizure_label)
        results.seizure.f1 = f1_score(y_seizure_pred, y_seizure_label)
        results.seizure.classification_report = classification_report(y_seizure_label, y_seizure_pred, output_dict=True)
        results.seizure.confusion_matrix = confusion_matrix(y_seizure_label, y_seizure_pred)
        if max_bckg_samps_per_file_test is not None or max_bckg_samps_per_file_test==-1:
            total_samps = sum(results.seizure.confusion_matrix[0]) #just use the samps labeled negative, max_bckg_samps_per_file_test is used to run faster but leads to issues with class imbalance not being fully reflected if we include seizure
        else:
            total_samps = sum(sum(results.seizure.confusion_matrix))
        results.seizure.false_alarms_per_hour = false_alarms_per_hour(results.seizure.confusion_matrix[0][1], total_samps=total_samps)

        try:
            results.seizure.AUC = roc_auc_score(y_seizure_pred, y_seizure_label)
        except Exception:
            results.seizure.AUC = "failed to calculate"

    return results.to_dict()


if __name__ == "__main__":
    ex.run_commandline()
