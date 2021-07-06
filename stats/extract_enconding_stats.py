import pandas as pd
import numpy as np
import glob
import sys
from os.path import getsize

sys.path.append('../src/')
from encoder import *

N_FRAMES = 36
N_NOTES = 88
MIDI_OFFSET = 20

data_path = 'data/'
encoded_data_path = 'encoded_data/'

times = []
midi_sizes = []
pkl_sizes = []
# data inflation rate
i_rates = []

# be sure that the dirs exist
if not os.path.isdir(encoded_data_path):
    os.mkdir(encoded_data_path)

for file in glob.glob(data_path + '*.mid'):
    midi_size = getsize(file)
    midi_sizes.append(midi_size)

    timer = time.time()

    encode_data(file,
                N_FRAMES,
                N_NOTES,
                MIDI_OFFSET
                , save_at=encoded_data_path)

    duration = time.time() - timer

    times.append(duration)

for e_file in glob.glob(encoded_data_path + '*.pkl'):
    pkl_size = getsize(e_file)
    pkl_sizes.append(pkl_size)

i_rates = np.divide(pkl_sizes, midi_sizes)

raw_stats = np.array([times, midi_sizes, pkl_sizes, i_rates])
stats = pd.DataFrame(raw_stats.T, columns=['Encode time (seconds)',
            'Original size (bytes)',
            'Encoded size (bytes)',
            'Data Inflation Rate (i)']
)
# stats = stats.transpose()

print(stats)
stats.to_csv('results.csv')
