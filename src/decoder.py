from pathlib import Path
import logging
import os
import time
import numpy as np
from tqdm import tqdm
import pandas as pd
from music21 import *


# discover if a list is a continuous sequence
def is_continuous(list):
    # if list is empty or len is 1,  return True
    if len(list) < 2: return True
    return list[-1] - list[0] == len(list) - 1


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


# TODO: ligadura, conectar duas measures e somar as durações
def decode_measure(measure, n_measure, n_frames, curr_info, save_as=None):
    # print(measure.to_string())
    # input()

    decodedMeasure = stream.Measure(number=n_measure)

    #
    #   INFO DECODING
    #

    # get info about the first frame
    # and considering it as the
    # 'Main' info of the song
    measure_ks = measure.ks.mode()[0]
    measure_bpm = measure.bpm.mode()[0]
    measure_ts = measure.ts.mode()[0]

    # now that we have a copy of the info table,
    # lets detach it just for simplification
    measure = measure.drop(['ks', 'bpm', 'ts'], axis=1)

    ks = key.Key(measure_ks)
    transpose_int = get_transpose_interval(ks)

    # check for ks change
    if measure_ks != curr_info['ks']:
        # set key and record the transposition int
        curr_info[0] = measure_ks
        decodedMeasure.append(ks)

    # check for bpm change
    if measure_bpm != curr_info['bpm']:
        # set bpm
        curr_info[1] = measure_bpm
        decodedMeasure.append(tempo.MetronomeMark(number=measure_bpm,
                                           referent='quarter'))

    ts = meter.TimeSignature(measure_ts)
    # check for ts change
    if measure_ts != curr_info['ts']:
        # set ts
        curr_info[2] = measure_ts
        decodedMeasure.append(ts)

    # calculate amount of frames per beat
    frames_per_beat = n_frames // ts.numerator

    #
    #   DATA DECODING
    #

    # decode the measure data, note by note
    for measure_note in measure.columns:
        # filter the frames where the current note is on
        on_frames = measure.loc[measure.loc[:, measure_note] == True, measure_note]

        if not on_frames.empty:

            # get the list of on frames
            frames = [int(f) for f in on_frames.index]

            # print(frames)
            # print(is_continuous(frames))
            # input()

            # if 'frames' is a continuous sequence it can become a single note.
            # if not, it'll become more than one
            while not is_continuous(frames):
                # this will keep track of the frames we
                # have already counted
                temp = []
                while is_continuous(temp):
                    # temp is continuous, we'll try to add
                    # the next frame
                    temp.append(frames[0])

                    if is_continuous(temp):
                        # it temp is still continuous, it's safe to
                        # remove the frame added in the last line
                        # from the original 'frames' list
                        del frames[0]
                    else:
                        # if temp is now no more
                        # a continuous sequence, we must
                        # remove from 'temp' the frame that
                        # caused this property loss
                        del temp[-1]
                        break

                # print(temp)
                # input()
                # calculate duration in frames (amount of frames on)
                n_obj = note.Note(nameWithOctave=measure_note)
                beat_dur = len(temp) / frames_per_beat
                n_obj.duration.quarterLength = beat_dur

                # get the start frame of the note
                frames_offset = (temp[0] % n_frames) - 1
                beat_offset = frames_offset / frames_per_beat

                # insert into stream
                decodedMeasure.insert(beat_offset, n_obj)

            #
            #  here list of frames is a continuous sequence
            #

            # calculate duration in quarters
            note_obj = note.Note(nameWithOctave=measure_note)
            beat_dur = len(frames) / frames_per_beat
            note_obj.duration.quarterLength = beat_dur

            # get the start frame of the note
            frames_offset = (frames[0] % n_frames) - 1
            beat_offset = frames_offset / frames_per_beat

            # insert into measure
            decodedMeasure.insert(beat_offset, note_obj)

    # transpose it back to the original ks
    decodedMeasure.transpose(transpose_int, inPlace=True)

    # insert rests in between the notes
    decodedMeasure.makeRests(fillGaps=True, inPlace=True, hideRests=True)

    # make offsets and durations more strict
    # NOTE: it can remove the 'humanity' of the dynamics
    # decodedMeasure.quantize(inPlace=True)

    # decoded.show('text')
    # input()

    # return it
    return decodedMeasure


