import sys
import numpy as np
import pandas as pd
from music21 import *
import music21
import glob
from tqdm import tqdm

# open and read file
def open_midi(midi_path, no_drums):
    mf = music21.midi.MidiFile()
    mf.open(midi_path)
    mf.read()
    mf.close()
    if (no_drums):
        for i in range(len(mf.tracks)):
            mf.tracks[i].events = [ev for ev in mf.tracks[i].events if ev.channel != 10]

    return music21.midi.translate.midiFileToStream(mf)


# get all notes from music21 obj
def extract_notes(midi_part):
    parent_element = []
    # print(midi_part)
    # ret = []
    for nt in midi_part.flat.notes:
        if isinstance(nt, note.Note):
            # ret.append(max(0.0, nt.pitch.ps))
            parent_element.append(nt)
        elif isinstance(nt, chord.Chord):
            for pitch in nt.pitches:
                # ret.append(max(0.0, pitch.ps))
                parent_element.append(nt)

    # return ret, parent_element
    return parent_element


# extract frames from each measure
def measure2frames(measure, n_frames, N_BEATS=4, BEAT_S=None, DUR=None):
    measure_notes = extract_notes(measure)
    v = []
    for i in measure_notes:
        if isinstance(i, chord.Chord):
            for nt in i:
                v.append(nt)

        else:
            v.append(i)

    try:
        frames_beat = n_frames / measure.timeSignature.numerator
    except:
        frames_beat = n_frames / N_BEATS
    # print(frames_beat)

    frames = [[0 for i in range(88)] for j in range(n_frames)]

    for nt in v:
        if BEAT_S:
            frame_i = int((BEAT_S - 1) * frames_beat)
        else:
            try:
                frame_i = int((nt.beat - 1) * frames_beat)
            except:
                pass

        if DUR:
            frame_e = frame_i + int((DUR - 1) * frames_beat)
        else:
            try:
                frame_e = frame_i + int(nt.quarterLength * frames_beat)
            except:
                pass

        index = nt.pitch.midi - 24

        try:
            for i in range(frame_i, frame_e):
                # frames[i][index] = index
                frames[i][index] = 1
        except:
            pass

        # print('{} | Índice: {} | Frame início: {} \t| \t Frame final: {} \t | Frames: {}'.format(nt.nameWithOctave, index, frame_i, frame_e, frame_c))

    # print(len(frames))
    return frames


# retrieve data from music21 Part obj
def get_part_data(part):
    part_data = []

    n_bars = int(len(part) / part.timeSignature.numerator)
    bar = []
    for measure in part.measures(1, n_bars):
        # print(measure)

        if isinstance(measure, stream.Measure):
            try:
                bar.append(extract_notes(measure))
                # print(extract_notes(measure))
            except:
                pass
            part_data.append(bar)

    return part_data


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
        try:
            data = get_part_data(part.flat)
        except:
            break

        part_frames = []

        for it in tqdm(part.measures(1, len(data)),
                       desc="Converting measures from part {}".format(i + 1),
                       ascii=True, ncols=150):

            if isinstance(it, instrument.Instrument):
                print(it)
                # input()

            if isinstance(it, stream.Measure):
                part_frames.append(measure2frames(it, n_frames))

        this_part = np.asarray(part_frames)
        parts.append(this_part)
        data.clear()

    return parts


# get encoded file parts with 32 frames per measure (bar)
#parts = encode_data(path, N_FRAMES)

#for part in parts:
    # part = part.T
    # print(part.shape)
    # print(pd.DataFrame(part[0]))
