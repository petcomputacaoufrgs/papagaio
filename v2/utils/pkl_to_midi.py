import EPMS
from EPMS.serialization import SETTINGS
import glob
import os
import pandas as pd

path_midis = "musicnet_midis_desserialized"
path_pkl = "musicnet_pkl"
pkl_list = glob.glob(path_pkl + "/*.pkl", recursive=True)

success = 0
for i, pkl in enumerate(pkl_list):
    song_name = os.path.basename(pkl).removesuffix(".pkl")
    print(f"{song_name} - [{i+1}/{len(pkl_list)}] - Successful: {success}")
    try:
        out_deserialized_name = path_midis + "/" + song_name + ".mid"
        score = pd.read_pickle(pkl)
        serialized = EPMS.deserialization.file(score, SETTINGS, save_as=out_deserialized_name)
        success += 1
    except Exception as e:
        print(str(e))

