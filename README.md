Python-CRC32-Hasher
===================

### Introduction ###

This small program can be used to calculate various types of hash from any files (CRC-32, MD5, SHA1, SHA2, ED2K). It can detect CRC hashes from filenames and compares them with calculated values to verify files' integrity automatically. It can also add CRC-32 hashes to filenames, and create SFV checksum files.

### Requirements ###

- Python 2.7 and later, or 3.3 and later [recommended]
- A terminal

### Usage ###

Syntax: `python crc32.py [options] inputs`

Input can be individual files, and/or folders. Use Unix shell-style wildcard (*, ?) for the filename pattern.

Options:

 - --addcrc: Adds CRC to filenames  
 - --createsfv out.sfv: Creates a SFV file  
 - --r: Also includes sub-folder
 - --s: Also search sub-folder for matching filenames
 - --md5: Calculate MD5 hash
 - --sha1: Calculate SHA1 hash
 - --sha*: Calculate SHA2-224/256/384/512 hashes
 - --ed2k: Calculate ED2K hash
 - --all: Calculate all supported hashes
 
 CRC-32 calculation is enabled by default

Examples:

 - `python crc32.py "./[FFF] Unbreakable Machine-Doll - 11 [A3A1001B].mkv"`  
 - `python crc32.py ~/Downloads`  
 - `python crc32.py ~/Downloads/*.mkv`  
 - `python crc32.py --md5 --sha1 --sha256 --ed2k ~/Anime/*.mkv --s`
 - `python crc32.py --createsfv checksums.sfv ~/Downloads /var/www/upload/*OP*  "[FFF] Unbreakable Machine-Doll - 11 [A3A1001B].mkv"`
 
### Todo ###
 
 - Import/Export list of hashes
 - Setting file.