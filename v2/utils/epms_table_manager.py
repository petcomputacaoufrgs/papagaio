import pandas as pd
from EPMS.serialization import SETTINGS

INFO_SIZE = 9

def get_df_notes(df):
    notes = df.iloc[:, INFO_SIZE:]
    return notes


def get_df_slice(df, instrument, first_frame, last_frame):
    df_instrument = df[df.INSTRUMENT == instrument]
    df_slice = df_instrument.iloc[first_frame:last_frame]
    return df_slice


def fill_table_info(df, num_frames):
    last_df_row = df.iloc[-1, :]

    measure = last_df_row.MEASURE
    beat = last_df_row.BEAT
    frame = last_df_row.FRAME

    split_ts = last_df_row.TS.split("/")
    beats_in_bar = int(split_ts[1])
    rows = []

    for i in range(num_frames):
        frame = frame % SETTINGS["RESOLUTION"] + 1
        if frame == 1:
            beat = beat % beats_in_bar + 1
            if beat == 1:
                measure += 1

        row = [last_df_row.INSTRUMENT,
               last_df_row.MIDI_PROGRAM,
               last_df_row.SOUND,
               measure,
               beat,
               frame,
               last_df_row.ORIGINAL_KS,
               last_df_row.TS,
               last_df_row.TEMPO]

        rows.append(row)

    info_index = [df.index[-1]] * num_frames
    info_columns = df.columns[:INFO_SIZE]
    filled_info = pd.DataFrame(rows, index=info_index, columns=info_columns)
    return filled_info


def append_notes_df(df:pd.DataFrame, notes_to_append):
    notes_size = len(notes_to_append)
    notes_index = [df.index[-1]] * notes_size
    notes_pd = pd.DataFrame(notes_to_append, index=notes_index, columns=df.columns[INFO_SIZE:])
    info_pd = fill_table_info(df, len(notes_pd))
    df_to_append = pd.concat([info_pd, notes_pd], axis=1)
    updated_df = pd.concat([df, df_to_append], axis=0)
    return updated_df


if __name__ == "__main__":
    pkl_path = "../samples/pkls/chpn-p15.pkl"
    epms_table = pd.read_pickle(pkl_path)
    table_slice = get_df_slice(epms_table, "Piano", len(epms_table)-100, len(epms_table))
    notes = get_df_notes(table_slice)
    notes_np = notes.astype("float").to_numpy()
    updated_df = append_notes_df(epms_table, notes_np)

