#!/usr/bin/python
# encoding: utf-8
#
# Copyright (C) 2013 Nguyen Hung Quy a.k.a dreamer2908
#
# Python CRC-32 Hasher is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2 of
# the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# TODO:
#  - Multi-thread support. Probably a dedicated thread for each hash type.
#  - Setting file.
#  - More output format.
#  - SHA3 support.
#  - Smart file path shortening

import sys, os, zlib, hashlib, shutil, re, time, struct, multiprocessing, math

programName = "Python CRC-32 Hasher"
version = "1.10"
author = "dreamer2908"
contributors = ["felipem775"]

addcrc = False
updatecrc = False
force = False
recursive = False
searchSubFolder = False
createsfv = False
showChecksumResult = True
waitBeforeExit = False
showFullPath = False
showFileInfo = False

sfvPath = "checksums.sfv"
sfvHeader = "; Generated by %s v%s " % (programName, version)
sfvContent = []
sfvPureAscii = True

enableCrc = True
enableMd4 = False
enableMd5 = False
enableSha1 = False
enableSha256 = False
enableSha512 = False
enableEd2k = False

st_total = 0
st_ok = 0
st_notok = 0
st_error = 0
st_notfound = 0
st_size = 0

pathList = []
defaultTimer = None
cpuCount = 1

debug = False
fag = []
terminalSupportUnicode = False

# According to my benchmark, without OS disk cache (or file much larger than the cache),
# 1 MiB of cache gives much higher speed than 100 KiB (59.247 MiB/s vs. 31.205 MiB/s),
# but consumes about 10% more CPU; 4 MiB of cache doesn't give any benefit over 1 MiB.
# With OS disk cache (files much smaller than the cache), speed: 100 KiB > 1 MiB > 4 MiB,
# CPU usage: 100 KiB < 1 MiB < 4 MiB. 1 MiB cache seems to be your choice.
# All tests were done on Windows 7 SP1 x64 and Python 3.3.3 x86.
# Additional tests on Python 2.7.4, 3.3.1, PyPy3 2.1 Beta 1, PyPy 2.2.1 (Mint 15 x64):
# 4 MiB cache gives about 3-5% more speed than 1 MiB does (119.707 vs. 111.884 MiB/s)
# PyPy3, surprisingly, give bad results: it consumes the whole core, but runs much
# slower (56.497 MiB/s). PyPy gives less but still bad results (85.958 MiB/s).
# Maybe they implenebted zlib in pure Python?
# Changed to 2 MiB cache. Slightly better on fast disks.