# decode a PARTxN_NOTESxN_FRAMES array
def decode_part(part, instrument_name, instrument_midi_code, n_frames, save_as=None):
    # print(part.to_string())
    # input()

    # M21 object to be returned
    decodedPart = stream.Part()

    # replace index:
    #
    # Instrument Name -> Frame Number in Part
    part = part.reset_index()
    part.index += 1
    part = part.drop('inst', axis=1)
    # print(part)
    # input()

    # set instrument
    try:
        inst = instrument.instrumentFromMidiProgram(instrument_midi_code)
    except:
        inst = instrument.fromString(instrument_name)

    # the following midi codes generate errors
    # when M21 tries to create the .mid file
    #
    # 52 (Voice)
    # 26 (Steel Electric Guitar)
    # 29 (Muted Electric Guitar)
    # 73 (Piccolo)
    # if inst.midiProgram in [52, 73]:
    #     inst = instrument.Flute()
    # elif inst.midiProgram in [26, 29]:
    #     inst = instrument.ElectricGuitar()

    decodedPart.append(inst)
    part = part.drop('inst_code', axis=1)

    # total number of measures (bars)
    # in this part
    n_measures = len(part.index) // n_frames
    # print('n_measures: ', n_measures)
    # input()

    # here we will create a pd Series
    # containing the current decoder info
    # about the part
    curr_ks = None
    curr_bpm = None
    curr_ts = None

    # these are the notes that are kept playing since last measure
    # (notes that start in on measure and ends in another)
    curr_on_notes = []
    curr_info = pd.Series([curr_ks, curr_bpm, curr_ts],
                          index=['ks', 'bpm', 'ts'])
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

        # send measure to decoding
        measure = decode_measure(measure,
                                 measure_i,
                                 n_frames,
                                 curr_info)
        decodedPart.append(measure)

    decodedPart.makeTies(inPlace=True)
    decodedPart.makeNotation(inPlace=True)

    if save_as is not None:
        decodedPart.write('midi', fp=save_as)

    return decodedPart


#
#
#  Multi Hot Encoding (Pandas DataFrame) -> MIDI
def decode_data(encoded_song, n_frames, save_as=None):
    if save_as is not None:
        filename = Path(save_as).stem.replace(' ', '_').replace('/', '')

    decodedScore = stream.Score()

    # meta = encoded_data.metadata

    # get a list of unique instruments in the song
    instruments_list = list(set(encoded_song.index))
    instruments = [encoded_song.loc[i] for i in instruments_list]
    # print(instruments)

    # separate song parts by instrument
    for instrument in instruments:
        instrument_name = instrument.index[0]
        instrument_midi_code = instrument.inst_code[0]

        print('Decoding instrument: {}'.format(instrument_name))
        timer = time.time()

        part = decode_part(instrument,
                           instrument_name,
                           instrument_midi_code,
                           n_frames)

        # insert the part at the beginning of the file
        decodedScore.insert(0, part)

    decodedScore.makeNotation(inPlace=True)

    # decoded.show('text')

    # save .mid
    if save_as is not None:
        # try:
        #     mf = midi.translate.streamToMidiFile(decoded)
        #     mf.open(save_as + '.mid', 'wb')
        #     mf.write()
        # except:
        #     logging.warning('Could not save MIDI file.')
        #     pass

        mf = midi.translate.streamToMidiFile(decodedScore)
        mf.open(save_as + '.mid', 'wb')
        mf.write()

    print('Took {}'.format(time.time() - timer))
    return decodedScore
