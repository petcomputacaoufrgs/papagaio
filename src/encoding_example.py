import os
import pandas as pd

from MidiExpress import read, write

data_path = '../datasets/midi/test/lpd_midi/'
out_encoded_path = '../encoded/'
out_decoded_path = '../decoded/'
file = '(When You Say You Love Somebody) In The Heart.mid'
in_file = data_path + file
out_encoded = out_encoded_path + file
out_decoded = out_decoded_path + file

SETTINGS = {
  'RESOLUTION': 36,
  'KEYBOARD_SIZE': 88,
  'KEYBOARD_OFFSET': 20
}

# be sure that the dirs exist
if not os.path.isdir(data_path):
    os.mkdir(data_path)
if not os.path.isdir(out_decoded_path):
    os.mkdir(out_decoded_path)
if not os.path.isdir(out_encoded_path):
    os.mkdir(out_encoded_path)
# os.makedirs(out_decoded, )

# get encoded data and save encoded file
interpreted_song = read.file(in_file,
                             SETTINGS,
                             save_as=out_encoded
                            )

# open a encoded file
# encoded_song = pd.read_pickle(out_encoded + '.pkl')
# print(interpreted_song)

# decode
reverted_song = write.file(interpreted_song,
                           SETTINGS,
                           save_as=out_decoded)

# data_out.show()
