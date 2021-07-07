import logging
import os
import time
import pandas as pd
import numpy as np
from music21 import *
from pathlib import Path


# Key index in our keyboard -> M21 Note
def key_index2note(i, midi_offset):
    index = i + midi_offset
    n = note.Note(midi=index)
    return n


# return tuple (key, transposed_stream)
#
# (label, key)
def transposeStreamToC(stream, force_eval=False):
    # trying to capture a M21 Key object in the stream
    stream_key = stream.getElementsByClass(key.Key)
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
            transpose_int = interval. \
                Interval(stream_key.tonic, pitch.Pitch('C'))
            transposed_stream = stream.transpose(transpose_int)
        elif stream_key.mode == 'minor':
            transpose_int = interval. \
                Interval(stream_key.tonic, pitch.Pitch('a'))
            transposed_stream = stream.transpose(transpose_int)

    return stream_key.tonicPitchNameWithCase, transposed_stream


# open and read file
#
# MIDI -> M21 Score
def open_file(midi_path, no_drums=True):
    # declare and read
    mf = midi.MidiFile()
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

    return midi.translate.midiFileToStream(mf)


# get all notes from m21 obj
#
# M21 Stream (Measure) -> Multi Hot Encoding
def measure_data(measure):
    data = []
    for item in measure:
        # print(item)
        if isinstance(item, note.Note) or isinstance(item, note.Rest):
            data.append(item)
            # print('data', data)
        elif isinstance(item, chord.Chord):
            for p in item.pitches:
                data.append(note.Note(pitch=p))
                # print('data', data)

    return data


# extract frames from measure
#
#  M21 Measure -> Multi Hot Encodinghttps://tenor.com/view/taffarel-futebol-no-score-gif-12585286
def measure2stackframe(measure, frames_per_beat, n_frames, n_notes, midi_offset, print_and_hold=False):
    data = measure_data(measure.flat)

    keyboard_range = n_notes + midi_offset

    frames = [[False for i in range(n_notes)] for j in range(n_frames)]

    for item in data:

        # if item is a Rest, we can break
        # since no key must be turned on
        if isinstance(item, note.Rest): break

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
        key = item.pitch.midi - midi_offset

        # turn them on captain!
        for frame in range(frame_s, frame_e):
            frames[frame][key] = True

        # print('{} | Índice: {} | Frame início: {} \t| \t Frame final: {}'.format(nt.nameWithOctave, index, frame_s, frame_e))
        # input()

    # create Pandas dataframe
    note_names = [key_index2note(i, midi_offset).nameWithOctave for i in range(0, n_notes)]
    frame_count = [int(i) for i in range(1, n_frames + 1)]
    stackframe = pd.DataFrame(frames, index=frame_count, columns=note_names)

    # print the full frame stack
    if print_and_hold:
        print(stackframe)
        input()

    return stackframe


# encode a single measure
#
# M21 Measure -> Multi Hot Encoding
def encode_measure(measure, n_frames, n_notes, midi_offset, p_ks, p_bpm, p_ts, p_inst, p_inst_midi_code, save_at=None):
    number = measure.measureNumber
    if save_at is not None:
        save_measure_at = save_at + '/Measure_' + str(number)
        save_stackframe_at = save_at + '/stackframe_' + str(number)

    # print('Encoding measure #{}'.format(number))

    # check for key changes
    m_ks, transposed_measure = transposeStreamToC(measure, force_eval=False)
    if m_ks is None:
        m_ks = p_ks

    # check for tempo changes
    m_bpm = measure.getElementsByClass(tempo.TempoIndication)
    if len(m_bpm) != 0:
        m_bpm = m_bpm[0].getQuarterBPM()
    else:
        m_bpm = p_bpm

    # check for time sign changes
    m_ts = measure.getTimeSignatures()
    if len(m_ts) != 0:
        m_ts = m_ts[0]
        if m_ts != p_ts:
            # ts changed
            if m_ts.ratioString != '4/4':
                logging.warning('Found measure not in 4/4, skipping.')
                return None
    else:
        m_ts = p_ts

    # calculate amount of frames per beat
    frames_per_beat = n_frames / m_ts.numerator

    # header
    header = [
        p_inst,
        p_inst_midi_code,
        m_ks,
        m_bpm,
        '{}/{}'.format(m_ts.numerator, m_ts.denominator)
    ]
    header = pd.Series(data=header)
    header_df = pd.DataFrame(np.tile(header, (n_frames + 1, 1)),
                             columns=['inst', 'inst_code', 'ks', 'bpm', 'ts'])
    # print(header1)
    # input()

    # pandas stackframe
    stackframe = measure2stackframe(transposed_measure,
                                    frames_per_beat,
                                    n_frames,
                                    n_notes,
                                    midi_offset,
                                    print_and_hold=False)

    # print(stackframe)
    # input()

    # print('Header:\n',header)
    # input()
    # print('SF:\n',stackframe)
    # input()

    encoded_measure = pd.concat([header_df, stackframe], axis=1).drop(0)
    # print(encoded_measure)
    # input()

    # encoded_measure = pd.concat([header, stackframe],
    #                             axis=1)

    # print('e_measure:\n',encoded_measure)
    # input()

    # encoded_measure = pd.DataFrame(header,
    #                                stackframe,
    #                                columns=['header', 'stackframe']
    #                                )

    if save_at is not None:
        stackframe.to_pickle(save_stackframe_at + '.pkl')
        encoded_measure.to_pickle(save_measure_at + '.pkl')

    return encoded_measure