# For ED2K, see http://wiki.anidb.info/w/Ed2k-hash
# ED2K checked agains rHash (red) and RapidCRC (blue - alternative reference)
# This program uses red method because it's more common
def hasher(fileName):
	fileSize = os.path.getsize(fileName)
	blockSize = 2 * 1024 * 1024

	crc = 0
	md4 = hashlib.new('md4')
	md5 = hashlib.md5()
	sha1 = hashlib.sha1()
	sha256 = hashlib.sha256()
	sha512 = hashlib.sha512()

	ed2kHash = bytearray()
	ed2kChunkSize = 9728000
	ed2kChunkHash = hashlib.new('md4')
	ed2kChunkRemain = ed2kChunkSize

	try:
		fd = open(fileName, 'rb')
		while True:
			buffer = fd.read(blockSize)
			if len(buffer) == 0: # EOF or file empty. return hashes
				fd.close()

				if ed2kChunkRemain < ed2kChunkSize:
					ed2kHash += ed2kChunkHash.digest()
				ed2kEndHash = hashlib.new('md4')
				if (fileSize % ed2kChunkSize == 0):
					ed2kHash += ed2kEndHash.digest()
				if fileSize >= ed2kChunkSize:
					ed2kEndHash.update(ed2kHash)
					ed2kHash = ed2kEndHash.hexdigest()
				elif fileSize > 0:
					ed2kHash = ed2kChunkHash.hexdigest()
				else:
					ed2kHash = ed2kEndHash.hexdigest()

				if sys.version_info[0] < 3 and crc < 0:
					crc += 2 ** 32
				return crc, md4.hexdigest().upper(), md5.hexdigest().upper(), sha1.hexdigest().upper(), sha256.hexdigest().upper(), sha512.hexdigest().upper(), ed2kHash.upper(), False

			if enableCrc: crc = zlib.crc32(buffer, crc)
			if enableMd4: md4.update(buffer)
			if enableMd5: md5.update(buffer)
			if enableSha1: sha1.update(buffer)
			if enableSha256: sha256.update(buffer)
			if enableSha512: sha512.update(buffer)

			if enableEd2k:
				dataLen = len(buffer)
				if dataLen < ed2kChunkRemain:
					ed2kChunkHash.update(buffer)
					ed2kChunkRemain -= dataLen
				elif dataLen == ed2kChunkRemain:
					ed2kChunkHash.update(buffer)
					ed2kHash += ed2kChunkHash.digest()
					ed2kChunkRemain = ed2kChunkSize
					ed2kChunkHash = hashlib.new('md4')
				else:
					ed2kChunkHash.update(buffer[0:ed2kChunkRemain])
					ed2kHash += ed2kChunkHash.digest()
					ed2kChunkHash = hashlib.new('md4')
					dataRemain = dataLen - ed2kChunkRemain
					chunkHashRepeat = int(math.floor(dataRemain / ed2kChunkSize))
					for i in range(chunkHashRepeat):
						ed2kChunkHash.update(buffer[ed2kChunkRemain + i * ed2kChunkSize : ed2kChunkRemain + i * ed2kChunkSize + ed2kChunkSize])
						ed2kHash += ed2kChunkHash.digest()
						ed2kChunkHash = hashlib.new('md4')
						hashCount += 1
					dataRemain = dataRemain - chunkHashRepeat * ed2kChunkSize
					ed2kChunkHash.update(buffer[-dataRemain:])
					ed2kChunkRemain = ed2kChunkSize - dataRemain

	except Exception as e:
		if sys.version_info[0] < 3:
			error = unicode(e)
		else:
			error = str(e)
		return 0, '', '', '', '', '', '', error

# From version 2.6, the return value is in the range [-2**31, 2**31-1],
# and from ver 3.0, the return value is unsigned and in the range [0, 2**32-1]
# This works on both versions, confirmed by checking over 33 different files
def hasher_s(fileName):
	iHash, md4, md5, sha1, sha256, sha512, ed2k, error = hasher(fileName)
	if sys.version_info[0] < 3 and iHash < 0:
		iHash += 2 ** 32
	sHash = '%08X' % iHash
	return sHash, md4, md5, sha1, sha256, sha512, ed2k, error

# In-used CRC-32 pattern: 8 characters of hexadecimal, separated from the rest
# by some certain "special" characters. It's usually at the end of file name,
# so just take the last one; there shouldn't more than one anyway.
def detectCRC(fileName):
	crc = ""
	found = False
	reCRC = re.compile(r'[A-Fa-f0-9]{8}')
	separator1 = "([_. "
	separator2 = ")]_. "
	for match in reCRC.finditer(fileName):
		start = match.start()
		end = match.end()
		if ((start == 0 or fileName[start - 1] in separator1)
			and (end == len(fileName) or fileName[end + 1] in separator2)):
			crc = fileName[start:end]
			found = True
	return found, crc

