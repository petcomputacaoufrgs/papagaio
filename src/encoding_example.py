import pandas as pd

from encoder import *
from decoder import *

in_path = '../data/Amazing.mid'
out_encoded_file = '../encoded/Amazing.pkl'
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

# get encoded data and save encoded file
# encoded_data = encode_data(in_path,
#                            N_FRAMES,
#                            N_NOTES,
#                            MIDI_OFFSET
#                            ,save_at=out_encoded_path
#                            )

# just save the encoded data file in disk
encode_data(in_path,
            N_FRAMES,
            N_NOTES,
            MIDI_OFFSET
            , save_at=out_encoded_path
            )

# open a encoded file
encoded_song = pd.read_pickle(out_encoded_file)

# check out the data
print(encoded_song.to_string())
input()

# list of instruments in this song
instruments = list(set(encoded_song.index))
print(instruments)

# iterate over the instruments and print them
for instrument in instruments:
    print(encoded_song.loc[instrument])
    input('Next instrument -> [Press Enter]')

# decode
# data_out = decode_data(encoded_data,
#                        save_decoded_at=out_decoded_path)
