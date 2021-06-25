import numpy as np
from tqdm import tqdm
import pandas as pd
from music21 import *


# Key index in our keyboard -> M21 Note
def key_index2note(i, midi_offset):
    index = i + midi_offset
    n = note.Note(midi=index)
    return n


# decode a N_NOTESxN_FRAMES array and turn it into a m21 Measure
def decode_measure(measure, n_frames, ts):
    last_frame = False

    # the stream that will receive the notes
    output = stream.Measure()

    # vectors that will hold the current notes states and durations
    # they are initialized with the values of the first frame
    state_register = measure[:][0].copy().to_numpy()
    start_register = measure[:][0].copy().to_numpy() - 1
    duration_register = measure[:][0].copy().to_numpy()

    # iterate over frames
    for f in range(n_frames):
        # print('Frame ', f)
        # with np.printoptions(threshold=np.inf):
        #     print('\nStates:\t', state_register.reshape(1, 88))
        #     print('\nStarts:\t', start_register.reshape(1, 88))
        #     print('\nDurs:\t', duration_register.reshape(1, 88))
        # input()

        frames_per_beat = n_frames / ts.numerator

        frame = measure[f]

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


# decode a PARTxN_NOTESxN_FRAMES array
def decode_part(part, n_frames):
    decoded = stream.Stream()

    # part settings
    try:
        decoded.append(instrument.fromString(part[0]))
    except:
        pass

    ks = key.Key(part[1])
    transpose_int = 0
    decoded.append(ks)
    if ks != 'C' and ks != 'a':
        if ks.mode == 'major':
            transpose_int = interval. \
                Interval(pitch.Pitch('C'), ks.tonic)

        elif ks.mode == 'minor':
            transpose_int = interval. \
                Interval(pitch.Pitch('a'), ks.tonic)

    decoded.append(tempo.MetronomeMark(number=part[2], referent='quarter'))
    ts = meter.TimeSignature(part[3])
    decoded.append(ts)

    part_measures = part[4:][0]

    # iterate over measures (bars)
    for i, m in enumerate(part_measures):
        # measure settings
        decoded.append(key.Key(m[0]))
        decoded.append(tempo.MetronomeMark(number=m[1], referent='quarter'))
        # decoded.append(tempo.TempoIndication(m[1]))
        decoded.append(meter.TimeSignature(m[2]))

        # now here comes the frames
        measure = pd.DataFrame(m[3:][0])
        measure = measure.T
        print("Measure {}\n".format(i+1), measure)
        # input()
        decoded.append(decode_measure(measure, n_frames, meter.TimeSignature('4/4')))

    decoded.transpose(transpose_int, inPlace=True)
    decoded.makeNotation(inPlace=True)
    decoded.write('midi', fp='decoded.mid')
    print('Saved')
    # input()

    return decoded


# decode a list of streams
def decode_data(data, n_frames, n_notes, midi_offset, save_as=None):
    decoded = None

    meta = data.metadata
    data = data.data

    for i, part in enumerate(data):
        print('Decoding part #{}', i + 1)
        decoded_part = decode_part(part)
        decoded.append(decoded_part)

    decoded.makeNotation(inPlace=True)

    # save .mid
    if save_as is not None:
        decoded.write('midi', fp=save_as)

    return decoded
