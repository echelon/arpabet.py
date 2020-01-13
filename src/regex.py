import re

# Regex for phonemes with match groups
PHONEME_REGEX = re.compile(r"^([\w\-\(\)\.']+)\s+([^\s].*)\s*$")

# Regex for comments
COMMENT_REGEX = re.compile(r"^;;;\s+")

# Regex for splitting
SPACE_SPLIT = re.compile("\s+")
