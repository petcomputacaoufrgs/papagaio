from pathlib import Path
import logging
import os
import time
import numpy as np
from tqdm import tqdm
import pandas as pd
import music21


# discover if a list is a continuous sequence
def is_continuous(list):
    # if list is empty or len is 1,  return True
    if len(list) < 2: return True
    return list[-1] - list[0] == len(list) - 1


# Key index in our keyboard -> M21 Note
def key_index2note(i, midi_offset):
    index = i + midi_offset
    n = music21.note.Note(midi=index)
    return n


def get_transpose_interval(ks):
    if ks is None:
        return None

    if ks != 'C' and ks != 'a':
        if ks.mode == 'major':
            return music21.interval.Interval(music21.pitch.Pitch('C'), ks.tonic)
        elif ks.mode == 'minor':
            return music21.interval.Interval(music21.pitch.Pitch('a'), ks.tonic)


#   Deserialise a single measure
#
#   Multi Hot Encoding (Pandas DataFrame) -> M21
#
# TODO: ligadura, conectar duas measures e somar as durações
def measure(m_environment, m_performance, SETTINGS, measure_index):
    if not isinstance(SETTINGS, pd.Series):
        SETTINGS = pd.Series(SETTINGS)

    deserialised_measure = music21.stream.Measure(number=measure_index)

    #
    #   INFO DESERIALISATION
    #

    # get info about the first frame
    # and considering it as the
    # 'Main' info of the song
    measure_ks = m_environment.KS.mode()[0]
    measure_ts = m_environment.TS.mode()[0]
    measure_bpm = m_environment.TEMPO.mode()[0]

    ks = music21.key.Key(measure_ks)
    # check for ks change
    transpose_int = get_transpose_interval(ks)
    deserialised_measure.append(ks)

    deserialised_measure.append(music21.tempo.MetronomeMark(number=measure_bpm,
                                                            referent='quarter'))
    ts = music21.meter.TimeSignature(measure_ts)
    deserialised_measure.append(ts)

    # calculate amount of frames per beat
    frames_per_beat = SETTINGS.RESOLUTION // ts.numerator

    #
    #   DATA DECODING
    #

    # decode the measure data, note by note
    for measure_note in m_performance.columns:
        # filter the frames where the current note is on
        on_frames = m_performance.loc[m_performance.loc[:, measure_note] == True, measure_note]
        on_frames = on_frames.reset_index()

        if not on_frames.empty:

            # get the list of on frames
            frames = [int(f) for f in on_frames.index]

            # print(frames)
            # input()

            # if 'frames' is a continuous sequence it can become a single note.
            # if not, it'll become more than one
            temp = []
            while not is_continuous(frames):
                # this will keep track of the frames we
                # have already counted
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

                # calculate duration in frames (amount of frames on)
                n_obj = music21.note.Note(nameWithOctave=measure_note)
                beat_dur = len(temp) / frames_per_beat  # amount of beats
                n_obj.duration.quarterLength = abs(beat_dur)

                # get the start frame of the note
                beat_offset = (frames[0] + 1) % ts.numerator

                # insert into stream
                deserialised_measure.insert(beat_offset, n_obj)

            #
            #  here list of frames is a continuous sequence
            #

            # calculate duration in quarters
            note_obj = music21.note.Note(nameWithOctave=measure_note)
            beat_dur = len(frames) / frames_per_beat
            note_obj.duration.quarterLength = abs(beat_dur)

            # get the start frame of the note
            beat_offset = (frames[0] + 1) % ts.numerator

            # insert into measure
            deserialised_measure.insert(beat_offset, note_obj)

    # transpose it back to the original ks
    deserialised_measure.transpose(transpose_int, inPlace=True)

    # insert rests in between the notes
    deserialised_measure.makeRests(fillGaps=False, inPlace=True)

    # make offsets and durations more strict
    # NOTE: it can remove the 'humanity' of the dynamics
    # deserialised_measure.quantize(inPlace=True)

    # return it
    return deserialised_measure


