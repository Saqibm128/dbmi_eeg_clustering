# dbmi_eeg_clustering
Uses the TUH dataset:  https://www.isip.piconepress.com/projects/tuh_eeg/

This dataset is segmented into a train set and test set and includes annotations.
In addition, there are subsets of the data based on the exact reference node of the EEG.

## Setup
Reads the directory of the data using config.json file

``` config.json
{
  "mongo_uri": "mongodb://user:pass@ip:port",
  "data_dir_root": "/home/ms994/v1.5.0/edf",
  "train_01_tcp_ar": "/home/ms994/v1.5.0/edf/train/01_tcp_ar/",
  "combined_01_tcp_ar": "/home/ms994/v1.5.0/edf/combined/01_tcp_ar/",
  "dev_test_01_tcp_ar": "/home/ms994/v1.5.0/edf/dev_test/01_tcp_ar/",
  "train_02_tcp_le": "/home/ms994/v1.5.0/edf/train/02_tcp_le/",
  "dev_test_02_tcp_le": "/home/ms994/v1.5.0/edf/dev_test/02_tcp_le/",
  "train_03_tcp_ar_a": "/home/ms994/v1.5.0/edf/dev_test/03_tcp_ar_a/",
  "dev_test_03_tcp_ar_a": "/home/ms994/v1.5.0/edf/train/03_tcp_ar_a/",
  "seizure_tse_root": "/n/scratch2/ms994/",
  "seizure_config": {
    "data_dir_root": "/home/ms994/v1.5.0/edf",
    "train_01_tcp_ar": "/home/ms994/v1.5.0/edf/train/01_tcp_ar/",
    "combined_01_tcp_ar": "/home/ms994/v1.5.0/edf/combined/01_tcp_ar/",
    "dev_test_01_tcp_ar": "/home/ms994/v1.5.0/edf/dev_test/01_tcp_ar/",
    "train_02_tcp_le": "/home/ms994/v1.5.0/edf/train/02_tcp_le/",
    "dev_test_02_tcp_le": "/home/ms994/v1.5.0/edf/dev_test/02_tcp_le/",
    "train_03_tcp_ar_a": "/home/ms994/v1.5.0/edf/dev_test/03_tcp_ar_a/",
    "dev_test_03_tcp_ar_a": "/home/ms994/v1.5.0/edf/train/03_tcp_ar_a/"
  },
  "tuh_eeg_all": {
    "data_dir_root": "/n/scratch2/ms994/tuh_files/tuh_eeg/v1.1.0/edf/",
    "train_01_tcp_ar": "/n/scratch2/ms994/tuh_files/tuh_eeg/v1.1.0/edf/train/01_tcp_ar/",
    "combined_01_tcp_ar": "/n/scratch2/ms994/tuh_files/tuh_eeg/v1.1.0/edf/combined/01_tcp_ar/",
    "dev_test_01_tcp_ar": "/n/scratch2/ms994/tuh_files/tuh_eeg/v1.1.0/edf/dev_test/01_tcp_ar/",
    "train_02_tcp_le": "/n/scratch2/ms994/tuh_files/tuh_eeg/v1.1.0/edf/train/02_tcp_le/",
    "dev_test_02_tcp_le": "/n/scratch2/ms994/tuh_files/tuh_eeg/v1.1.0/edf/dev_test/02_tcp_le/",
    "train_03_tcp_ar_a": "/n/scratch2/ms994/tuh_files/tuh_eeg/v1.1.0/edf/dev_test/03_tcp_ar_a/",
    "dev_test_03_tcp_ar_a": "/n/scratch2/ms994/tuh_files/tuh_eeg/v1.1.0/edf/train/03_tcp_ar_a/"
  }
}

```

## Code Overview

### Experiments

Actual experiments are run as python scripts from the experiment folder while in the root project directory.

```
python -u experiments/predictAgeExp.py with  use_lstm n_process=4 num_epochs=150
```



### Reading Data
Data is read using classes from data_reader file or from waveform_analysis/dataset.py file. All classes implement __getitem__ and __len__ (array-like).

(Originally created because of fears that loading entire dataset locally would be too much for local machine, so better to dynamically load data in. https://stanford.edu/~shervine/blog/keras-how-to-generate-data-on-the-fly)
#### EdfDataset
Reads data directly from file structure, returns raw data. Is constructor parameter for other classes

#### EdfFFTDatasetTransformer
Transforms raw data into:
* either an FFT analysis of data for entire window of token file if window parameter is None
* a STFFT (FFT on multiple windows) based on the window given

#### EdfDWTDatasetTransformer
Transforms raw data using DWT

#### SimpleHandEngineeredDataset
Transforms single channel into multiple features using a set of simple uni-channel transforms passed in.

#### BandPassTransformer
Separates out signals from a single channel. Is intended to separate out alpha, beta, delta, theta bands. Will increase number of channels to # bandpass freqs * # channels.

#### CoherenceTransformer
Does coherence transformation. If run in coherence_all mode, then returns all channels coherence with all other channels (increases number of channels to #numchannels * #numchannels - 1)

#### Combining the Transformers and Datasets
All datasets were built with expectation of an array like, so it could be possible to pipe data.

I.e. get hand engineered features of alpha, beta, delta, theta bands then do
(with appropriate args)
```
SimpleHandEngineeredDataset(BandPassTransformer(EdfDataset))
```

### util_funcs.py and constants.py
constants.py determines key constants for project like resampling frequency
util_funcs.py includes utility functions, like reading config data out

## Sacred
Uses sacred to control experiments and provides logging
https://sacred.readthedocs.io/en/latest/

I used MongoObserver to record experiment results

## Project Setup
Notebooks include some test code.
[environmentSetup.sh](environmentSetup.sh) can be used to create a conda environment that can run this code

[data_reader.py](data_reader.py) is used to read data from edf files.
The EdfDataset returns raw data in the form of Pd.DataFrame
The EdfFFTDatasetTransformer returns the same data transformed.

[env.yaml](env.yaml)
the conda environment i'm using

[script_runner.py](script_runner.py)
Used to run the initial_clustering.py file with multiple parameters

[util_funcs.py](util_funcs.py)
Contains a few utility functions, including a MongoClient provider for access to
a db to store sacred experiment results.

## Data Format
data should be accessible using the EdfDataset and EdfFFTDatasetTransformer
EdfDataset and EdfFFTDatasetTransformer is array-like, and will return tuples.
The first elem is the actual data, second is a timeseries by annotation array
showing the assigned probabilities for various annotations

## Data
Data is from TUH project.
https://www.isip.piconepress.com/projects/tuh_eeg/


3d_positions is generated from code in https://github.com/sappelhoff/eeg_positions/

### Notes
Data from all versions are concatenated into a single ALL directory with the use of the TUH_EEG file updates notebook.
(using symlinks to the original location)

2 EEF files are excluded due to issues with channels; there are 50352 edf files, but only 50350 have all 21 common channels.
These were manually removed due to this issue:
tuh_eeg/all//01_tcp_ar/117/00011700/s001_2014_06_11/00011700_s001_t000.edf
tuh_eeg/all//01_tcp_ar/114/00011488/s002_2014_06_06/00011488_s002_t001.edf
