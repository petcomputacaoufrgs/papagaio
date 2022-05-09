import torch
import torch.optim as optim
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from typing import List
import pandas as pd
import glob
import numpy as np
from pathlib import Path


SETTINGS = pd.Series(
  {
    'RESOLUTION': 16, # Frame per measure amount
    'KEYBOARD_SIZE': 88, # Amount of keys in the Model's Keyboard
    'KEYBOARD_OFFSET': 21 # MIDI index for the first Model's Keyboard key
  }
)


NUM_LAYERS = 4

model = BI_LSTM(input_size=SETTINGS.KEYBOARD_SIZE,
                output_size=SETTINGS.KEYBOARD_SIZE,
                hidden_size=SETTINGS.RESOLUTION,
                num_layers=NUM_LAYERS).to(device)

class InstrumentDataset(Dataset):
    def __init__(self, root_dir:str, instrument:str, keyboard_size:int):
        self.root_dir = root_dir
        self.instrument = instrument
        self.keyboard_size = keyboard_size
        self.dataset_files = glob.glob(f'{root_dir}**/**.pkl', recursive=True)

    def __len__(self):
        return len(self.dataset_files)

    def __getitem__(self, idx):

class LSTM(nn.Module):
    def __init__(self, vocab_size, hidden_size, num_layers, output_size):
        super(LSTM, self).__init__()
        self.vocab_size = vocab_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.output_size = output_size








class ShakespeareLSTM(nn.Module):
    def __init__(self, vocab_size, embedding_dim, hidden_size, n_layers):
        super().__init__()
        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim
        self.hidden_size = hidden_size
        self.n_layers = n_layers
        self.embedding_layer = nn.Embedding(vocab_size, embedding_dim)
        self.lstm = nn.LSTM(embedding_dim, hidden_size, n_layers, batch_first=True)
        self.linear = nn.Linear(hidden_size, vocab_size)

    def forward(self, x, h0=None, c0=None):
        x = self.embedding_layer(x)
        if h0 is None or c0 is None:
            out, (hf, cf) = self.lstm(x)
        else:
            out, (hf, cf) = self.lstm(x, (h0, c0))
        out = self.linear(out)
        return out, (hf, cf)