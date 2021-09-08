import os
import sys
import pretty_midi
import time
import streamlit as st
import music21
import pandas as pd
import numpy as np
import torch
import torch.nn as nn

# import src.MidiExpress as MidiExpress


SETTINGS = pd.Series(
    {
        'RESOLUTION': 36,
        'KEYBOARD_SIZE': 88,
        'KEYBOARD_OFFSET': 20
    }
)

device = torch.device("cuda:0") if torch.cuda.is_available() else torch.device("cpu")


class BI_LSTM(nn.Module):
    def __init__(self, input_size, hidden_size, num_layers, output_size):
        super(BI_LSTM, self).__init__()

        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=False, bidirectional=True)
        self.fc1 = nn.Linear(hidden_size * 2, hidden_size * 2)
        self.fc2 = nn.Linear(hidden_size * 2, output_size)
        self.relu = nn.ReLU()
        self.softplus = nn.Softplus(beta=500, threshold=0)
        self.sigmoid = nn.Sigmoid()

        # self.fromInstrument =
        # self.toInstrument =

    def forward(self, x, hidden, cell):
        # Passing in the input and hidden state into the model and obtaining outputs
        out, (hidden, cell) = self.lstm(x.unsqueeze(1), (hidden, cell))

        # Reshaping the outputs such that it can be fit into the fully connected layer
        out = out.contiguous().view(-1, self.hidden_size * 2)

        out = self.fc2(out)
        out = self.sigmoid(out)

        return out, (hidden, cell)

    def init_hidden(self, batch_size):
        # This method generates the first hidden state of zeros which we'll use in the forward pass
        # We'll send the tensor holding the hidden state to the device we specified earlier as well
        hidden = torch.zeros(self.num_layers * 2, batch_size, self.hidden_size).to(device)
        cell = torch.zeros(self.num_layers * 2, batch_size, self.hidden_size).to(device)

        return hidden, cell


# TODO: Be able to especify the number of measures to predict!

@torch.no_grad()
def generateMeasures(model, context, resolution, amount=1, temperature=0.5, batch_size=1):
    hidden, cell = model.init_hidden(batch_size)

    if isinstance(context, torch.Tensor):
        # send to gpu
        context_performance_block = context.cuda()
        # cast to float
        context_performance_block = context_performance_block.float()
    else:
        context_performance_block = torch.from_numpy(context.astype(float)).float().to(device)

    # amount of frameblocks in the context input
    n_context_performance_block = len(context_performance_block) - resolution

    # getting context iterating over
    # N-1 of the frameblocks

    for i in range(n_context_performance_block):
        context_performance = context_performance_block[i:i + resolution]

        # we dont care about the output here.
        # we are just feeding the model with the
        # context we received as input
        _, (hidden, cell) = model(context_performance,
                                  hidden, cell)

    # we must get the output from the last context fb
    last_context_performance = context_performance_block[n_context_performance_block:]

    output_measures = []
    for _ in range(amount):

        out, (hidden, cell) = model(last_context_performance, hidden, cell)

        # generate the other remaining frames
        for i in range(resolution - 1):
            out = torch.where(out >= (1 - temperature), 1, 0).float()
            out, (hidden, cell) = model(out, hidden, cell)

            # # update last frame block
            # last_context_performance = out

        out = np.where(out.cpu() >= (1 - temperature), True, False)
        output_measures.append(out)

    # print(out, out.shape)
    return np.array(output_measures, dtype=bool)


header = st.beta_container()
modelUpload = st.beta_container()
modelUpload = st.beta_container()



@st.cache(suppress_st_warning=True)
def readContextFile(file):
    contextFile = pretty_midi.PrettyMIDI(file)

    contextFile.write('temp.mid')

    context = MidiExpress.read.file('temp.mid', SETTINGS)

    return context


# TODO: receive a input int for the amount of info data (currently 4).
#       this way testing will be easier.

def getPerformance(data, first_frame, last_frame, to_float=True):
    stackframe = data.iloc[first_frame:last_frame, 4:]
    stackframe = stackframe.to_numpy()

    if to_float:
        stackframe.astype(float)
        stackframe = stackframe + 0.0

    return stackframe


def getInfo(data, first_frame, last_frame):
    infos = data.iloc[first_frame:last_frame, 0:4]
    return infos


