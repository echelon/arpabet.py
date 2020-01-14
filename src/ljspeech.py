#!/usr/bin/env python3

"""
Read the LJSpeech dataset CSV
"""

import csv

from sentence import encode_sentence

def read_sentences(filename):
  sentences = []
  with open(filename, 'r') as file_handle:
    reader = csv.reader(file_handle, delimiter='|')
    for row in reader:
      if len(row) != 3:
        #print("Problems with row {}".format(row))
        continue
      sentences.append(row[2])
  return sentences

def filter_file(input_filename, output_filename):
  with open(input_filename, 'r') as infile:
    with open(output_filename, 'w') as outfile:
      reader = csv.reader(infile, delimiter='|', quoting=csv.QUOTE_NONE)
      writer = csv.writer(outfile, delimiter='|', quoting=csv.QUOTE_NONE, quotechar='')
      filter_file_csv(reader, writer)

def filter_file_csv(csv_reader, csv_writer):
  success_count = 0
  failure_count = 0

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
        passes = False
        break

    if not passes:
      failure_count += 1
      continue

    try:
      csv_writer.writerow([wav, original_sentence, expanded_sentence])
    except:
      print('Failure: {}'.format(row))
    success_count +=1

  print('Success count: {}'.format(success_count))
  print('Failure count: {}'.format(failure_count))



if __name__ == '__main__':
  input_file = '/home/bt/datasets/LJSpeech-1.1/metadata.csv'
  output_file = '/home/bt/datasets/LJSpeech-1.1/filtered.csv'
  filter_file(input_file, output_file)
