import sys, os
sys.path.append(os.path.realpath(".."))
from hyperopt import base
base.have_bson = False
from sacred.initialize import Scaffold
def noop(item):
    pass
Scaffold._warn_about_suspicious_changes = noop

#https://github.com/Lab41/pythia/blob/master/experiments/hyperopt_experiments.py


import sys
import argparse
import os
import pickle
import logging
import copy

import numpy as np
from sklearn.metrics import precision_recall_fscore_support
from sacred import Experiment
from sacred.observers import MongoObserver
from sacred.initialize import Scaffold
import hyperopt
from hyperopt import fmin, tpe, hp, STATUS_OK, Trials
from predictSeizureConvExp import ex

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def objective(args_):
    conv_args = make_args_for_conv(args_)
    print(conv_args)
    try:
        r = ex.run(config_updates=conv_args)
    except Exception as e: #invalid set of params for experiment, likely can't set up correct
        print(e)
        return 0 #0 loss


    return - r.result["seizure"]["f1"]



def make_args_for_conv(args):
    algorithm= args['algorithm_opts']
    passed_args = copy.deepcopy(args)
    passed_args.update(algorithm)
    del passed_args['algorithm_opts']

    algorithm= args['steps_per_epoch_opts']
    passed_args = copy.deepcopy(passed_args)
    passed_args.update(algorithm)
    del passed_args['steps_per_epoch_opts']

    algorithm= args['max_pool_opts']
    passed_args = copy.deepcopy(passed_args)
    passed_args.update(algorithm)
    del passed_args['max_pool_opts']

    if "num_conv_temporal_layers" in passed_args.keys() and \
        passed_args["num_conv_temporal_layers"] + passed_args["num_layers"] > 6:
        passed_args["num_layers"] = 6 - passed_args["num_layers"] #don't do too many layers

    if "steps_per_epoch" in passed_args.keys() and passed_args["steps_per_epoch"] is not None:
         passed_args["patience"] = int(300 /   passed_args["steps_per_epoch"])


    if "use_inception" in passed_args.keys() and passed_args["use_inception"]:
        passed_args["num_filters"] = int(passed_args["num_filters"]/3) #if using inception, don't do an insane number of filters
    return passed_args


def run_pythia_hyperopt():

    global parse_args

    space = {
        "test_pkl": "/n/scratch2/ms994/valid_seizure_data_4.pkl", #create metrics for best model from validation dataset
        "algorithm_opts":hp.choice('algorithm_type', [
                # {
                #     'use_inception': True,
                #
                # },
                {
                    'use_inception': False,
                    "use_batch_normalization": True,
                    # "num_temporal_filter": hp.choice("num_temporal_filter", [30,40,50,60]),
                    "conv_spatial_filter": hp.choice('conv_spatial_filter', [
                        (3,3), (4,4), (2,2)
                    ]),
                    # "conv_temporal_filter": hp.choice("conv_temporal_filter", [(1,3), (1,4), (1,5), (2,3),(2,4), (2,5),]),
                    "num_conv_temporal_layers": 0
                } ]),
        "steps_per_epoch_opts": hp.choice('steps_per_epoch_opts', [
            {
                "steps_per_epoch": hp.choice("steps_per_epoch", [20,40]),
                "patience": 30,
                "epochs": 1000
            },
            {
                "steps_per_epoch": None,
                "patience": 3,
                "epochs": 100
            },
        ]),
        "batch_size": 32,
        "max_pool_opts": hp.choice("max_pool_opts", [
            {
                "max_pool_size": (2,1),
                "max_pool_stride": hp.choice("max_pool_stride_21", [(2,1)])
            },
            {
                "max_pool_size": (2,2),
                "max_pool_stride": hp.choice("max_pool_stride_22", [(2,2)])
            }
        ]),
        "regenerate_data": False,
        "hyperopt_run" : True,
        # "use_standard_scaler": hp.choice("use_standard_scaler", [True, False]),
        "hyperopt_run": True,
        "cnn_dropout": hp.choice("cnn_dropout", [0, 0.1, 0.25, 0.5]),
        "linear_dropout": hp.choice("linear_dropout", [0, 0.25, 0.5]),
        "num_lin_layer": hp.randint("num_lin_layer", 2),
        "num_post_cnn_layers": 0,
        # "num_post_cnn_layers": hp.randint("num_post_cnn_layers", 2),
        # "num_post_lin_h": hp.choice("num_post_lin_h", [5,10,20,25]),
        "pre_layer_h": hp.choice("pre_layer_h", [32,64]),
        "num_filters": hp.choice("num_filters", [1,2,3]),
        "num_layers": hp.choice("num_layers", [1,2,3]),
        # "use_lstm": hp.choice("use_lstm", [True, False])
        "use_lstm":False
    }
    trials = Trials()
    best = fmin(objective, space, algo=tpe.suggest, max_evals=int(parse_args.num_runs), trials=trials)
    print("Best run ", best)
    return trials, best

if __name__ == '__main__':
    """
    Runs a series of test using Hyperopt to determine which parameters are most important
    All tests will be logged using Sacred - if the sacred database is set up correctly, otherwise it will simply run
    To run pass in the number of hyperopt runs, the mongo db address and name, as well as the directory of files to test
    For example for 10 tests:
    python experiments/hyperopt_experiments.py 10 db_server:00000 pythia data/stackexchange/anime
    """


    parser = argparse.ArgumentParser(description="Pythia Hyperopt Tests logging to Sacred")
    parser.add_argument("num_runs", type=int, help="Number of Hyperopt Runs")

    global parse_args
    parse_args = parser.parse_args()

    if int(parse_args.num_runs)<=0:
        print("Must have more than one run")

    # Monkey patch to avoid having to declare all our variables
    def noop(item):
        pass
    Scaffold._warn_about_suspicious_changes = noop

    trial_results, best = run_pythia_hyperopt()
    with open( "pythia_hyperopt_results" + '.pkl', 'wb') as f:
        pickle.dump(trial_results, f, pickle.HIGHEST_PROTOCOL)