# deserialise a PARTxN_NOTESxN_FRAMES array
def instrument(SETTINGS, INSTRUMENT_BLOCK, ENVIRONMENT_BLOCK, PERFORMANCE_BLOCK, save_as=None):
    if not isinstance(SETTINGS, pd.Series):
        SETTINGS = pd.Series(SETTINGS)

    # M21 object to be returned
    deserialised_part = music21.stream.Part()

    # set instrument
    try:
        inst = music21.instrument.instrumentFromMidiProgram(INSTRUMENT_BLOCK.MIDI_CODE[0])
    except:
        inst = music21.instrument.fromString(INSTRUMENT_BLOCK.INSTRUMENT[0])

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

    inst.autoAssignMidiChannel()
    deserialised_part.insert(0, inst)

    # total number of measures (bars)
    # in this part
    n_measures = len(PERFORMANCE_BLOCK.index) // SETTINGS.RESOLUTION

    # deserialise measures
    #
    # iterate over measures (bars)
    for measure_index in range(1, n_measures + 1):
        # calculate first and last frame indexes
        s_frame = (measure_index - 1) * SETTINGS.RESOLUTION
        e_frame = (measure_index * SETTINGS.RESOLUTION) - 1

        measure_environment = ENVIRONMENT_BLOCK.iloc[np.arange(s_frame, e_frame)]
        measure_performance = PERFORMANCE_BLOCK.iloc[np.arange(s_frame, e_frame)]

        # send measure to deserialisation
        midi_measure = measure(measure_environment,
                               measure_performance,
                               SETTINGS,
                               measure_index)

        ts_numerator = int(measure_environment.TS[0][0])
        deserialised_part.insert(measure_index * ts_numerator
                                 , midi_measure)

    deserialised_part.makeNotation(inPlace=True)

    if save_as is not None:
        deserialised_part.write('midi', fp=save_as)

    return deserialised_part


# Deserialise a whole file
#
#  Multi Hot Encoding (Pandas DataFrame) -> MIDI
def file(serialised, SETTINGS, save_as=None):
    if not isinstance(SETTINGS, pd.Series):
        SETTINGS = pd.Series(SETTINGS)

    deserialised_score = music21.stream.Score()

    # meta = serialised.metadata

    # get a list of unique instruments in the song
    instruments_list = list(set(serialised.index))
    instruments = [serialised.loc[i] for i in instruments_list]
    # print(instruments)
    # input()

    # separate song parts by instrument
    for inst_interpretation in instruments:
        INSTRUMENT_BLOCK = pd.DataFrame(
            {
                'INSTRUMENT': inst_interpretation.index,
                'MIDI_CODE': inst_interpretation.MIDI_CODE
            }
        )

        ENVIRONMENT_BLOCK = pd.DataFrame(
            {
                'KS': inst_interpretation.KS,
                'TS': inst_interpretation.TS,
                'TEMPO': inst_interpretation.TEMPO,
            }
        )

        inst_drop_list = [i for i in set(INSTRUMENT_BLOCK.columns)]
        inst_drop_list.remove('INSTRUMENT')
        PERFORMANCE_BLOCK = inst_interpretation.drop(columns=inst_drop_list)

        env_drop_list = [i for i in set(ENVIRONMENT_BLOCK.columns)]
        PERFORMANCE_BLOCK = PERFORMANCE_BLOCK.drop(columns=env_drop_list)

        # print('Decoding instrument: {}'.format(INSTRUMENT_BLOCK.NAME))

        part = instrument(SETTINGS,
                          INSTRUMENT_BLOCK,
                          ENVIRONMENT_BLOCK,
                          PERFORMANCE_BLOCK
                          )

        # insert the part at the beginning of the file
        deserialised_score.insert(0, part)
        deserialised_score.makeVoices(inPlace=True)
        # deserialised_score.makeNotation(inPlace=True)

    # decoded.show('text')

    # save .mid
    if save_as is not None:
        deserialised_score.write("midi", save_as)

    return deserialised_score
