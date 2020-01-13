#!/usr/bin/env python3

from arpabet import Arpabet
from encoding import ALL_SYMBOLS
from regex import SPACE_SPLIT
import ljspeech

# Per the LJSpeech website, these are some expected abbreviations:
# https://keithito.com/LJ-Speech-Dataset/
ABBREVIATIONS = {
  'capt.' : 'captain',
  'co.' : 'company',
  'col.' :  'colonel',
  'dr.' : 'doctor',
  'drs.' :  'doctors',
  'esq.' :  'esquire',
  'ft.' : 'fort',
  'gen.' :  'general',
  'hon.' :  'honorable',
  'jr' : 'junior',
  'jr.' : 'junior',
  'lt.' : 'lieutenant',
  'ltd.' :  'limited',
  'maj.' :  'major',
  'mr' :  'mister',
  'mr.' :  'mister',
  'mrs' : 'misess',
  'mrs.' : 'misess',
  'no.' : 'number',
  'rev.' :  'reverend',
  'sgt.' :  'sergeant',
  'st' : 'saint',
  'st.' : 'saint',
}

class Token:
  pass

class SpaceToken(Token):
  def encode(self):
    return ALL_SYMBOLS['Space']

  def __repr__(self):
    return 'Space'

class PunctuationToken(Token):
  def __init__(self, key):
    self._key = key

  def encode(self):
    return ALL_SYMBOLS[self._key]

  def __repr__(self):
    return 'Punctuation({})'.format(self._key)

class UnknownToken(Token):
  """Represents tokens that are not fully tokenized."""
  def __init__(self, payload):
    self._payload = payload

  def get(self):
    return self._payload

  def __repr__(self):
    return 'UnknownToken({})'.format(self._payload)

class WordToken(Token):
  def __init__(self, word):
    self._word = word

class ArpabetToken(Token):
  def __init__(self, polyphone: list):
    self._polyphone = polyphone.copy()

  def encode(self):
    encoded = []
    for phone in self._polyphone:
      if phone not in ALL_SYMBOLS:
        raise Exception('Not in symbols: "{}".'.format(phone))
      encoded.append(ALL_SYMBOLS[phone])
    return encoded

  def __repr__(self):
    return 'Arpabet({})'.format(self._polyphone)

class StartToken(Token):
  def encode(self):
    return ALL_SYMBOLS['StartToken']

  def __repr__(self):
    return 'Start'

class EndToken(Token):
  def encode(self):
    return ALL_SYMBOLS['EndToken']

  def __repr__(self):
    return 'End'

START_TOKEN = StartToken()
END_TOKEN = EndToken()
SPACE_TOKEN = SpaceToken()

PERIOD_TOKEN = PunctuationToken('Period')
COMMA_TOKEN = PunctuationToken('Comma')
QUESTION_TOKEN = PunctuationToken('Question')
EXCLAMATION_TOKEN = PunctuationToken('Exclamation')

ARPABET = Arpabet.load_file('./cmudict/cmudict-0.7b')


def filter_sentence(sentence_tokens, token_func):
  """
  token_func(token: string) -> []
  token_func takes in a token and returns a list of replacements
    - False means no-op / skip
    - Lists are for replacement:
      - empty list means delete the current item.
      - single item list means direct replacement
      - multi-item list means expansion
  """
  changed = False
  i = 0
  while i < len(sentence_tokens):
    token = sentence_tokens[i]
    if not isinstance(token, UnknownToken):
      i += 1
      continue
    results = token_func(token.get())
    if results == False:
      i += 1
      continue
    if isinstance(results, list):
      changed = True
      if not results:
        sentence_tokens.pop(i)
        continue
      j = i + 1
      for k in range(len(results)):
        token = results[k]
        if k == 0:
          sentence_tokens[i] = results[k]
        else:
          sentence_tokens.insert(j, results[k])
          j += 1
      i += len(results)
    else:
      raise Exception("Wrong return type {}: {}".format(type(results), results))
  return changed

def arpabet_filter(token):
  polyphone = ARPABET.get(token)
  if not polyphone:
    return False
  return [ArpabetToken(polyphone)]

