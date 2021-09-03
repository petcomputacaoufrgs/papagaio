import guitarpro
import music21
import os
import logging
from pathlib import Path

input_dir = 'gp_files'


def gp2midi(file_path, outfile_path):

    query = f"musescore '{file_path}' -o '{outfile_path}'"
    # print(query)

    try:
        s = os.system(query)
    except Exception as e:
        logging.error(e)
    if s:
        logging.error('Failed to convert .GP -> MIDI.')
        return

    mf = music21.midi.MidiFile()
    mf.open(outfile_path)
    mf.read()
    mf.close()

    # remove drums
    for i in range(len(mf.tracks)):
        mf.tracks[i].events = [ev for ev in mf.tracks[i].events if ev.channel != 10]

    song = music21.midi.translate.midiFileToStream(mf)

    # for track in song.parts:
    #     pass

    music21.midi.translate.prepareStreamForMidi(song)
    mf = music21.midi.translate.streamToMidiFile(song)
    mf.open(outfile_path, 'wb')
    mf.write()
    return


# for i in song.tracks:
#     print(i)
# for track in song.tracks:
#     for measure in track.measures:
#         for voice in measure.voices:
#             for beat in voice.beats:
#                 for note in beat.notes:
#                     print(note.durationPercent)
#                     print(note.effect)


if __name__ == '__main__':
    pathlist = Path(input_dir).glob('**/*.gp*')

    for path in pathlist:

        file_path = str(path)

        folder, filename = os.path.split(file_path)

        if "'" in folder:
            # same thing but now with the quote char
            new_f = folder.replace("'", '')
            Path(new_f).mkdir(exist_ok=True)
            logging.info(f'{folder} -> {new_f}')
            folder = new_f

        if file_path.endswith('gpx'):
            # .gpx cause problems.
            # we must rename them to .gp5
            # to solve this
            new_fp = file_path[:-1] + '5'
            os.rename(file_path, new_fp)
            logging.info(f'{file_path} -> {new_fp}')
            file_path = new_fp

        if file_path.endswith('gp'):
            # same thing that the .gpx
            new_fp = file_path + '5'
            os.rename(file_path, new_fp)
            logging.info(f'{file_path} -> {new_fp}')
            file_path = new_fp

        if "'" in filename:
            # same thing but now with the quote char
            new_fn = filename.replace("'", '')
            logging.info(f'{filename} -> {new_fn}')
            filename = new_fn

        file_path = os.path.join(folder, filename)
        filename = filename.split(' - ')[1]
        folder = folder.replace('gp_files', 'mid_files')
        Path(folder).mkdir(exist_ok=True)
        outfile_path = os.path.join(folder, filename[:-4] + '.mid')

        gp2midi(file_path, outfile_path)