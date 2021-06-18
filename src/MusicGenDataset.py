# Basic libraries
import os
import numpy as np
import pandas as pd
# Internal libraries
from GetData import  *
# Data preprocessing libraries
from torch.utils.data import Dataset
from torch.utils.data import DataLoader
from torch.utils.data import TensorDataset
import torch


# Import the whole dataset
#   * Inputs: path to the dataset, how many frames per bar
#   the function encode_data will take
def import_dataset(path, frames_per_bar):
    dataset = []

    for filename in os.listdir(path):
        if filename.endswith("mid"):
            print(path + filename)
            data = encode_data(path + filename, frames_per_bar)
            dataset.append(data)

    return dataset


def preprocess_bar(encoded_seq, n_in=32, n_out=32):
    # create lag copies of the sequence
    df = pd.DataFrame(encoded_seq)
    df = pd.concat([df.shift(n_in - i - 1) for i in range(n_in)], axis=1)

    # drop rows with missing values
    df.dropna(inplace=True)

    # specify columns for input and output values
    values = df.values
    width = encoded_seq.shape[1]

    X = values[:, 0:width * (n_in - 1)].reshape(n_in - 1, width)
    y = values[:, width:].reshape(n_in - 1, width)

    return X, y


def create_dataset(dataset):
    X = []
    y = []

    # create a two arrays X, y with bars
    for song in dataset:
        for part in song:
            for bar in part:
                xa, ya = preprocess_bar(bar)
                X.append(xa)
                y.append(ya)

    X = np.array(X)
    y = np.array(y)
    X = torch.from_numpy(X)
    y = torch.from_numpy(y)
    print(X.shape, y.shape)
    train_ds = TensorDataset(X, y)

    return train_ds


def create_dataloader(train_ds, batch_size=1):
    train_dl = DataLoader(train_ds, batch_size=batch_size, shuffle=False)

    return train_dl


def save_dataset(ds, file_name):
    torch.save(ds, '../saves/' + file_name + '.pt')


def save_dataloader(dl, file_name):
    torch.save(dl, '../saves/' + file_name + '.pkl')


def load_dataset(path):
    return torch.load(path)


def load_dataloader(path):
    return torch.load(path)


if __name__ == '__main__':
    path = '../clean_midi/AC_DC/'
    frames_per_bar = 32
    dataset = import_dataset(path, frames_per_bar)
    print(len(dataset))
    train_ds = create_dataset(dataset)
    print(len(train_ds))
    train_dl = create_dataloader(train_ds)
    print(len(train_dl.dataset))
    save_dataset(train_ds, 'acdc')
    save_dataloader(train_dl, 'acdc')
