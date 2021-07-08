import pandas as pd

from encoder import *
from decoder import *

data_path = '../data/'
out_encoded_path = '../encoded/'
out_decoded_path = '../decoded/'
file = 'Dont_Stop_Me_Now.1'
in_file = data_path + file
out_encoded = out_encoded_path + file
out_decoded = out_decoded_path + file

N_FRAMES = 36
N_NOTES = 88
MIDI_OFFSET = 20

# be sure that the dirs exist
if not os.path.isdir(data_path):
    os.mkdir(data_path)
if not os.path.isdir(out_decoded_path):
    os.mkdir(out_decoded_path)
if not os.path.isdir(out_encoded_path):
    os.mkdir(out_encoded_path)

# get encoded data and save encoded file
encoded_song = encode_data(in_file,
                           N_FRAMES,
                           N_NOTES,
                           MIDI_OFFSET
                           , save_as=out_encoded
                           )

# just save the encoded data file in disk
# encode_data(in_path,
#             N_FRAMES,
#             N_NOTES,
#             MIDI_OFFSET
#             , save_as=out_encoded_path
#             )

# open a encoded file
# encoded_song = pd.read_pickle(out_encoded + '.pkl')

# check out the data
# print(encoded_song)
# input()

# list of instruments in this song
# instruments = list(set(encoded_song.index))
# print(instruments)
# input()

# iterate over the instruments and print them
# for instrument in instruments:
#     print(encoded_song.loc[instrument])
#     input('Next instrument -> [Press Enter]')

# decode
data_out = decode_data(encoded_song,
                       N_FRAMES,
                       N_NOTES,
                       save_as=out_decoded)
