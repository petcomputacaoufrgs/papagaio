from pathlib import Path
import os
import numpy as np
from tqdm import tqdm
import pandas as pd
from music21 import *


# Key index in our keyboard -> M21 Note
def key_index2note(i, midi_offset):
    index = i + midi_offset
    n = note.Note(midi=index)
    return n


def get_transpose_interval(ks):
    if ks is None:
        return None

    if ks != 'C' and ks != 'a':
        if ks.mode == 'major':
            return interval.Interval(pitch.Pitch('C'), ks.tonic)
        elif ks.mode == 'minor':
            return interval.Interval(pitch.Pitch('a'), ks.tonic)


# MultiHotEncoding -> M21 Notes
def decode_stackframe(stackframe):
    notes = []


# decode a N_NOTESxN_FRAMES array and turn it into a m21 Measure
def decode_stackframe(stackframe, n_frames, ts):
    last_frame = False

    # the stream that will receive the notes
    output = stream.Measure()

    # vectors that will hold the current notes states and durations
    # they are initialized with the values of the first frame
    state_register = stackframe[:][0].copy().to_numpy()
    start_register = stackframe[:][0].copy().to_numpy() - 1
    duration_register = stackframe[:][0].copy().to_numpy()

    # iterate over frames
    for f in range(n_frames):
        # print('Frame ', f)
        # with np.printoptions(threshold=np.inf):
        #     print('\nStates:\t', state_register.reshape(1, 88))
        #     print('\nStarts:\t', start_register.reshape(1, 88))
        #     print('\nDurs:\t', duration_register.reshape(1, 88))
        # input()

        frames_per_beat = n_frames / ts.numerator

        frame = stackframe[f]

        if f == n_frames - 1:
            last_frame = True

        # print("Frame {}\n".format(f), frame)
        # input()

        # iterate over notes
        # state is ON/OFF 1/0
        for note_index, state in enumerate(frame):

            # if note state changed
            if bool(state) != bool(state_register[note_index]):

                # 1 -> *0*
                if bool(state) is False:

                    nt = key_index2note(note_index)
                    nt.duration.quarterLength = duration_register[note_index] / frames_per_beat

                    note_offset = start_register[note_index] / frames_per_beat
                    output.insert(note_offset, nt)

                    # print('Note {} turned off at frame {}\n'.format(int2note(note_index).nameWithOctave, f + 1) +
                    #       'offset of {} frames ({})\n'.format(start_register[note_index], note_offset) +
                    #       'and duration on {} frames ({})'.format(duration_register[note_index],
                    #                                               nt.duration.quarterLength))
                    # input()

                    # restarting the registers
                    duration_register[note_index] = 0
                    state_register[note_index] = 0
                    start_register[note_index] = -1


                # 0 -> *1*
                else:
                    # starting registers
                    duration_register[note_index] = 1
                    state_register[note_index] = 1
                    start_register[note_index] = f

                    # print('Note {} turned on at frame {}'.format(int2note(note_index).nameWithOctave, f + 1))
                    # input()

            # if note is on and didnt change, increase duration
            elif bool(state) is True:
                duration_register[note_index] += 1

                # print('Note {} increased duration at frame {} ({} frames)'.
                #       format(int2note(note_index).nameWithOctave, f + 1, duration_register[note_index]))
                # input()

            # note is ON and measure ended
            elif bool(state_register[note_index]) and last_frame:

                nt = key_index2note(note_index)
                note.duration.quarterLength = duration_register[note_index] / frames_per_beat

                note_offset = start_register[note_index] / frames_per_beat
                output.insert(note_offset, nt)
                # print('Note {} turned off at frame {}\n'.format(int2note(note_index).nameWithOctave, f + 1) +
                #       'offset of {} frames ({})\n'.format(start_register[note_index], note_offset) +
                #       'and duration on {} frames ({})'.format(duration_register[note_index], nt.duration.quarterLength))
                # input()

    # make offsets and durations more strict
    # NOTE: it can remove the 'humanity' of the dynamics
    output.quantize(inPlace=True)

    return output


