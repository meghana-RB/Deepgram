from flask import Flask
import wave
import contextlib
import json
import speech_recognition as sr
from os import path
import os

def save_json_to_disk(file_metadata: dict)->None:
    """
    Updates the json on disk with newly transcribed disctionary

    Parameter:
        file_metadata: newly introduced dictionary to be saved to disk
    Returns: None
    """
    pwd = os.getcwd()
    file_path = os.path.join(pwd, 'audio_data_repo.json')
    dict = []
    if os.path.isfile(file_path):
        with open(file_path,'r+') as outfile:
            dict = json.load(outfile)
            
    dict.append(file_metadata)
    with open('audio_data_repo.json', "w") as outfile:
        json.dump(dict, outfile)


def get_duration(filename: str)->float:
    """
    Gets the duration of an audio file

    Parameters:
       filename: name of the file for the duration to be determined
    Returns:
       duration: the duration of the file if of type audio
    """
    with contextlib.closing(wave.open(filename,'r')) as f:
        frames = f.getnframes()
        rate = f.getframerate()
        duration = frames / float(rate)

    return round(duration, 2)


def process_text(text: str)->json:

    list_of_words = text.split(' ')
    dict_of_words = {}
    dict_of_words['transcipt']=text
    dict_of_words['words']=list_of_words
    dict_of_words['number of words']=len(list_of_words)
    return dict_of_words


def convert_wav_to_jsons(filename: str)->None:
    """
    Converts an audio file to transcribed text with metadata

    Parameters:
        filename: name of the file to be processed to text and stored
    Returns: None
    """
    # wav_files = [f for f in os.listdir(path) if f.endswith('.wav')]
    # text = ''
    # for file in wav_files:

    r = sr.Recognizer()
    with sr.AudioFile(filename) as source:
        audio = r.record(source)  # read the entire audio file
    try:
        text = r.recognize_sphinx(audio)
    except sr.UnknownValueError:
        print("Sphinx could not understand audio in file:{}".format(filename))
    except sr.RequestError as e:
        print("Sphinx error; {0}".format(e))
    
    file_metadata = process_text(text)
    file_metadata['duration'] = get_duration(filename)
    file_metadata['filename'] = os.path.split(filename)[1]
    save_json_to_disk(file_metadata)
    # name = os.path.splitext(filename)[0]
    

    # with open("{0}.json".format(name), "w") as outfile:
    #     json.dump(file_metadata, outfile)


# if __name__ == '__main__':
#     convert_wav_to_jsons('Recording.wav')
