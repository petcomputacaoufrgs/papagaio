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
# Inputs:
#   * path: path to the dataset,
#   * frames_per_bar: how many frames per bar
#   the function encode_data will take
def import_dataset(root_dir, frames_per_bar):
    dataset = []
    num_files_to_add = 0
    for artist in os.listdir(root_dir):
        artist_path = root_dir + '/' + artist
        if artist_path == "clean_midi/Lois_Lane":
          break
        print(artist_path)
        save_artist_path = 'saves/' + artist
        print(save_artist_path)
        os.mkdir(save_artist_path)
        if (not os.path.exists(save_artist_path + '/' + artist + '.pkl')) and \
                (not os.path.exists(save_artist_path + '/' + artist + '.pt')):
            for filename in os.listdir(artist_path):
                if filename.endswith("mid"):
                    num_files_to_add += 1
                    data = encode_data(root_dir + '/' + artist + '/' + filename, frames_per_bar)
                    dataset.append(data)
            train_ds = create_dataset(dataset)
            train_dl = create_dataloader(train_ds)
            save_dataset(train_ds, save_artist_path + '/' + artist)
            save_dataloader(train_dl, save_artist_path + '/' + artist)
            dataset = []

        #input('Continue? Y[ENTER] N[CTRL+C]')
        clear = lambda: os.system('cls')
        clear()

    return dataset


# Preprocess a bar with 'n_in' frames encoded as multi-hot
# encoding and splits it in X, y, whose shape is (n_in-1, 88)
# Inputs:
#   * encoded_seq: multi-hot tensor with 'n_in' frames
#   * n_in: number of frames in the bar
def preprocess_bar(encoded_seq, n_in=32):
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


# Create a torch.Tensor dataset
# Inputs:
#   * dataset: dataset with .mid files
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


def create_vocab(dataset):
    vocab = []
    for song in dataset:
        for part in song:
            for bar in part:
                vocab.append(bar)

    vocab = np.array(vocab)
    vocab = vocab.reshape(vocab.shape[0] * vocab.shape[1], vocab.shape[2])
    vocab = np.unique(vocab, axis=0)

    print(vocab)

    return vocab


# Create a torch DataLoader
# Inputs:
#   * train_ds: torch.Tensor dataset encoded as multi-hot
#   * batch_size
def create_dataloader(train_ds, batch_size=1):
    train_dl = DataLoader(train_ds, batch_size=batch_size, shuffle=False)

    return train_dl


def save_dataset(ds, path):
    torch.save(ds, path + '.pt')


def save_dataloader(dl, path):
    torch.save(dl, path + '.pkl')


def load_dataset(path):
    return torch.load(path)


def load_dataloader(path):
    return torch.load(path)


def test():
    path = '../clean_midi'
    frames_per_bar = 32
    dataset = import_dataset(path, frames_per_bar)
    print(len(dataset))
    #train_ds = create_dataset(dataset)
    #print(len(train_ds))
    #train_dl = create_dataloader(train_ds)
    #print(len(train_dl.dataset))
    #save_dataset(train_ds, 'acdc')
    #save_dataloader(train_dl, 'acdc')


def test_load():
    print('Loading ds ...')
    train_ds = load_dataset('../saves/train_ds')
    print(len(train_ds))
    print('Loading dl ...')
    train_dl = load_dataloader('../saves/train_dl')
    print(len(train_dl.dataset))


if __name__ == '__main__':
    test()
    #test_load()
