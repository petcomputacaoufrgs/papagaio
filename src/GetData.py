import os
import sys
import numpy as np
import pandas as pd
from encoder import *
from decoder import *
import glob
from tqdm import tqdm
import matplotlib.pyplot as plt
from scipy import interpolate

in_path = '../data/No_Excuses.mid'
out_encoded_path = '../encoded/'
out_decoded_path = '../decoded/'
N_FRAMES = 36
N_NOTES = 88
MIDI_OFFSET = 20

# be sure that the dirs exist
if not os.path.isdir(out_decoded_path):
    os.mkdir(out_decoded_path)
if not os.path.isdir(out_encoded_path):
    os.mkdir(out_encoded_path)

# get encoded file parts with N_FRAMES frames per measure (bar)
data_in = encode_file(in_path,
                      N_FRAMES,
                      N_NOTES,
                      MIDI_OFFSET,
                      save_encoded_at=out_encoded_path)

# decode
# data_out = decode_data(data_in,
#                        N_FRAMES,
#                        N_NOTES,
#                        MIDI_OFFSET,
#                        save_as=out_decoded_path)

# for i, part in enumerate(data_in):
#     # print(part.shape)
#     print('Part #{}'.format(i + 1))
#     decode_part(part, N_FRAMES)
