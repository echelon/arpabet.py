#!/usr/bin/env python3

from regex import COMMENT_REGEX
from regex import PHONEME_REGEX
from regex import SPACE_SPLIT

class Arpabet:
  def __init__(self, mappings: dict):
    self._mappings = mappings

  def get(self, word: str):
    word = word.upper()
    return self._mappings.get(word)

  @classmethod
  def load_file(cls, filename: str):
    with open(filename, 'r') as file_handle:
      mappings = {}
      for line in file_handle:
        line = line.strip()
        if COMMENT_REGEX.match(line):
          continue

        matches = PHONEME_REGEX.match(line)
        if not matches:
          continue

        word = matches.group(1)
        polyphone = matches.group(2)
        if not word or not polyphone:
          continue

        phonemes = SPACE_SPLIT.split(polyphone.strip())

        if not phonemes:
          continue

        mappings[word] = phonemes

    return Arpabet(mappings)

if __name__ == '__main__':
  arpabet = Arpabet.load_file('./cmudict/cmudict-0.7b')


