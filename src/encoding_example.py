import pandas as pd

from encoder import *
from decoder import *

in_path = '../data/Amazing.mid'
out_encoded_file = '../encoded/Amazing.csv'
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
encoded_data = encode_data(in_path,
                           N_FRAMES,
                           N_NOTES,
                           MIDI_OFFSET
                           ,save_at=out_encoded_file
                           )


# get encoded data and save encoded file
# and a folder with all its measures and stackframes
# encoded_data = encode_data(in_path,
#                            N_FRAMES,
#                            N_NOTES,
#                            MIDI_OFFSET,
#                            save_at=out_encoded_path,
#                            save_folder=True
#                            )


# get encoded data without saving a file
# encoded_song = encode_data(in_path,
#                            N_FRAMES,
#                            N_NOTES,
#                            MIDI_OFFSET
#                            )
# print(type(encoded_song))
# encoded_song.to_csv(out_encoded_path + encoded_song.name + '.csv')

# song_metadadata = encoded_song.metadata
# song_data = encoded_song.data

# print('Available Instruments\n', song_data.index)
# on = False
# while not on:
#     choose = input('Choose instrument:\n')
#     choose = choose.capitalize()
#     if choose not in song_data.index:
#         print('Not in list, try again.')
#     else: on = True

# instrument = song_data.loc[choose]
# print(instrument)

# instrument_header = instrument.header
# instrument_measures = instrument.measures
# print(instrument_header)
# print(instrument_measures)
# input()

# print first stackframes
# print(instrument_measures.stackframe.head())
# input()


# instrument_measure_five = instrument_measures.loc[5]
# instrument_stackframe_five = instrument_measure_five['stackframe']

# print(instrument_measure_five, instrument_stackframe_five.to_string())
# input()


# open a encoded file
# encoded_song = pd.read_csv(out_encoded_file)
#
# data = encoded_song.iloc[1]
# # print(type(encoded_song))
# print(data)
# print(data[0, :])
# input()

# decode
data_out = decode_data(encoded_data,
                       save_decoded_at=out_decoded_path)
