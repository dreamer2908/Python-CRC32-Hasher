Python-CRC32-Hasher
===================

### Introduction ###

This small program can be used to calculate CRC-32 hash from any files. It can detect CRC hashes from filenames and compares them with calculated values to verify files' integrity automatically. It can also add CRC hashes to filenames, and create SFV checksum files.

### Requirements ###

- Python 2.7 and later, or 3.3 and later
- A terminal

### Usage ###

Syntax: `python crc32.py [options] inputs`

Input can be individual files, and/or folders.

  Use Unix shell-style wildcard (*, ?, []) for the file name pattern.

Options:

  -addcrc                        Adds CRC to filenames
  
  -createsfv out.sfv             Creates a SFV file
  
  -r                             Also includes sub-folder

Examples:

  `python crc32.py "/home/yumi/Desktop/[FFF] Unbreakable Machine-Doll - 11 [A3A1001B].mkv"`
  
  `python crc32.py ~/Downloads`
  
  `python crc32.py ~/Downloads/*.mkv`
  
  `python crc32.py -createsfv checksums.sfv ~/Downloads /var/www/upload/*OP*  "[FFF] Unbreakable Machine-Doll - 11 [A3A1001B].mkv"`