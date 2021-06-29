from encoder import *
from decoder import *

in_path = '../data/Riders_on_the_Storm.2.mid'
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
#                            MIDI_OFFSET,
#                            save_at=out_encoded_path
#                            )


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
encoded_song = encode_data(in_path,
                           N_FRAMES,
                           N_NOTES,
                           MIDI_OFFSET
                           )

song_metadadata = encoded_song.metadata
song_data = encoded_song.data

print('Available Instruments\n', song_data.index)
on = False
while not on:
    choose = input('Choose instrument:\n ')
    if choose not in song_data.index:
        print('Not in list.')
    else: on = True
instrument = song_data.loc[choose]
print(choose, instrument)
input()

instrument_header = instrument['header']
instrument_measures = instrument['measures']
instrument_measure_twelve = instrument_measures.loc[12]
instrument_stackframe_twelve = instrument_measure_twelve['stackframe']
print('instrument_header:\n', instrument_header)
input()
print('instrument_measures:\n', instrument_measures)
input()
print('instrument_measure_12\n:', instrument_measure_twelve)
print('instrument_stackframe_12\n:', instrument_stackframe_twelve)
# input()







# decode
# data_out = decode_data(data_in,
#                        N_FRAMES,
#                        N_NOTES,
#                        MIDI_OFFSET,
#                        save_as=out_decoded_path)
