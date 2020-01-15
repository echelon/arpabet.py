arpabet.py
==========
Currently this is a bit messy. This repo conflates Arpabet, Integer encoding, and sentence tokenization.
It's meant to encode the LJSpeech dataset into integer-encodable Arpabet for training with Tacotron, etc.

There are a number of different script entrypoints, and all of the paths are hardcoded to my personal
machine and dev setup.

In the future I may separate these concerns and turn this into a proper library.

See my [arpabet.rs](https://github.com/echelon/arpabet.rs) crate 
for a better Rust version.

This focuses on integer encodings of phonemes.