def processFile(fileName, fromFolder = False):
	# Not gonna trust the caller completely
	if not os.path.isfile(fileName):
		if not fromFolder:
			print('%s    Not found or invalid!' % path)
		fag.append(fileName)
		return

	# In Python 2, decode the path to unicode string
	# In python 3, it's already unicode, so don't
	if sys.version_info[0] < 3 and hasattr(fileName, 'decode'):
		fileName = fileName.decode(sys.getfilesystemencoding())

	sHash, md4, md5, sha1, sha256, sha512, ed2k, error = hasher_s(fileName)
	newName = fileName

	fileSize = os.path.getsize(fileName)

	global st_total, st_ok, st_notok, st_notfound, st_size, st_error
	if not error:
		try:
			st_size += fileSize
		except:
			doNothing = 1
	st_total += 1

	found, crc = detectCRC(fileName)

	if error:
		result = error
		st_error += 1
	elif sHash in fileName.upper():
		result = "File OK!"
		st_ok += 1
	elif found and not updatecrc:
		result = "File not OK! %s found in filename." % crc
		st_notok += 1
	else:
		if addcrc:
			namae, ext = os.path.splitext(fileName)
			newName = namae + "[%s]" % sHash + ext
			try:
				shutil.move(fileName, newName)
				result = "CRC added!"
			except:
				result = "Renaming failed!"
				newName = fileName
		elif updatecrc:
			namae, ext = os.path.splitext(fileName)
			newName = namae.replace(crc,sHash) + ext
			try:
				shutil.move(fileName, newName)
				result = "CRC updated!"
			except Exception as e:
				result = "Renaming failed!"
				newName = fileName
		else:
			result = "CRC not found!"
		st_notfound += 1

	# deal with terminal encoding mess
	global terminalSupportUnicode
	if not terminalSupportUnicode:
		fileName = removeNonAscii(fileName)

	name2Show = fileName
	if not showFullPath:
		path, name2Show = os.path.split(fileName)

	if showChecksumResult:
		if not showFileInfo:
			print('%s    %s    %s' % (name2Show, sHash, result))
		else:
			print('Filename: %s' % name2Show)
			print('Size: %d bytes (%s)' % (fileSize, byteToHumanSize(fileSize)))
			print('CRC-32: %s' % sHash)
		if not error:
			if enableMd4: print('MD4: %s' % md4)
			if enableMd5: print('MD5: %s' % md5)
			if enableSha1: print('SHA-1: %s' % sha1)
			if enableSha256: print('SHA-256: %s' % sha256)
			if enableSha512: print('SHA-512: %s' % sha512)
			if enableEd2k: print('ED2K: %s' % ed2k)
		if showFileInfo: print(' ')

	# Append this file info to sfvContent. Yes, use newName as it's up-to-date
	# Remember to use "global" to access external variable!!
	path, name = os.path.split(newName)
	if not error:
		global sfvContent
		sfvContent.append('\n')
		sfvContent.append(name)
		sfvContent.append(' ')
		sfvContent.append(sHash)

		global sfvPureAscii
		if sfvPureAscii:
			sfvPureAscii = isPureAscii(name)

def processFolderv2(path):

	pattern = '*'
	usePattern = False

	# Check if input is an existing file
	if os.path.isfile(path):
		processFile(path, False)
	# Check if input is an existing folder.
	# If not, split the path and check if "folder" exists
	if not os.path.isdir(path):
		folder, pattern = os.path.split(path)
		if os.path.isdir(folder) and ('*' in pattern or '?' in pattern or ('[' in pattern and ']' in pattern)):
			path = folder
			usePattern = True
		elif folder == '':
			path = os.getcwd()
			usePattern = True
		else:
			print('%s    Not found or invalid!' % path)
			return

	for (dirpath, dirnames, filenames) in os.walk(path):
		if usePattern:
			filenames = patternMatching(filenames, pattern)
		for fname in sorted(filenames):
			processFile(os.path.join(dirpath, fname), True)
		if (not usePattern and not recursive) or (usePattern and not searchSubFolder):
			break

def patternMatching(filenames, pattern):

	#pattern = 'C?*apter?.txt'
	matchingFname = []

	if not ('*' in pattern or  '?' in pattern):
		return []

	def convertPatternToRegex(pattern):
		specialChars = '.^$*+?{}, \\[]|():=#!<'
		regex = ''

		# convert to unicode string first
		# just assume all utf-8 -- this file is in this encoding anyway
		if hasattr(pattern, 'decode'):
			pattern = pattern.decode('utf-8')

		# parse pattern
		for i in range(len(pattern)):
			char = pattern[i]
			if char == '*' or char == '?':
				if char == '?':
					regex += '.'
				elif char == '*':
					regex += '(.*)'
			else:
				# escape stuff
				if char in specialChars:
					regex += '\\'
				regex += char
				if i == len(pattern) - 1: # end of pattern. Fixed a bug that made pattern blablah*.mkv match blablah.mkv.pass
					regex += '$'

		return regex

	regPattern = convertPatternToRegex(pattern)
	if debug:
		print(regPattern)
	regObject = re.compile(regPattern)

	for fname in filenames:
		match = regObject.match(fname)
		if match:
			matchingFname.append(fname)

	if debug:
		print(matchingFname)

	return matchingFname

