import logging
import os
import time
import pandas as pd
import numpy as np
import music21
from pathlib import Path


# Key index in our keyboard -> M21 Note
def key_index2note(i, midi_offset):
    index = i + midi_offset
    n = music21.note.Note(midi=index)
    return n


# return tuple (key, transposed_stream)
#
# (label, key)
def transposeStreamToC(stream, force_eval=False):
    # trying to capture a M21 Key object in the stream
    stream_key = stream.getElementsByClass(music21.key.Key)
    if len(stream_key) != 0:
        stream_key = stream_key[0]
    else:
        stream_key = None

    # if we failed to get a M21 Key and 'forceEval' is set to True
    # we will try to use M21 key analyzer.
    # but this analyzer sometimes fails and breaks the code
    # so this flag should be used carefully
    if force_eval and stream_key is None:
        stream_key = stream.analyze('key')

    # if the flag jump was not taken, we raise a warn and
    # return the own input.
    # this is, we reject the input
    if stream_key is None:
        # logging.warning('Transposing measures containing empty KeySignatures can cause errors. Returning key as None '
        #                 'type.')
        return None, stream

    # at this point we should have a key
    # so it's safe to compare
    if stream_key != 'C' and stream_key != 'a':
        # transpose song to C major/A minor
        if stream_key.mode == 'major':
            transpose_int = music21.interval. \
                Interval(stream_key.tonic, music21.pitch.Pitch('C'))
            transposed_stream = stream.transpose(transpose_int)
        elif stream_key.mode == 'minor':
            transpose_int = music21.interval. \
                Interval(stream_key.tonic, music21.pitch.Pitch('a'))
            transposed_stream = stream.transpose(transpose_int)

    return stream_key.tonicPitchNameWithCase, transposed_stream


# open and read file
#
# MIDI -> M21 Score
def open_file(midi_path, no_drums=True):
    # declare and read
    mf = music21.midi.MidiFile()
    mf.open(midi_path)

    if mf.format not in [0, 1]:
        # m21 cant read
        logging.warning('Music21 cant open format {} MIDI files. Skipping.'.format(mf.format))
        return None

    mf.read()
    mf.close()

    n_tracks = len(mf.tracks)

    if n_tracks == 1 or n_tracks is None:
        logging.warning('MIDI file has only 1 track, Skipping.'.format(mf.format))
        return None

    # if no_drums is on, we'll remove the drums
    if no_drums:
        for i in range(0, n_tracks):
            mf.tracks[i].events = [ev for ev in mf.tracks[i].events if ev.channel != 10]

    return music21.midi.translate.midiFileToStream(mf)


# get all notes from m21 obj
#
# M21 Stream (Measure) -> Multi Hot Encoding
def measure_data(measure):
    items = measure.flat.notes
    data = []
    for item in items:
        if isinstance(item, music21.note.Note) or isinstance(item, music21.note.Rest):
            data.append(item)
            # print('data', data)
        elif isinstance(item, music21.chord.Chord):
            for p in item.pitches:
                data.append(music21.note.Note(pitch=p))
                # print('data', data)

    return data


