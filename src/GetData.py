import sys
import numpy as np
import pandas as pd
from music21 import *
import music21 as m21
import glob
from tqdm import tqdm
import matplotlib.pyplot as plt
from scipy import interpolate

# path = '../data/Dreadlock_Holiday.4.mid'
N_FRAMES = 36
N_NOTES = 88
MIDI_OFFSET = 20


def int2note(i):
    index = i + MIDI_OFFSET
    n = m21.note.Note(midi=index)
    return n


# open and read file
def open_midi(midi_path, no_drums):
    mf = m21.midi.MidiFile()
    mf.open(midi_path)
    mf.read()
    mf.close()
    if (no_drums):
        for i in range(len(mf.tracks)):
            mf.tracks[i].events = [ev for ev in mf.tracks[i].events if ev.channel != 10]

    return m21.midi.translate.midiFileToStream(mf)


# get all notes from m21 obj
def extract_notes(midi):
    parent_element = []
    # print(midi_part)
    # ret = []
    for nt in midi.flat.notes:
        if isinstance(nt, note.Note):
            parent_element.append(nt)
        elif isinstance(nt, chord.Chord):
            for p in nt.pitches:
                # print(p, m21.note.Note(pitch=p))
                # input()
                parent_element.append(m21.note.Note(pitch=p))

    # print(parent_element)
    # input()
    return parent_element


# extract frames from each measure
def measure2frames(measure, n_frames, N_BEATS=4):
    measure_notes = extract_notes(measure)

    frame_s = None
    frame_e = None

    try:
        frames_beat = n_frames / measure.timeSignature.numerator
    except:
        frames_beat = n_frames / N_BEATS
    # print(frames_beat)

    frames = [[0 for i in range(N_NOTES)] for j in range(n_frames)]

    for nt in measure_notes:
        # try:
        # print(nt.offset)
        frame_s = int(nt.offset * frames_beat)
        # except:
        # print('a')
        # break
        # pass

        # try:
        # print(int(nt.quarterLength * frames_beat))
        frame_e = frame_s + int(nt.quarterLength * frames_beat)
        # except:
        # print('b')
        # break
        # pass

        index = nt.pitch.midi - MIDI_OFFSET

        for i in range(frame_s, frame_e):
            # frames[i][index] = index
            frames[i][index] = 1

        # print('{} | Índice: {} | Frame início: {} \t| \t Frame final: {}'.format(nt.nameWithOctave, index, frame_s, frame_e))
        # input()

    # print('\n', pd.DataFrame(frames).to_string())
    # input()
    return frames


# encode the file data from a .mid file
def encode_data(path, n_frames):
    print('Processing file {}'.format(path))
    score = open_midi(path, True)

    n = len(score.parts)
    parts = []

    for i, part in enumerate(score.parts):

        print('Processing part {}/{}'.format(i + 1, n))

        n_beats = None

        try:
            n_beats = part.timeSignature.numerator
        except:
            n_beats = 4

        part_frames = []

        for it in tqdm(part.measures(1, len(part)),
                       desc="Converting part {}".format(i + 1),
                       ncols=80):

            if isinstance(it, instrument.Instrument):
                print('Intrumento: ', it)
                # input()

            if isinstance(it, stream.Measure):
                part_frames.append(measure2frames(it, n_frames))

        this_part = np.asarray(part_frames)
        parts.append(this_part)

    return parts


# decode a N_NOTESxN_FRAMES array and turn it into a m21 Measure
def decode_measure(measure, n_frames):

    last_frame = False

    # the stream that will receive the notes
    output = stream.Stream()

    # vectors that will hold the current notes states and durations
    # they are initialized with the values of the first frame
    state_register = measure[:][0].copy().to_numpy()
    start_register = measure[:][0].copy().to_numpy() - 1
    duration_register = measure[:][0].copy().to_numpy()

    # iterate over frames
    for f in range(1, n_frames):
        # print('Frame ', f)
        # with np.printoptions(threshold=np.inf):
        #     print('\nStates:\t', state_register.reshape(1, 88))
        #     print('\nStarts:\t', start_register.reshape(1, 88))
        #     print('\nDurs:\t', duration_register.reshape(1, 88))
        # input()

        frame = measure[f]

        if f == n_frames - 1:
            last_frame = True

        # print("Frame {}\n".format(j), frame)
        # input()

        # iterate over notes
        # state is ON/OFF 1/0
        for note_index, state in enumerate(frame):

            # if note state changed
            if bool(state) != bool(state_register[note_index]):

                # 1 -> *0*
                if bool(state) is False:

                    note = int2note(note_index)
                    note.offset = start_register[note_index] / n_frames
                    note.duration.quarterLength = duration_register[note_index] / n_frames

                    output.append(note)

                    # restarting the registers
                    duration_register[note_index] = 0
                    state_register[note_index] = 0
                    start_register[note_index] = -1

                    # print(note)
                    # input()

                # 0 -> *1*
                else:
                    # starting registers
                    duration_register[note_index] = 1
                    state_register[note_index] = 1
                    start_register[note_index] = f+1

            # if note is on and didnt change, increase duration
            elif bool(state) is True:
                duration_register[note_index] += 1

            # note is ON and measure ended
            elif bool(state_register[note_index]) and last_frame:

                note = int2note(note_index)
                note.offset = start_register[note_index] / n_frames
                note.duration.quarterLength = duration_register[note_index] / n_frames
                # print('Change caused by end frame #{}'.
                #       format(f + 1),
                #       ':\t {} | duration: {} | {} -> {}'.
                #       format(note.nameWithOctave, note.duration,
                #              bool(state_register[note_index]), bool(state)))
                output.append(note)

                # print(note)
                # input()

    # output.show('text')
    # for n in output:
    #     print("Note: %s%d | Start: %0.3f | End: %0.3f" %
    #           (n.pitch.unicodeName, n.pitch.octave, n.offset, n.offset + n.duration.quarterLength))
    # input()

    return output


# decode a PARTxN_NOTESxN_FRAMES array
def decode_part(part, n_frames):
    # iterate over measures (bars)
    for m in range(len(part)):
        measure = pd.DataFrame(part[m])
        measure = measure.T
        # print("Measure {}\n".format(i+1), measure)

        # print(measure.shape[1])
        # input()

        # print(measure)
        # input()
        # print(measure.to_string())

        print("Measure #{}".format(m + 1))
        decode_measure(measure, n_frames)


# get encoded file parts with N_FRAMES frames per measure (bar)
parts = encode_data(path, N_FRAMES)

for i, part in enumerate(parts):
    # print(part.shape)
    print('Part #{}'.format(i + 1))
    decode_part(part, N_FRAMES)