def mergeData(infos, stackframe, instrument, midi_offset):
    # (A, B, C)
    #
    # A -> number of measures (bars)
    # B -> number of frames (resolution)
    # C -> number of notes (keyboard size)

    n_measures = stackframe.shape[0]
    resolution = stackframe.shape[1]
    keyboard_size = stackframe.shape[2]

    # Generate note names and use as column
    sf_columns = [MidiExpress.key_index2note(i, midi_offset).nameWithOctave for i in range(keyboard_size)]

    # Initialize blank df with notes column
    measures = pd.DataFrame([], columns=sf_columns)
    measures.index.name = 'inst'

    #
    for i in range(n_measures):
        indexes = pd.Series([instrument for i in range(resolution)])
        decoded_measure = pd.DataFrame(stackframe[i], columns=sf_columns).set_index(pd.Index(indexes))
        measures = measures.append(decoded_measure)

    print(f'Info shape {infos.shape} | measures shape {measures.shape}')

    output = pd.concat([infos, measures], axis=1)

    print(f'Result shape {output.shape}')

    return output


# Reshape so that we have all frames in one dimension
# generated_sf = generated_sf.reshape(-1, generated_sf.shape[-1])
# print(f'Reshaped stackframe: \n {generated_sf} \t Shape: {generated_sf.shape}')


def runGeneration(model, instrument, contextData, amountToGenerate, firstContextMeasure, lastContextMeasure, temperature):
    generatedFile = None
    with st.spinner(f'Generating {amountToGenerate} measures...'):
        first_context_frame = (firstContextMeasure - 1) * SETTINGS.RESOLUTION
        last_context_frame = lastContextMeasure * SETTINGS.RESOLUTION - 1

        first_generated_frame = last_context_frame
        last_generated_frame = first_generated_frame + SETTINGS.RESOLUTION

        context_info = getInfo(contextData, first_context_frame, last_context_frame)

        context_performance = getPerformance(contextData, first_context_frame, last_context_frame, to_float=True)

        generated_info = getInfo(contextData, first_generated_frame, last_generated_frame)
        generated_info = pd.concat([generated_info] * amountToGenerate)

        start_timer = time.time()
        generatedPerformance = generateMeasures(model,
                                                context_performance,
                                                SETTINGS.RESOLUTION,
                                                amount=amountToGenerate,
                                                temperature=temperature
                                                )

        # Merge StackFrame and Info blocks
        generatedRepresentation = mergeData(generated_info, generatedPerformance, instrument, SETTINGS.KEYBOARD_OFFSET)
        st.write(f'Generated interpretation shape: {generatedRepresentation.shape}')
        showGen1 = st.expander('Show generated interpretation (50 lines)', expanded=False)
        with showGen1:
            st.table(generatedRepresentation.head(50))

        generatedFile = MidiExpress.write.file(generatedRepresentation, SETTINGS, save_as='output.mid')

        showGen2 = st.expander('Show generated file as piano roll', expanded=False)
        with showGen2:
            st.pyplot(generatedFile.plot('pianoroll'))

        end_timer = time.time()
        st.write(f'Took {end_timer - start_timer} seconds.')

    st.subheader('Download generated file')
    st.download_button('Generated file', 'output.mid')


def main():

    # st.title('Papagaio: Digital music generation using Bidirectional LSTM')

    modelFile = st.file_uploader('Upload a model', type='pt')
    if modelFile is not None:
        with st.spinner('Loading model...'):
            model = torch.load(modelFile)
        st.text(model)

        contextData = None
        contextFile = st.file_uploader('Upload a MIDI file for context', type='mid')
        if contextFile is not None:
            contextData = readContextFile(contextFile)

        if contextData is not None:
            instrumentList = pd.Series(list(set(contextData.index)), name='Instrument list')
            st.subheader('Choose a instrument from context file')
            instrument = st.selectbox('Choose a instrument from context file', options=instrumentList)

            contextData = contextData[contextData.index == instrument]
            contextMeasureAmount = int(len(contextData) / SETTINGS.RESOLUTION)

            st.write(f'Context interpretation shape: {contextData.shape}')
            showInterpretation = st.expander('Show context interpretation (50 lines)', expanded=False)
            with showInterpretation:
                st.table(contextData.head(50))

            st.subheader('Select the context offset if measures')
            (firstContextMeasure,
             lastContextMeasure) = st.slider('Select context measures',
                                             min_value=1,
                                             max_value=contextMeasureAmount,
                                             value=(1, contextMeasureAmount))

            amountToGenerate = st.number_input('Enter the amount of measures to generate', value=10)
            temperature = st.number_input('Enter the temperature for generation', value=0.55)

            btnGenerate = st.button('GENERATE')
            if btnGenerate:
                runGeneration(model, instrument, contextData, amountToGenerate, firstContextMeasure, lastContextMeasure,
                              temperature)


if __name__ == '__main__':
    st.set_page_config(
        page_title="Papagaio",
        page_icon="musical_note",
        initial_sidebar_state="collapsed",
        layout='wide'
    )
    main()