def decode_measure(measure, n_notes, n_frames, save_at=None):
    decoded = stream.Measure()

    # get info about the first frame
    # and considering it as the
    # 'Main' info of the song
    measure_ks = measure.ks.mode()[0]
    measure_bpm = measure.bpm.mode()[0]
    measure_ts = measure.ts.mode()[0]

    measure = measure.drop(['ks', 'bpm', 'ts'], axis=1)

    # set key and record the tranposition int
    ks = key.Key(measure_ks)
    transpose_int = get_transpose_interval(ks)
    decoded.append(ks)

    # set bpm
    decoded.append(tempo.MetronomeMark(number=measure_bpm,
                                       referent='quarter'))

    # set ts
    decoded.append(meter.TimeSignature(measure_ts))

    # decode the measure data, note by note
    for note in measure.columns:
        # filter the frames where the current note is on
        on_frames = measure.loc[measure.loc[:, note] == True, note]
        if not on_frames.empty:
            print(on_frames)
            input()

    # transpose it back to the original ks
    decoded.transpose(transpose_int, inPlace=True)

    # make offsets and durations more strict
    # NOTE: it can remove the 'humanity' of the dynamics
    decoded.quantize(inPlace=True)

    # return it
    return decoded


# decode a PARTxN_NOTESxN_FRAMES array
def decode_part(part, instrument_name, instrument_midi_code, n_frames, n_notes, save_at=None):
    # M21 object to be returned
    decoded = stream.Part()

    # replace index:
    #
    # Instrument Name -> Frame Number in Part
    part = part.reset_index()
    part.index += 1
    part = part.drop('inst', axis=1)
    # print(part)
    # input()

    # get info about the first frame
    # and considering it as the
    # 'Main' info of the song
    part_ks = part.at[1, 'ks']
    part_bpm = part.at[1, 'bpm']
    part_ts = part.at[1, 'ts']

    # set instrument
    decoded.append(instrument.instrumentFromMidiProgram(instrument_midi_code))

    # set key and record the tranposition int
    ks = key.Key(part_ks)
    decoded.append(ks)

    transpose_int = get_transpose_interval(ks)

    # set bpm
    decoded.append(tempo.MetronomeMark(number=part_bpm,
                                       referent='quarter'))

    # set ts
    decoded.append(meter.TimeSignature(part_ts))

    # total number of measures (bars)
    # in this part
    n_measures = len(part.index) // n_frames
    # print('n_measures: ', n_measures)
    # input()

    # decode measures
    #
    # iterate over measures (bars)
    for measure_i in range(1, n_measures + 1):
        # calculate first and last frame indexes
        s_frame = (measure_i - 1) * n_frames
        e_frame = measure_i * n_frames

        measure = part.iloc[np.arange(s_frame, e_frame)]
        # print(measure)
        # input()
        decoded.append(decode_measure(measure,
                                      n_notes,
                                      n_frames))

        # send measure to decoding

    decoded.transpose(transpose_int, inPlace=True)
    decoded.makeNotation(inPlace=True)

    if save_at is not None:
        decoded.write('midi', fp=save_at)

    return decoded


#
#
#  Multi Hot Encoding (Pandas DataFrame) -> MIDI
def decode_data(encoded_song, n_frames, n_notes, save_decoded_at=None):
    filename = Path().stem.replace(' ', '_').replace('/', '')

    decoded = stream.Stream()

    if save_decoded_at is not None:
        if not os.path.isdir(save_decoded_at):
            os.mkdir(save_decoded_at)
        save_parts_at = save_decoded_at + filename + '/'
        if not os.path.isdir(save_parts_at):
            os.mkdir(save_parts_at)

    # meta = encoded_data.metadata

    # get a list of unique instruments in the song
    instruments_list = list(set(encoded_song.index))
    instruments = [encoded_song.loc[i] for i in instruments_list]
    print(instruments)

    # separate song parts by instrument
    for instrument in instruments:
        instrument_name = instrument.index[0]
        # print(instrument_name)
        instrument_midi_code = instrument.inst_code[0]
        # print(instrument_midi_code)
        print('Decoding instrument: {}'.format(instrument_name))
        # print(instrument)
        # input()
        decoded.append(decode_part(instrument,
                                   instrument_name,
                                   instrument_midi_code,
                                   n_frames, n_notes))

    decoded.makeNotation(inPlace=True)

    # save .mid
    if save_at is not None:
        decoded.write('midi', fp=save_at + '.mid')

    return decoded
