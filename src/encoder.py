import logging
import os
import time
import pandas as pd
from music21 import *
from pathlib import Path


# Key index in our keyboard -> M21 Note
def key_index2note(i, midi_offset):
    index = i + midi_offset
    n = note.Note(midi=index)
    return n


# return tuple (key, transposed_stream)
def transposeStreamToC(stream, forceEval=False):
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
    if forceEval and stream_key is None:
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
    mf = midi.MidiFile()
    mf.open(midi_path)
    mf.read()
    mf.close()
    if no_drums:
        for i in range(len(mf.tracks)):
            mf.tracks[i].events = [ev for ev in mf.tracks[i].events if ev.channel != 10]

    return midi.translate.midiFileToStream(mf)


# get all notes from m21 obj
#
# M21 Stream (Measure) -> Multi Hot Encoding
def measure_data(measure):
    data = []
    for item in measure:
        if isinstance(item, note.Note) or isinstance(item, note.Rest):
            data.append(item)
        elif isinstance(item, chord.Chord):
            for p in item.pitches:
                data.append(note.Note(pitch=p))

    # print(parent_element)
    # input()
    return data


# extract frames from measure
#
#  M21 Measure -> Multi Hot Encodinghttps://tenor.com/view/taffarel-futebol-no-score-gif-12585286
def measure2stackframe(measure, frames_per_beat, n_frames, n_notes, midi_offset, print_and_hold=False):
    data = measure_data(measure)

    keyboard_range = n_notes + midi_offset

    frames = [[0 for i in range(n_notes)] for j in range(n_frames)]

    for item in data:

        # if item is a Rest, we can break
        # since no key must be turned on
        if isinstance(item, note.Rest): break

        # if the item is a Note that is above
        # or below our keyboard range, we can break
        # cause it will not be represented
        if item.pitch.midi > keyboard_range:
            break

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
    frame_count = [i for i in range(1, n_frames + 1)]
    stackframe = pd.DataFrame(frames, index=frame_count, columns=note_names)

    # print the full frame stack
    if print_and_hold:
        print(stackframe)
        input()

    return stackframe


# encode a single measure
#
# M21 Measure -> Multi Hot Encoding
def encode_measure(measure, n_frames, n_notes, midi_offset, p_ks, p_bpm, p_ts, save_at=None):
    number = measure.measureNumber
    if save_at is not None:
        save_measure_at = save_at + '/Measure_' + str(number)
        save_stackframe_at = save_at + '/stackframe_' + str(number)

    # print('Encoding measure #{}'.format(number))

    # check for key changes
    m_ks, measure = transposeStreamToC(measure, forceEval=False)
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
    header = [m_ks,
              m_bpm,
              '{}/{}'.format(m_ts.numerator, m_ts.denominator)]
    header = pd.DataFrame(header, index=['keySignature', 'BPM', 'timeSignature'])

    # pandas stackframe
    stackframe = measure2stackframe(measure,
                                    frames_per_beat,
                                    n_frames,
                                    n_notes,
                                    midi_offset,
                                    print_and_hold=False)

    encoded_measure = pd.Series(
        {
            'header': header,
            'stackframe': stackframe
        }

    )

    if save_at is not None:
        encoded_measure.to_csv(save_measure_at + '.csv')
        stackframe.to_csv(save_stackframe_at + '.csv')

    return encoded_measure


# encode a single part
#
# M21 Part -> Multi Hot Encoding
def encode_part(part, n_frames, n_notes, midi_offset, save_part_at=None):
    name = part.partName.replace(' ', '_').replace('/', '')
    save_measures_at = None

    if save_part_at is not None:
        save_measures_at = save_part_at + '/' + name
        if not os.path.isdir(save_measures_at):
            os.mkdir(save_measures_at)

    print('Encoding part {}'.format(name))

    # get part instrument
    inst = part.getElementsByClass(instrument.Instrument)[0].instrumentName

    # get part tempo
    metronome = part.getElementsByClass(tempo.TempoIndication)[0]
    bpm = metronome.getQuarterBPM()

    # filter parts that are not in 4/4
    ts = part.getTimeSignatures()[0]
    if ts.ratioString != '4/4':
        logging.error('Part not in 4/4, breaking.')
        exit(1)

    # transpose song to C major/A minor
    ks, part = transposeStreamToC(part, forceEval=True)

    # header
    header = [inst,
              ks,
              bpm,
              '{}/{}'.format(ts.numerator, ts.denominator)]
    header = pd.DataFrame(header, index=['instrument', 'keySignature', 'BPM', 'timeSignature'])

    measures = pd.DataFrame([encode_measure(i,
                                            n_frames,
                                            n_notes,
                                            midi_offset,
                                            ks,
                                            bpm,
                                            '{}/{}'.format(ts.numerator, ts.denominator),
                                            save_at=save_measures_at
                                            ) for i in part.measures(1, len(part))])

    # flat the stream
    # part = part.voicesToParts()
    # part = part.semiFlat

    encoded_part = pd.Series(
        {
            'header': header,
            'measures': measures
        }
    )

    # for showcase only
    # for measure in measures:
    #     encoded_part.append(measure)

    if save_measures_at is not None:
        encoded_part.to_csv(save_part_at + '/' + name + '.csv')

    return encoded_part


# encode the file data from a .mid file
#
# MIDI -> Multi Hot Encoding (Pandas DataFrame)
def encode_data(path, n_frames, n_notes, midi_offset, save_at=None, save_folder=False):
    filename = Path(path).stem.replace(' ', '_').replace('/', '')

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
    meta = score.metadata

    # score.show('text')
    # input()

    # polyphonic -> monophonic
    score.explode()
    score.voicesToParts()
    score.semiFlat

    if save_at is not None:

        if save_folder:
            parts = [
                pd.DataFrame(
                    encode_part(part,
                                n_frames,
                                n_notes,
                                midi_offset,
                                save_part_at=folder_path
                                )
                ) for part in score.parts]
        else:
            parts = [
                pd.DataFrame(
                    encode_part(part,
                                n_frames,
                                n_notes,
                                midi_offset
                                )
                ) for part in score.parts]

        encoded_data = pd.Series(
            {
                'metadata': meta,
                'data': parts
            }
        )

        encoded_data.to_csv(save_at + filename + '.csv')

        print('Took {}'.format(time.time() - timer))
        return encoded_data
    else:
        parts = [
            pd.DataFrame(
                encode_part(part,
                            n_frames,
                            n_notes,
                            midi_offset
                            )
            ) for part in score.parts]

        encoded_data = pd.Series(
            {
                'metadata': meta,
                'data': parts
            }
        )
        print('Took %f.3 seconds.' % (time.time() - timer))
        return encoded_data
