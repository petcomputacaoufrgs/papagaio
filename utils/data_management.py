import pandas as pd
import numpy as np
import glob
import torch
from pathlib import Path
from MidiExpress import read, write
from torch.utils.data import TensorDataset


# Separate Stackframe data from Info data
# TODO: receive a input int for the amount of info data (currently 4).
#       this way testing will be easier.
def getPerformance(data, first_frame, last_frame, to_float=True):
    stackframe = data.iloc[first_frame:last_frame, 4:]
    stackframe = stackframe.to_numpy()

    if to_float:
        stackframe.astype(float)
        stackframe = stackframe + 0.0

    return stackframe


def getInfo(data, first_frame, last_frame):
    infos = data.iloc[first_frame:last_frame, 0:4]
    return infos


# Merge Stackframe and Info to match the codification
def mergeData(infos, stackframe, instrument, midi_offset):
    # (A, B, C)
    #
    # A -> number of measures (bars)
    # B -> number of frames (resolution)
    # C -> number of notes (keyboard size)

    n_measures = stackframe.shape[0]
    resolution = stackframe.shape[1]
    keyboard_size = stackframe.shape[2]

    # Generate note names and use as column
    sf_columns = [key_index2note(i, midi_offset).nameWithOctave for i in range(keyboard_size)]

    # Initialize blank df with notes column
    measures = pd.DataFrame([], columns=sf_columns)
    measures.index.name = 'inst'

    #
    for i in range(n_measures):
        indexes = pd.Series([instrument for i in range(resolution)])
        decoded_measure = pd.DataFrame(stackframe[i], columns=sf_columns).set_index(pd.Index(indexes))
        measures = measures.append(decoded_measure)

    print(f'Info shape {infos.shape} | measures shape {measures.shape}')

    output = pd.concat([infos, measures], axis=1)

    print(f'Result shape {output.shape}')

    return output


# Read all dataset and isolates the data from a single instrument
def createInstrumentPerformanceDataset(datasetPath, instrument, resolution):
    instrumentPerformanceDataset = []
    interpreted_files = glob.glob(f'{datasetPath}**/**.pkl', recursive=True)
    for int_file in interpreted_files:

        int_file_path = Path(int_file)
        interpreted_file = pd.read_pickle(int_file_path)
        # print(interpreted_file.head())

        interpreted_instrument = interpreted_file[interpreted_file.index == instrument]
        if (interpreted_instrument.empty):
            continue
        # print(interpreted_instrument.head())

        first_frame = 0
        last_frame = len(interpreted_instrument)

        interpreted_performance = getStackframe(interpreted_instrument, first_frame=first_frame, last_frame=last_frame)
        # print(interpreted_performance.head())

        instrumentPerformanceDataset.append(np.array(interpreted_performance))

    return instrumentPerformanceDataset


# Split dataset into two blocks, one frame apart at every single index
# I don't know if this one should be here, considering that the transformers can have different training examples
def preparePerformanceTrainingExamples(dataset, resolution):
    X = []
    y = []

    # create two arrays X, y with bars
    for performance in dataset:
        # create the frame blocks shifted in one position
        for i in range(performance.shape[0] - resolution):
            j = i + resolution
            xa = performance[i:j]
            ya = performance[i + 1:j + 1]
            X.append(xa)
            y.append(ya)

    X = np.array(X, dtype='float64')
    y = np.array(y, dtype='float64')
    X = torch.from_numpy(X)
    y = torch.from_numpy(y)

    training_ds = TensorDataset(X, y)  # (X, y)
    return training_ds


def getPerformanceSample(dataloader):
    n_training_examples = len(dataloader.dataset.tensors[0])

    input = torch.zeros(n_training_examples, SETTINGS.RESOLUTION, SETTINGS.KEYBOARD_SIZE)
    target = torch.zeros(n_training_examples, SETTINGS.RESOLUTION, SETTINGS.KEYBOARD_SIZE)

    for sample, (xb, yb) in enumerate(dataloader):  # gets the samples
        input[sample] = xb
        target[sample] = yb

    return input, target