# extract frames from measure
#
#  M21 Measure -> Multi Hot Encodinghttps://tenor.com/view/taffarel-futebol-no-score-gif-12585286
def measure2stackframe(measure, SETTINGS, frames_per_beat):
    data = measure_data(measure)

    keyboard_range = SETTINGS.KEYBOARD_SIZE + SETTINGS.KEYBOARD_OFFSET

    frames = [[False for i in range(SETTINGS.KEYBOARD_SIZE)] for j in range(SETTINGS.RESOLUTION)]

    for item in data:

        # print(item)
        # input()

        # if item is a Rest, we can break
        # since no key must be turned on
        if isinstance(item, music21.note.Rest): break

        # if the item is a Note that is above
        # or below our keyboard range, we can break
        # cause it will not be represented
        if item.pitch.midi > keyboard_range: break

        # # # # # # # #
        # ITEM IS VALID
        # # # # # # # #
        #
        # here we only have
        # individual notes
        # that are inside our
        # keyboard range
        #
        # now we must discover
        # what frames must be set
        # not True at what note
        # index to get the
        # One Hot Encoding of
        # the measure

        # start and end frames
        frame_s = int(item.offset * frames_per_beat)
        frame_e = frame_s + int(item.quarterLength * frames_per_beat)

        # note index on our keyboard
        i_key = item.pitch.midi - SETTINGS.KEYBOARD_OFFSET

        # turn them on captain!
        for frame in range(frame_s, frame_e):
            try: frames[frame][i_key] = True
            except: pass

    # create Pandas dataframe
    note_names = [key_index2note(i, SETTINGS.KEYBOARD_OFFSET).nameWithOctave for i in range(0, SETTINGS.KEYBOARD_SIZE)]
    frame_count = [int(i) for i in range(1, SETTINGS.RESOLUTION + 1)]
    stackframe = pd.DataFrame(frames, index=frame_count, columns=note_names)

    return stackframe


# encode a single measure
#
# M21 Measure -> Multi Hot Encoding
def measure(m, SETTINGS, INSTRUMENT_BLOCK, ENVIRONMENT_BLOCK):
    number = m.measureNumber

    # TODO: ligadura, conectar duas measures e somar as durações

    # check for key changes
    m_ks, transposed_measure = transposeStreamToC(m, force_eval=False)
    if m_ks is None:
        m_ks = ENVIRONMENT_BLOCK.KS

    # check for tempo changes
    m_bpm = m.getElementsByClass(music21.tempo.TempoIndication)
    if len(m_bpm) != 0:
        m_bpm = m_bpm[0].getQuarterBPM()
    else:
        m_bpm = ENVIRONMENT_BLOCK.TEMPO

    # check for time sign changes
    m_ts = m.getTimeSignatures()
    if len(m_ts) != 0:
        m_ts = m_ts[0]
        if m_ts != ENVIRONMENT_BLOCK.TS:
            # ts changed
            if m_ts.ratioString != '4/4':
                # logging.warning('Found measure not in 4/4, skipping.')
                # return None
                pass
    else:
        m_ts = ENVIRONMENT_BLOCK.TS

    # Update Env according to this measure
    ENVIRONMENT_BLOCK.KS = m_ks
    ENVIRONMENT_BLOCK.TS = '{}/{}'.format(m_ts.numerator, m_ts.denominator)
    ENVIRONMENT_BLOCK.TEMPO = m_bpm

    # calculate amount of frames per beat
    frames_per_beat = SETTINGS.RESOLUTION // m_ts.numerator
    # pandas stackframe
    stackframe = measure2stackframe(transposed_measure,
                                    SETTINGS,
                                    frames_per_beat)
    # INSTRUMENT_BLOCK = INSTRUMENT_BLOCK.T
    # ENVIRONMENT_BLOCK = ENVIRONMENT_BLOCK.T
    inst_df = pd.concat([INSTRUMENT_BLOCK]*SETTINGS.RESOLUTION, axis=1).T
    # inst_df = inst_df.reshape(len(INSTRUMENT_BLOCK), SETTINGS.RESOLUTION, axis=0)

    env_df = pd.concat([ENVIRONMENT_BLOCK]*SETTINGS.RESOLUTION, axis=1).T
    # env_df = env_df.reshape(len(ENVIRONMENT_BLOCK), SETTINGS.RESOLUTION)

    # print(f'INST DF: \n\n {inst_df.to_string()} \n Shape {inst_df.shape}\n')
    # print(f'ENV DF: \n\n {env_df.to_string()} \n Shape {env_df.shape}\n')
    # print(f'PERFORMANCE DF: \n\n {stackframe.to_string()} \n Shape {stackframe.shape}\n')

    encoded_measure = pd.concat([inst_df, env_df, stackframe], axis=1).drop(0).dropna()

    return encoded_measure