def punctuation_filter(token):
  add_token = None
  if token.endswith('.'):
    return [
      UnknownToken(token[:-1]),
      PERIOD_TOKEN,
    ]
  elif token.endswith(',') \
      or token.endswith(';') \
      or token.endswith(':'):
    # NB: Not tracking colons or semicolons yet
    return [
      UnknownToken(token[:-1]),
      COMMA_TOKEN,
    ]
  elif token.endswith('?'):
    return [
      UnknownToken(token[:-1]),
      QUESTION_TOKEN,
    ]
  elif token.endswith('!'):
    return [
      UnknownToken(token[:-1]),
      EXCLAMATION_TOKEN,
    ]
  return False

def dash_arpabet_filter(token):
  splits = token.split('-')
  if len(splits) < 2:
    return False
  polyphone_list = []
  for split in splits:
    polyphone = ARPABET.get(split)
    if not polyphone:
      return False
    polyphone_list.append(polyphone)
  return [ArpabetToken(polyphone) for polyphone in polyphone_list]


def encode_sentence(sentence):
  sentence_tokens = sentence_to_tokens(sentence)
  encodings = []
  for token in sentence_tokens:
    if token in [START_TOKEN, END_TOKEN, SPACE_TOKEN]:
      encodings.append(token.encode())
      continue
    if isinstance(token, PunctuationToken):
      encodings.append(token.encode())
      continue
    if isinstance(token, ArpabetToken):
      encodings.extend(token.encode())
      continue
    encodings.append(token)

  # TODO
  reduced_encodings = []
  for e in encodings:
    if not isinstance(e, int):
      reduced_encodings.append(e)
  return reduced_encodings

def sentence_to_tokens(sentence):
  sentence_tokens = [START_TOKEN]

  # First pass. Tokenize sentence and handle some punctuation.

  splits = SPACE_SPLIT.split(sentence)

  for i in range(len(splits)):
    token = splits[i]

    # NB: No quotes or parens for now.
    token = token.replace('"', '')
    token = token.replace('(', '')
    token = token.replace(')', '')

    # TODO:
    #if token in ['PRS', 'Revill', 'Hosty']:
    #  continue

    #dehyphenated = token.split('-')
    #if len(dehyphenated) > 1:
    #  print(token, dehyphenated)
    #  continue

    sentence_tokens.append(UnknownToken(token))

    #if add_token:
    #  sentence_tokens.append(add_token)

    if i < len(splits) - 1:
      sentence_tokens.append(SPACE_TOKEN)

  sentence_tokens.append(END_TOKEN)

  # Second pass. Look up Arpabet.

  filter_sentence(sentence_tokens, arpabet_filter)
  filter_sentence(sentence_tokens, punctuation_filter)
  filter_sentence(sentence_tokens, arpabet_filter)
  filter_sentence(sentence_tokens, dash_arpabet_filter)


  """
  for i in range(len(sentence_tokens)):
    current = sentence_tokens[i]
    if not isinstance(current, UnknownToken):
      continue
    polyphone = ARPABET.get(current.get())
    if not polyphone:
      continue
    sentence_tokens[i] = ArpabetToken(polyphone)

  # Third pass. Correct.
  i = 0
  for i < len(sentence_tokens):
    current = sentence_tokens[i]
    if isinstance(current, UnknownToken):
      i += 1
      continue

    token = current.get()

    add_token = None
    if token.endswith('.'):
      token = token[:-1]
      add_token = PERIOD_TOKEN
    elif token.endswith(',') \
        or token.endswith(';') \
        or token.endswith(':'):
      # NB: Not tracking colons or semicolons yet
      token = token[:-1]
      add_token = COMMA_TOKEN
    elif token.endswith('?'):
      token = token[:-1]
      add_token = QUESTION_TOKEN
    elif token.endswith('!'):
      token = token[:-1]
      add_token = EXCLAMATION_TOKEN
  """


  return sentence_tokens

if __name__ == '__main__':
  result = encode_sentence("this is the song that never ends, it goes on and on.")

  sentences = ljspeech.read_file('/home/bt/datasets/LJSpeech-1.1/metadata.csv')

  good = 0
  bad = 0
  for sentence in sentences:
    result = encode_sentence(sentence)
    if not result:
      good += 1
    if result:
      bad += 1
      print(result)

  print('Good: {}'.format(good))
  print('Bad: {}'.format(bad))


