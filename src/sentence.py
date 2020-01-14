#!/usr/bin/env python3

from arpabet import Arpabet
from encoding import ALL_SYMBOLS
from regex import SPACE_SPLIT
#import ljspeech

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
  # But also,
  'etc' : 'etcetera',
  'etc.' : 'etcetera',
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

class PluralArpabetToken(ArpabetToken):
  def __init__(self, polyphone: list):
    super().__init__(polyphone)

  def encode(self):
    encoded = super().encode()
    encoded.append(ALL_SYMBOLS['Z']) # TODO: Or 'S'
    return encoded

  def __repr__(self):
    return 'PluralArpabet({}-s)'.format(self._polyphone)

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

def unquote_filter(token):
  if token.endswith("',") or token.endswith(",'"): # NB: This is garbage
    token = token[:-2]
  if token.endswith(",”") or token.endswith("”,"): # NB: This is garbage
    token = token[:-2]
  if token.endswith("'"):
    token = token[:-1]
  if token.endswith("’"):
    token = token[:-1]
  if token.startswith("'"):
    token = token[1:]
  if token.startswith("“"):
    token = token[1:]
  polyphone = ARPABET.get(token)
  if not polyphone:
    return [UnknownToken(token)]
  return [ArpabetToken(polyphone)]

def plural_possessive_arpabet_filter(token):
  polyphone = None
  if token.endswith("'S") or token.endswith("'s"):
    token = token[:-2]
    polyphone = ARPABET.get(token)
  elif token.endswith("S'") or token.endswith("s'"):
    token = token[:-2]
    polyphone = ARPABET.get(token)
  elif token.endswith("S") or token.endswith("s"):
    token = token[:-1]
    polyphone = ARPABET.get(token)
  if not polyphone:
    return False
  return [PluralArpabetToken(polyphone)]

def punctuation_filter(token):
  add_token = None
  if token == '--':
    # TODO: For now we treat emdash as comma
    return [COMMA_TOKEN]
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
    if len(split) == 0:
      continue
    polyphone = ARPABET.get(split)
    if polyphone:
      polyphone_list.append(ArpabetToken(polyphone))
    else:
      polyphone_list.append(UnknownToken(split))
  return polyphone_list

def colon_arpabet_filter(token):
  splits = token.split(':')
  if len(splits) < 2:
    return False
  polyphone_list = []
  for split in splits:
    if len(split) == 0:
      continue
    polyphone = ARPABET.get(split)
    if polyphone:
      polyphone_list.append(ArpabetToken(polyphone))
    else:
      polyphone_list.append(UnknownToken(split))
  return polyphone_list

def undefined_abbreviation_filter(token):
  splits = token.split('.')
  if len(splits) < 2:
    return False
  letter_polyphones = [] # NB: List of lists
  for i in range(len(splits)):
    letter = splits[i]
    if i == len(splits) - 1 and len(letter) == 0:
      # Last split is empty string if abbreviation ends with period, eg 'a.b.c.'
      continue
    if len(letter) > 1 or len(letter) < 1:
      return False
    polyphone = ARPABET.get(letter)
    if not polyphone:
      return False
    letter_polyphones.append(polyphone)
  return_tokens = []
  for i in range(len(letter_polyphones)):
    polyphones = letter_polyphones[i]
    if i < len(letter_polyphones) - 1:
      return_tokens.append(ArpabetToken(polyphones))
    else:
      return_tokens.append(ArpabetToken(polyphones))
      return_tokens.append(SPACE_TOKEN)
  return return_tokens

def predefined_abbreviation_filter(token):
  token = token.lower()
  if token not in ABBREVIATIONS:
    return False
  expanded = ABBREVIATIONS[token]
  polyphone = ARPABET.get(expanded)
  if polyphone:
    return [ArpabetToken(polyphone)]
  else:
    return [UnknownToken(expanded)]

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

  return encodings

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

    # NB: These will get picked up by the abbreviation filter later
    token = token.replace('USSR', 'U.S.S.R')
    token = token.replace('PRS', 'P.R.S.')
    token = token.replace('FPCC', 'F.P.C.C.')
    token = token.replace('WDSU', 'W.D.S.U')
    token = token.replace('BBL', 'B.B.L.')
    token = token.replace('UV', 'U.V.')

    # NB: For a few examples in LJSpeech
    token = token.replace('ü', 'u')
    token = token.replace('viz.', 'viz')
    token = token.replace('Jebb', 'Jeb')

    sentence_tokens.append(UnknownToken(token))

    if i < len(splits) - 1:
      sentence_tokens.append(SPACE_TOKEN)

  sentence_tokens.append(END_TOKEN)

  # Second pass. Apply filters.

  filter_sentence(sentence_tokens, arpabet_filter)
  filter_sentence(sentence_tokens, predefined_abbreviation_filter)
  filter_sentence(sentence_tokens, punctuation_filter)
  filter_sentence(sentence_tokens, unquote_filter)
  filter_sentence(sentence_tokens, arpabet_filter)
  filter_sentence(sentence_tokens, dash_arpabet_filter)
  filter_sentence(sentence_tokens, colon_arpabet_filter)
  filter_sentence(sentence_tokens, undefined_abbreviation_filter)
  filter_sentence(sentence_tokens, predefined_abbreviation_filter)
  filter_sentence(sentence_tokens, punctuation_filter)
  filter_sentence(sentence_tokens, plural_possessive_arpabet_filter)
  filter_sentence(sentence_tokens, arpabet_filter)

  return sentence_tokens

if __name__ == '__main__':
  import ljspeech
  sentences = ljspeech.read_sentences('/home/bt/datasets/LJSpeech-1.1/metadata.csv')

  good = 0
  bad = 0
  unknown_symbols = {}
  for sentence in sentences:
    result = encode_sentence(sentence)
    if not result:
      good += 1
    if result:
      tokens = sentence_to_tokens(sentence)
      bad += 1
      for symbol in result:
        symbol = symbol.get()
        if symbol not in unknown_symbols:
          unknown_symbols[symbol] = 0
        unknown_symbols[symbol] += 1

  print('')
  for key, value in sorted(unknown_symbols.items(), key=lambda item: item[1]):
    print('{}: {}'.format(key, value))

  print('')
  print('Good: {}'.format(good))
  print('Bad: {}'.format(bad))
  print('Unknown Symbols: {}'.format(len(unknown_symbols.keys())))

# TODO: Add tests