# encode a single part
#
# M21 Part -> Multi Hot Encoding
def instrument(part, SETTINGS, instrument_list=None):

    #
    #   INSTRUMENT BLOCK
    #

    inst_midi_code = part.getElementsByClass(music21.instrument.Instrument)[0].midiProgram
    if inst_midi_code is None:
        inst_midi_code = 0
        logging.warning('Could not retrieve Midi Program from instrument, setting it to default value 0 ({})'
                        .format(music21.instrument.instrumentFromMidiProgram(inst_midi_code).instrumentName))

    inst_name = music21.instrument.instrumentFromMidiProgram(inst_midi_code).instrumentName
    inst_name = inst_name.capitalize().replace('/', '').replace('.', '_')

    # if instrument name already in the list,
    # change its name by counting repetitions
    if inst_name in instrument_list:
        counter = 2
        while inst_name + f' [{counter}]' in instrument_list:
            counter += 1
        inst_name += f' [{counter}]'

    instrument_list.append(inst_name)

    INSTRUMENT_BLOCK = pd.Series(
        {
            'INSTRUMENT': inst_name,
            'MIDI_CODE': inst_midi_code
        }
    )

    # print(f'INSTRUMENT BLOCK: \n\n {INSTRUMENT_BLOCK} \n\n')

    #
    #   ENVIRONMENT BLOCK
    #

    # flat the stream
    # part = part.implode()
    # part. = part.voicesToParts()
    # part = part.semiFlat

    # get part tempo
    metronome = part.getElementsByClass(music21.tempo.TempoIndication)
    if len(metronome) == 0:
        bpm = 120
        logging.warning('Could not retrieve Metronome object from Part, setting BPM to default value ({})'
                        .format(bpm))
    else:
        bpm = metronome[0].getQuarterBPM()

    # filter parts that are not in 4/4
    time_signature = part.getElementsByClass(music21.meter.TimeSignature)
    if len(time_signature) == 0:
        ts = music21.meter.TimeSignature('4/4')
        logging.warning('Could not retrieve Time Signature object from Part, setting TS to default value ({})'
                        .format(ts))
    else:
        ts = time_signature[0]

    # transpose song to C major/A minor
    # original_ks, part = transposeStreamToC(part, force_eval=False)
    original_ks, transposed_part = transposeStreamToC(part, force_eval=True)

    n_measures = len(part) + 1

    ENVIRONMENT_BLOCK = pd.Series(
        {
            'KS': original_ks,
            'TS': '{}/{}'.format(ts.numerator, ts.denominator),
            'TEMPO': bpm
        }
    )

    # print(f'ENVIRONMENT BLOCK: \n\n {ENVIRONMENT_BLOCK} \n\n')

    # a vector containing the measures
    first_measure = True
    for m in transposed_part.measures(1, n_measures):

        e_measure = pd.DataFrame(
            measure(m,
                    SETTINGS,
                    INSTRUMENT_BLOCK,
                    ENVIRONMENT_BLOCK
                    )
        )

        if first_measure:
            part_df = pd.DataFrame(e_measure)
            first_measure = False
        else:
            part_df = pd.concat([part_df, e_measure], axis=0, ignore_index=True)

        part_df.index = part_df.index + 1

    return part_df


# encode the file data from a .mid file
#
# MIDI -> Interpretation (Pandas DataFrame)

# SETTINGS = {
#   'RESOLUTION': 36,
#   'KEYBOARD_SIZE': 88,
#   'KEYBOARD_OFFSET': 20
# }

def file(path, SETTINGS, save_as=None):

    # print(f'SETTINGS: \n\n {SETTINGS} \n\n')

    score = open_file(path)
    if not score:
        # bad file
        raise IOError

    # meta = score.metadata
    instrument_list = []

    # print('Instruments in file: {}'.format(len(score.parts)))
    # input()

    parts = [
        instrument(part,
                   SETTINGS,
                   instrument_list
                   )
        for part in score.parts]

    parts_df = pd.concat([*parts], axis=0)
    parts_df = parts_df.set_index('INSTRUMENT')

    if save_as is not None:
        parts_df.to_pickle(save_as + '.pkl')

    return parts_df
