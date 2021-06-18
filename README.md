# Papagaio

## About

Music resamples language as a temporal sequence of articulated sounds. They say something, often something human.

Although, there are crucial differences between language and music. We can still describe it as a sequence of symbols in the simplest form of understanding. Translating something complex into something simpler, but usable by computational models.

Thus, the objective of this project is to establish a communication between the human, that understands music in the most intense way that the brain can interpret through information, and the machine.

We'll create a model that can generate music based on the input information, i.e., generate a sequence of sounds which are related in some way with the sounds passed as input.

We'll use Natural Language Processing (NLP) methods, observing the music as it were a language, abstracting it. Doing this, the machine can recognize and process similar data.

On the first step, we'll use text generation techniques, using Recurrent Neural Networks (RNNs) and Long-Short Term Memories (LSTMs). With the effectiveness of the training, even if it's reasonable, we'll perform the same implementation using specific models such as Transformers.

## Dataset

## Data preprocessing
From an input file with songs in MIDI format, we preprocess the data in order to encode them using multi-hot encoding.

![image](https://user-images.githubusercontent.com/49798588/120706718-cdf9ce00-c48f-11eb-8eb1-db7f31cf26af.png)


For each bar, we separate them into 32 different frames, where each frame is an 88-position multi-hot vector, which each position represents the notes of a standard keyboard. The notes that are being played at the exact instant of the frame receive the value '1' in the respective position of the vector, whereas the notes that are turned off receive the value '0'.

The representation of the list is exemplified below.

![image](https://user-images.githubusercontent.com/49798588/120706592-ac004b80-c48f-11eb-9aad-89ce5634029a.png)

## LSTM Model

### Structure

### Training and validation

### Tests and music generation

## Improvements and optimizations
