#!/usr/bin/env python3

"""
Prepare Tacotron training data
"""

import csv
import os
import random

from sentence import encode_sentence

VALIDATION_THRESHOLD = 0.1

def prepare_training_data(input_filename, training_output_filename, validation_output_filename, wav_directory=None):
  with open(input_filename, 'r') as infile:
    with open(training_output_filename, 'w') as training_outfile:
      with open(validation_output_filename, 'w') as validation_outfile:
        reader = csv.reader(infile, delimiter='|', quoting=csv.QUOTE_NONE)
        training_writer = csv.writer(training_outfile, delimiter='|', quoting=csv.QUOTE_NONE, quotechar='')
        validation_writer = csv.writer(validation_outfile, delimiter='|', quoting=csv.QUOTE_NONE, quotechar='')
        prepare_training_csvs(reader, training_writer, validation_writer, wav_directory)

def prepare_training_csvs(csv_reader, training_csv_writer, validation_csv_writer, wav_directory=None):
  """
  Read LJSpeech metadata.csv, filter out things we can't parse, then save the
  good (passing) examples into a new file.
  """
  success_count = 0
  failure_count = 0
  training_count = 0
  validation_count = 0

  for row in csv_reader:
    if len(row) != 3:
      failure_count += 1
      print('Problem row: {}'.format(row))
      continue
    wav = row[0]
    original_sentence = row[1]
    expanded_sentence = row[2]
    encoded_sentence = encode_sentence(expanded_sentence)

    passes = True
    for token in encoded_sentence:
      if not isinstance(token, int):
        # If we can't encode the entire sentence, don't use it.
        # We can improve our sentence tokenizing to get a bettter pass rate,
        # but we're already in the long tail zone of deminishing returns.
        passes = False
        break

    if not passes:
      failure_count += 1
      continue

    training = True
    if random.random() < VALIDATION_THRESHOLD:
      training = False

    if not wav.endswith('.wav'):
      # Tacotron expects filenames. LJS does not include extensions.
      wav += '.wav'

    if wav_directory:
      wav = os.path.join(wav_directory, wav)

    try:
      # Here we only save two of the three columns back, because that's what Tacotron expects
      if training:
        training_csv_writer.writerow([wav, expanded_sentence])
        training_count += 1
      else:
        validation_csv_writer.writerow([wav, expanded_sentence])
        validation_count += 1
    except:
      print('Failure: {}'.format(row))
    success_count +=1

  print('Success count: {}'.format(success_count))
  print('Failure count: {}'.format(failure_count))
  print('Training count: {}'.format(training_count))
  print('Validation count: {}'.format(validation_count))

  validation_percent = validation_count / (validation_count + training_count)
  print('Validation percent: {}'.format(validation_percent))

if __name__ == '__main__':
  input_file = '/home/bt/datasets/LJSpeech-1.1/metadata.csv'
  training_file = '/home/bt/datasets/LJSpeech-1.1/filtered_training.csv'
  validation_file = '/home/bt/datasets/LJSpeech-1.1/filtered_validation.csv'
  wav_directory = '/home/bt/datasets/LJSpeech-1.1/wavs'

  prepare_training_data(input_file, training_file, validation_file, wav_directory)

