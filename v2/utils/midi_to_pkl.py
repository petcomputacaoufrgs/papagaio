import EPMS
import sys
import os
from EPMS.serialization import SETTINGS
import pickle

path_root = "datasets/classical/" # caminho
path_midis = path_root + "classical_midis/" # pasta em que estão os midis
path_save = path_root + "classical_pkl/" # pasta em que os pkls ficarão salvos
list_pickle = path_root + "list_classical" # arquivo pickle que vai conter a lista

with open(list_pickle, "rb") as f:
    midi_list = pickle.load(f)

# arquivos que serão serializados
first = 0 # posição inicial
last = 100 # posição final
success = 0

for i in range(first, last):
    midi = midi_list[i]
    song_name = os.path.basename(midi).removesuffix(".mid")
    print(f"{song_name} - [{i+1}/{len(midi_list)}] - Successful: {success}")
    try:
        out_serialized_name = path_save + song_name + ".pkl"
        serialized = EPMS.serialization.file(midi, SETTINGS, save_as=out_serialized_name)
        success += 1
    except KeyboardInterrupt:
        print('Interrupted')
        last = i
        del midi_list[first:last]
        with open(list_pickle, "wb") as f:
            pickle.dump(midi_list, f)
        sys.exit(0)
    except Exception as e:
        print(str(e))

del midi_list[first:last]
with open(list_pickle, "wb") as f:
    pickle.dump(midi_list, f)
