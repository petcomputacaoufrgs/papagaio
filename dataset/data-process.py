import guitarpro
import music21
import os

file = 'gp_files/Bob Marley/Bob Marley - Waiting In Vain (ver 3 by Mauriciobasalo).gp5'
path, filename = os.path.split(file)

if filename.endswith('.gp'):
    new_fn = filename + '5'
    os.rename(filename, new_fn)
    print(f'{filename} -> {new_fn}')
    filename = new_fn

if filename.endswith('gpx'):
    #turn gpX files int GP5
    new_fn = filename[:-1] + '5'
    os.rename(filename, new_fn)
    print(f'{filename} -> {new_fn}')
    filename = new_fn

path = path.replace('gp_files', 'mid_files')
os.makedirs(path, exist_ok=True)
outfile = os.path.join(path, filename[:-4] + '.mid')
print(outfile)
os.system(f"musescore '{file}' -o '{outfile}'")

# song = guitarpro.parse(file)
# print(song.tracks)

# input()

mf = music21.midi.MidiFile()
mf.open(outfile)
mf.read()
mf.close()
song = music21.midi.translate.midiFileToStream(mf)

for track in song.parts:
    track.makeMeasures(inPlace=True)
# song.show('text')

mf = music21.midi.translate.streamToMidiFile(song)
mf.open(outfile, 'wb')
mf.write()

# for i in song.tracks:
#     print(i)
# for track in song.tracks:
#     for measure in track.measures:
#         for voice in measure.voices:
#             for beat in voice.beats:
#                 for note in beat.notes:
#                     print(note.durationPercent)
#                     print(note.effect)