# encode a single part
#
# M21 Part -> Multi Hot Encoding
def encode_part(part, n_frames, n_notes, midi_offset, save_part_at=None):
    # get part instrument
    inst_midi_code = part.getElementsByClass(instrument.Instrument)[0].midiProgram
    if inst_midi_code is None:
        logging.warning('Could not retrieve Midi Program from instrument {}, skipping.'
                        .format(part.getElementsByClass(instrument.Instrument)[0].instrumentName))
        return None
    inst = instrument.instrumentFromMidiProgram(inst_midi_code).instrumentName
    inst = inst.capitalize().replace('/', '').replace('.', '_')

    save_measures_at = None

    if save_part_at is not None:
        save_measures_at = save_part_at + '/' + inst
        if not os.path.isdir(save_measures_at):
            os.mkdir(save_measures_at)

    print('Encoding {}'.format(inst))

    # get part tempo
    metronome = part.getElementsByClass(tempo.TempoIndication)[0]
    bpm = metronome.getQuarterBPM()

    # filter parts that are not in 4/4
    ts = part.getTimeSignatures()[0]
    if ts.ratioString != '4/4':
        logging.error('Part not in 4/4, breaking.')
        exit(1)

    # transpose song to C major/A minor
    # original_ks, part = transposeStreamToC(part, force_eval=False)
    original_ks, transposed_part = transposeStreamToC(part, force_eval=True)

    # flat the stream
    # part = part.implode()
    # part. = part.voicesToParts()
    # part = part.semiFlat

    n_measures = len(part) + 1

    # a vector containing the measures
    first_measure = True
    for measure in transposed_part.measures(1, n_measures):
        e_measure = pd.DataFrame(
            encode_measure(measure,
                           n_frames,
                           n_notes,
                           midi_offset,
                           original_ks,
                           bpm,
                           '{}/{}'.format(ts.numerator, ts.denominator),
                           inst,
                           inst_midi_code
                           ))
        # print(e_measure)
        if first_measure:
            part_df = pd.DataFrame(e_measure)
            first_measure = False
        else:
            part_df = pd.concat([part_df, e_measure], axis=0, ignore_index=True)

        part_df.index = part_df.index + 1
        # print(part_df)
    # input()
    # print(part_df)

    # for showcase only
    # for measure in measures:
    #     encoded_part.append(measure)

    if save_measures_at is not None:
        part_df.to_pickle(save_part_at + '/' + inst + '.pkl')

    return part_df


# encode the file data from a .mid file
#
# MIDI -> Multi Hot Encoding (Pandas DataFrame)
def encode_data(path, n_frames, n_notes, midi_offset, save_at=None, save_folder=False):
    filename = Path(path).stem.replace(' ', '_').replace('/', '').replace('.', '_')
    filename = filename.capitalize()

    if save_at is not None:
        if not os.path.isdir(save_at):
            os.mkdir(save_at)

        if save_folder:
            folder_path = save_at + filename + '/'
            if not os.path.isdir(folder_path):
                os.mkdir(folder_path)

    print('Encoding file {}'.format(filename))
    timer = time.time()

    score = open_file(path)
    if not score:
        # bad file
        return None

    meta = score.metadata

    # print('Instruments in file: {}'.format(len(score.parts)))
    # input()

    # polyphonic -> monophonic
    # score.explode()
    score.voicesToParts()
    score.semiFlat

    # print('Instruments in file: {}'.format(len(score.parts)))
    # input()

    if save_at is not None:

        if save_folder:
            parts = [
                encode_part(part,
                            n_frames,
                            n_notes,
                            midi_offset,
                            save_part_at=folder_path
                            )
                for part in score.parts]
        else:
            parts = [
                encode_part(part,
                            n_frames,
                            n_notes,
                            midi_offset
                            )
                for part in score.parts]

        parts_df = pd.concat([*parts], axis=0)
        parts_df = parts_df.set_index('inst')

        # parts_df = pd.DataFrame(parts)
        parts_df.to_pickle(save_at + filename + '.pkl')

        # encoded_data = pd.DataFrame(meta, parts_df)
        # encoded_data.to_pickle(save_at + filename + '.pkl')

        print('Took {}'.format(time.time() - timer))
        # print(encoded_data.to_string())
        return parts_df
    else:

        # print(score.parts)
        parts = [
            encode_part(part,
                        n_frames,
                        n_notes,
                        midi_offset
                        )
            for part in score.parts]

        parts_df = pd.concat([*parts], axis=0)
        parts_df = parts_df.set_index('inst')

        encoded_data = pd.DataFrame(parts_df)

        # print('e_data', encoded_data)
        # input()

        print('Took {}'.format(time.time() - timer))
        # print(encoded_data.to_string())
        return encoded_data