def byteToHumanSize(size):
	if size >= 1000 * 1024 * 1024:
		return '%0.3f GiB' % (size / (1024 ** 3))
	elif size >= 1000 * 1024:
		return '%0.3f MiB' % (size / 1024 ** 2)
	elif size >= 1000:
		return '%0.3f KiB' % (size / 1024)
	else:
		return '%s bytes' % size

# Calculate CPU time and average CPU usage
def getCpuStat(cpuOld, cpuNew, timeOld, timeNew):
	cpuTime = float(cpuNew) - float(cpuOld)
	elapsedTime = float(timeNew) - float(timeOld)

	if cpuTime == 0:
		cpuTime = 0.001
		elapsedTime = cpuTime
	if elapsedTime == 0:
		elapsedTime = cpuTime

	cpuPercentage = 100 * cpuTime / elapsedTime

	# Devide CPU percentage by the number of CPUs if it's Windows
	# to match reference system monitors (Windows Task Manager, etc.)
	if sys.platform == 'win32':
		cpuPercentage = cpuPercentage / cpuCount

	return cpuTime, cpuPercentage, elapsedTime

# Detects the number of CPUs on a system
def detectCPUs():
	cpu_count = multiprocessing.cpu_count()
	if debug:
		print('CPU count = %d' % cpu_count)
	return cpu_count

# Test unicode support
def checkUnicodeSupport():
	try:
		text = u'「いなり、こんこん、恋いろは。」番宣ＰＶ'.encode(sys.stdout.encoding)
	except:
		return False
	return True

def isPureAscii(text):
	for c in text:
		code = ord(c)
		if code > 127:
			return False
	return True

# Converts text into UTF-16LE bytes
# Nah, writing this instead of using the built-in one just for fun
def toUTF16leBytes(text):
	encodedBytes = bytearray()
	for c in text:
		encodedBytes += toUTF16leBytesSub(c)
	return encodedBytes

# Encodes a single character
# See RFC 2781, UTF-16, an encoding of ISO 10646 http://www.ietf.org/rfc/rfc2781.txt
# Reference encoder: Unicode Code Converter http://rishida.net/tools/conversion/
# Tests done with Notepad++
def toUTF16leBytesSub(c):
	U = ord(c)
	if U < 0x10000:
		return struct.pack("<H", U)
	else:
		U = U - 0x10000
		W1 = 0xD800
		W2 = 0xDC00
		UH = U >> 10
		UL = U - (UH << 10)
		W1 ^= UH
		W2 ^= UL
		return struct.pack('<HH', W1, W2)

def toAsciiBytes(text):
	asciiText = removeNonAscii(text)
	try:
		return asciiText.encode('ascii')
	except:
		return asciiText

# Kills non-ASCII characters
def removeNonAscii(original):
	result = ''
	for c in original:
		code = ord(c)
		if code < 128:
			result += c
		else:
			result += '?'
	return result

