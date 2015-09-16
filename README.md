Python CRC32 Hasher
===================

### Introduction ###

Python CRC-32 Hasher is a console utility for calculating and verifying various types of hash from any files (CRC-32, MD4, MD5, SHA1, SHA256, SHA512, ED2K). A recommended usage is putting it in your file manager context menu, as I put it in a custom action in Thunar.

### Features ###

- Optimised for fansub releases: It automatically reads CRC-32 hashes from filenames and compares with the actual hash to verify files' integrity. Adding CRC-32 hashes to filenames automatically is supported.
- Output in a predefined formats (only sfv currently).
- Supports filename patterns (* and ?) even when working with terminal that doesn't.
- Ability to process directories recursively.
- Portability: the program works the same under any platform as long as Python is installed (Linux, *BSD, Solaris, Mac OS, or Windows).
- Written in Python, small in size, fast, open source.

### Requirements ###

- Python 2.7+, or 3.3+ [recommended]
- A terminal

### Usage ###

Syntax: `python crc32.py [options] inputs`

Input can be individual files, and/or folders. Use * (any string), ? (one character) for the filename pattern.

Options:

 - `--addcrc`: Adds CRC to filenames
 - `-c out.sfv` or `--createsfv out.sfv`: Creates a SFV file
 - `-r` or `--recursive`: Also includes sub-folder
 - `-s` or  --searchsubfolder : Also search sub-folder for matching filenames
 - `--hashtype`: Enable the specified hash type. Currently supported hash types: CRC-32, MD4, MD5, SHA-1, SHA-256, SHA-512, ED2K. Please use lowercase and no hyphen for hash types. CRC-32 is enabled by default and can't be disabled.
 - `-m` or `--most`: Enable CRC-32, MD5, SHA-1, SHA-256, SHA-512, and ED2K.
 - `-a` or `--all`: Enable all supported hashes.
 - `-i` or `--inputs`: Treat all remaining paramenters as filenames.

Examples:

 - `python crc32.py "/home/yumi/Desktop/[FFF] Unbreakable Machine-Doll - 11 [A3A1001B].mkv"`
 - `python crc32.py --md5 --sha1 ~/Desktop ~/Downloads/*.mkv "/var/www/upload/Ep ??.mkv"`
 - `python crc32.py --sha512 --ed2k -c checksums.sfv -s --addcrc /var/www/upload/*.mp4 `

### Todo ###

 - Import/Export list of hashes.
 - Setting file.
 - Multi-thread support. Probably a dedicated thread for each hash type.
 - SHA3 support.
