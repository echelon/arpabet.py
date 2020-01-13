#!/usr/bin/env python3

"""
Read the LJSpeech dataset CSV
"""

import csv

def read_file(filename):
  sentences = []
  with open(filename, 'r') as file_handle:
    reader = csv.reader(file_handle, delimiter='|')
    for row in reader:
      if len(row) != 3:
        #print("Problems with row {}".format(row))
        continue
      sentences.append(row[2])
  return sentences

if __name__ == '__main__':
  sentences = read_file('/home/bt/datasets/LJSpeech-1.1/metadata.csv')
  for s in sentences:
    print(s)