# Parse paramenters
def parseParams():
	global pathList, addcrc, updatecrc, createsfv, sfvPath, force, recursive, searchSubFolder, showChecksumResult, showFileInfo, showFullPath
	global enableMd5, enableSha1, enableSha256, enableSha512, enableEd2k, enableCrc, enableAll, enableMd4
	global debug, waitBeforeExit

	pathList = []
	treatAllAsFilenames = False
	i = 1
	while i < len(sys.argv):
		arg = sys.argv[i]
		if not treatAllAsFilenames and arg.startswith('--'):
			arg = arg[2:].lower()

			if arg == "addcrc":
				addcrc = True
			elif arg == "updatecrc":
				updatecrc = True
			elif arg == "createsfv" and i < len(sys.argv) - 1:
				createsfv = True
				sfvPath = sys.argv[i+1]
				i += 1
			elif arg == "force":
				force == True
			elif arg == "recursive":
				recursive = True
			elif arg == "searchsubfolder":
				searchSubFolder = True
			elif arg == "quiet":
				showChecksumResult = False
			elif arg == 'debug':
				debug = True
			elif arg == "wait":
				waitBeforeExit = True
			elif arg == "md5":
				enableMd5 = True
			elif arg == "sha1":
				enableSha1 = True
			elif arg == "sha2":
				enableSha256 = True
				enableSha512 = True
			elif arg == "sha256":
				enableSha256 = True
			elif arg == "sha512":
				enableSha512 = True
			elif arg == "ed2k":
				enableEd2k = True
			elif arg == "all":
				enableMd4 = True
				enableMd5 = True
				enableSha1 = True
				enableSha256 = True
				enableSha512 = True
				enableEd2k = True
				enableCrc = True
			elif arg == "most":
				enableCrc = True
				enableMd5 = True
				enableSha1 = True
				enableSha256 = True
				enableSha512 = True
				enableEd2k = True
			elif arg == 'inputs':
				treatAllAsFilenames = True
			elif arg == 'showfileinfo':
				showFileInfo = True
			elif arg == 'showfullpath':
				showFullPath = True
		elif not treatAllAsFilenames and arg.startswith('-'):
			arg = arg[1:].lower()

			if arg == "c" and i < len(sys.argv) - 1:
				createsfv = True
				sfvPath = sys.argv[i+1]
				i += 1
			elif arg == "f":
				force == True
			elif arg == "r":
				recursive = True
			elif arg == "s":
				searchSubFolder = True
			elif arg == "d":
				debug = True
			elif arg == "w":
				waitBeforeExit = True
			elif arg == "md4":
				enableMd4 = True
			elif arg == "md5":
				enableMd5 = True
			elif arg == "sha1":
				enableSha1 = True
			elif arg == "sha2":
				enableSha256 = True
				enableSha512 = True
			elif arg == "sha256":
				enableSha256 = True
			elif arg == "sha512":
				enableSha512 = True
			elif arg == "ed2k":
				enableEd2k = True
			elif arg == "a":
				enableMd4 = True
				enableMd5 = True
				enableSha1 = True
				enableSha256 = True
				enableSha512 = True
				enableEd2k = True
				enableCrc = True
			elif arg == "m":
				enableMd5 = True
				enableSha1 = True
				enableSha256 = True
				enableSha512 = True
				enableEd2k = True
				enableCrc = True
			elif arg == 'i':
				treatAllAsFilenames = True
			elif arg == "q":
				showChecksumResult = False
			elif arg == 'fi':
				showFileInfo = True
			elif arg == 'fp':
				showFullPath = True
		else:
			pathList.append(arg)
		i += 1

def createChecksumFiles():
	global createsfv, sfvPath, sfvPureAscii, sfvContent

	if createsfv:
		try:
			sfvFile = open(sfvPath, 'wb')
			# encode to UTF-16LE if there is any non-ascii character
			if sfvPureAscii:
				for content in sfvContent:
					sfvFile.write(toAsciiBytes(content))
			else:
				# write BOM
				sfvFile.write(struct.pack("<B", 255))
				sfvFile.write(struct.pack("<B", 254))
				for content in sfvContent:
					sfvFile.write(toUTF16leBytes(content))
			sfvFile.close()
		except:
			print("Couldn't open \"%s\" for writing!" % sfvPath)

