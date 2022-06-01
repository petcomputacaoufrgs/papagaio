import pandas as pd
from EPMS.serialization import SETTINGS


def split_dataframe(df):
    initial_note = len(df.columns) - SETTINGS["KEYBOARD_SIZE"]
    info = df.iloc[:, :initial_note]
    notes = df.iloc[:, initial_note:]

    return info, notes

