## Running

For each ```.mid``` file, we need to encode it to be read by the model.
We have the **encoder** to encode ```.mid``` files into the multi-hot encoding, and the **decoder** to decode a multi-hot tensot into a ```.mid``` file.

### Encoder

The file ```encoder.py``` contains functions related to the encoding MIDI -> multi-hot-encoding.
The function ```encode_data()``` converts a ```.mid``` file into  a ```pandas``` dataframe, which is an encoded file with N_FRAMES frames per measure (bar). The function call is described below:

```python:
data_in = encode_data(in_path,  
                     N_FRAMES, 
                     N_NOTES, 
                     MIDI_OFFSET, 
                     save_encoded_at=None, 
                     save_file=False)
```

where:
* in_path: is the initial .mid file path
* N_FRAMES: is the number of frames that will be encoded
* N_NOTES: is the number of notes that will be encoded in the framme
* MIDI_OFFSET:  
* save_encoded_at: .mid file path. Default: None
* save_file: whether the file is going to be saved or not. Default: None


## Decoder