def printReadme():
	# Print user manual
	print("%s v%s by %s\n" % (programName, version, author))
	print("Syntax: python crc32.py [options] inputs\n")
	print("Input can be individual files, and/or folders.")
	print("  Use Unix shell-style wildcard (*, ?) for the filename pattern.\n")
	print("Options:")
	print("  --addcrc                        Add CRC-32 to filenames.")
	print("  --updatecrc                     Update CRC-32 to filenames.")
	print("  -c | --createsfv out.sfv        Create a SFV file.")
	print("  -r | --recursive                Also include sub-folder.")
	print("  -s | --searchsubfolder          Also search sub-folder for matching filenames.")
	print("  --<hashtype>                    Enable the specified hash type.")
	print("  -m | --most                     Enable CRC-32, MD5, SHA-1, SHA-256, SHA-512, and ED2K.")
	print("  -a | -all                       Enable all supported hashes.")
	print("  -i | --inputs                   Treat all remaining paramenters as filenames.\n")
	print("  Currently supported hash types: CRC-32, MD4, MD5, SHA-1, SHA-256, SHA-512, ED2K.")
	print("  Please use lowercase and no hyphen for hash types. CRC-32 is enabled by default.\n")
	print("Examples:")
	print('  python crc32.py \"/home/yumi/Desktop/[FFF] Unbreakable Machine-Doll - 11 [A3A1001B].mkv\"')
	print('  python crc32.py --md5 --sha1 ~/Desktop ~/Downloads/*.mkv \"/var/www/upload/Ep ??.mkv\"')
	print('  python crc32.py --sha512 --ed2k -c checksums.sfv -s --addcrc /var/www/upload/*.mp4 ')

def checkSanity():
	global terminalSupportUnicode, debug, pathList

	if debug:
		print('terminalSupportUnicode = %s' % terminalSupportUnicode)

	if len(pathList) < 1: # no imput
		printReadme()
		sys.exit()

def initStuff():
	global defaultTimer, terminalSupportUnicode, cpuCount

	terminalSupportUnicode = checkUnicodeSupport()

	# Stats setup
	if sys.platform == 'win32':
	    # On Windows, the best timer is time.clock
		# From Python 3.8, time.clock() has been replaced with time.perf_counter()
		if sys.version_info[0] < 3:
			defaultTimer = time.clock
		else:
			defaultTimer = time.perf_counter
	else:
	    # On most other platforms the best timer is time.time
	    defaultTimer = time.time

	cpuCount = detectCPUs()

def doStuff():
	startTime = defaultTimer()
	uOld, sOld, cOld, c, e = os.times()

	sfvContent.append(sfvHeader)
	sfvPureAscii = True

	# Process files and folders
	print('Processing %d input(s)...\n' % len(pathList))
	if debug:
		print(pathList)

	for path in pathList:
		if os.path.isfile(path):
			processFile(path) # processFolderv2 also works with file, but this saves some cpu circles
		elif os.path.isdir(path):
			processFolderv2(path)
		elif (path.endswith(os.sep) or path.endswith("'") or path.endswith('"')) and os.path.isdir(path[:-1]):
			processFolderv2(path[:-1])
		elif ("*" in path) or ("?" in path): # depreciated
		 	processFolderv2(path)
		else:
			processFolderv2(path)

	endTime = defaultTimer()

	createChecksumFiles()

	# Print stats
	uNew, sNew, cNew, c, e = os.times()
	cpuTime, cpuPercentage, elapsed = getCpuStat(uOld + sOld, uNew + sNew, startTime, endTime)

	print("\nTotal: %d. OK: %d. Not OK: %d. CRC not found: %d. Error: %d." % (st_total, st_ok, st_notok, st_notfound, st_error))

	speed = st_size * 1.0 / elapsed
	print("Speed: %s read in %0.3f sec =>  %s/s." % (byteToHumanSize(st_size), elapsed, byteToHumanSize(speed)))

	print('CPU time: %0.3f sec => Average: %0.2f %%.' % (cpuTime, cpuPercentage))

	# So many bugs
	if debug:
		print(' ')
		print('Terminal supporting unicode = %s' % terminalSupportUnicode())
		print('fag = %r' % fag)

	if waitBeforeExit:
		print(' ')
		if sys.version_info[0] < 3:
			dummy = raw_input('Press Enter To Exit...')
		else:
			dummy = input('Press Enter To Exit...')


initStuff()
parseParams()
checkSanity()
doStuff()
