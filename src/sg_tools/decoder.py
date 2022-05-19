# -*- coding: utf8 -*-
"""
Decoder functions for romheader module.

Some segments are validated. If a segment of data appears invalid, ValidationError is raised.
"""

import struct
import sys
from struct import pack

if sys.version[0] in '3':
    # pylint: disable-next=invalid-name
    unicode = str


class ValidationError(Exception):
    """Exception class for validating the image header for decoding."""

    def __init__(self, fatal=False):
        self.message = "Invalid image header"
        Exception.__init__(self, self.message)
        if fatal:
            raise SystemExit(1)


def decode(option, segment):
    """
    Decode based on field string given.

    Keywords:
        option -- string
        segment -- raw tuple of bytes
    """
    functions = {"ascii": string, "checksum": raw, "device": peripheral, "modem": modem,
                 "range": alloc, "extra": sram, "region": locale, "prod": raw_be,
                 "version": nibble_lsb, "m3region": m3locale, "size": sizes}

    if option in ["system", "copyright", "domestic", "export", "serial"]:
        option = "ascii"
    if option in ["romrange", "ramrange"]:
        option = "range"
    result = functions[option](segment)

    if option in "ascii":
        if not isinstance(result, (str, unicode)):
            raise ValidationError()
    return result


# Data manipulation
def join(mid, end):
    """
    Join hex value parts to create an offset value.

    Keywords:
        mid -- string
        end -- string
    Join leading hex symbol with two hex representations of a byte, and convert to integer.
    """
    return int("0x" + mid + end, 16)


def nibble_lsb(byte):
    """Return the least significant nibble of a byte in a tuple."""
    return raw(byte)[1]


def nibble_msb(byte):
    """Return the most significant nibble of a byte in a tuple."""
    return raw(byte)[0]


def raw(segment):
    """
    Return the raw hex value of the raw data segment.

    Keyword:
        segment -- tuple of bytes
    Convert raw tuple byte array to a string representation of a hex value without leading hex
    symbol.
    """
    return ''.join([hex(x)[2:].zfill(2) for x in segment])


def raw_be(segment):
    """
    Return the raw hex value of the raw data segment, in big-endian order.

    Keyword:
        segment -- tuple of bytes
    """
    code = nibble_msb(segment[-1:])
    for byte in segment[-2::-1]:
        code = code + hex(byte)[2:].zfill(2)
    if code[0] == "0":
        code = code[1:]
    return code


def string(segment):
    """
    Return the locale-decoded string value of the raw data segment.

    Keyword:
        segment -- tuple of bytes
    Convert raw byte array segment to a readable string. Decode any characters encoded in
    the CP-932 character set to the environment's locale. If a decode error occurs, pass
    through all characters undecoded.
    """
    try:
        return pack("B"*len(segment), *segment).decode("cp932")
    except (UnicodeDecodeError, LookupError):
        return pack("B"*len(segment), *segment)
    except struct.error:
        print("FATAL: Byte array tuple required")
        return None


def bintostr(key):
    """Decode region value from a hex value key."""
    value = ""
    if key & 0x1:
        value += "J"
    if key & 0x4:
        value += "U"
    if key & 0x8:
        value += "E"
    return value


def integer(word):
    """Return the integer of a raw hex value word."""
    return int(raw(word), base=16)


# Scanning
def scan(data, option=''):
    """
    Determine the type of image by scanning different offsets of file.

    Keywords:
        data -- tuple of bytes
    """
    if option in "md" or not option:
        if "SEGA" in str(string(data[0x100:0x110])):
            return "md", None
    if option in "sms" or not option:
        try:
            if "SEGA" in str(string(data[0x7ff0:0x7ff8])):
                return "sms", "7f"
        except UnicodeEncodeError:
            pass
        try:
            if "SEGA" in str(string(data[0x81f0:0x81f8])):
                return "sms", "81"
        except UnicodeEncodeError:
            # pylint: disable-next=raise-missing-from
            raise ValidationError()
    raise ValidationError()


def lookup(table, segment):
    """Perform a table lookup of a data segment and return all matches."""
    matches = []
    for code in segment:
        if code in table.keys():
            matches.append(table[code])
    return matches


# 16-bit specific
def alloc(segment):
    """Decode, calculate, and return address space allocation."""
    space = []
    space.append(raw(segment[0x0:0x4]))
    space.append(raw(segment[0x4:0x8]))
    divisor = integer(segment[0x4:0x8]) - integer(segment[0x0:0x4])
    space.append(divisor//1024 + (divisor % 1024 > 0))
    return space


def peripheral(segment):
    """Return the matching peripheral device value of a key in a data segment."""
    devices = {"O": "SMS Controller", "4": "Multitap", "6": "6-button Controller", "A": "Analog",
               "B": "Trackball", "C": "CD-ROM", "F": "Floppy", "G": "Lightgun",
               "J": "3-button Controller", "K": "Keyboard", "L": "Activator", "M": "Mouse",
               "P": "Printer", "R": "Serial RS-232", "T": "Tablet"}
    return lookup(devices, string(segment))


def modem(segment):
    """Return modem support and metadata information."""
    if string(segment[0x0:0x2]) not in "MO":
        return "No Support"
    support = ["No", "Yes", "Yes with mic"]
    values = {"00": [1, 0], "10": [2, 0], "20": [0, 1], "30": [0, 2], "40": [1, 1], "50": [2, 2],
              "60": [1, 2], "70": [2, 1]}
    details = [string(segment[0x2:0x6])]  # Publisher
    details.append(string(segment[0x6:0x8]))  # Game number
    details.append(string(segment[0x9:0xa]))  # Game version
    code = string(segment[0xa:0xc])
    details.append(support[values[code][0]])  # Jp Support
    details.append(support[values[code][1]])  # Export Support
    return details


def sram(segment):
    """Return static RAM support and metadata information."""
    if string(segment[0x0:0x2]) not in "RA":
        return "No SRAM"
    if raw(segment[0x3:0x4]) == "40":
        return ["EEPROM", "Unknown", alloc(segment[0x4:0xb])]
    config = []
    types = raw(segment[0x2:0x3])
    if types[0] in "ae":
        config.append("16-bit")
    elif types[0] in "bf":
        if types[1] == "0":
            config.append("8-bit even addresses")
        elif types[1] == "8":
            config.append("8-bit odd addresses")
    config.append(types[0] in "ef")
    config.extend(alloc(segment[0x4:0xc]))
    return config


def locale(segment):
    """Return the region or market area the software is meant to be published for."""
    regions = {"J": "Japan, South Korea, Taiwan", "U": "N. America, Brazil",
               "E": "Europe, Hong Kong, Australia"}
    code = string(segment)
    markets = lookup(regions, code)
    if not markets:  # crossover from old to new local format around Q1 1995
        try:
            code = bintostr(int(code[0], base=16))
        except ValueError:
            # pylint: disable-next=raise-missing-from
            raise ValidationError()
        markets.extend(lookup(regions, code))
    return markets


# 8-bit specific
def sizes(segment):
    """Return the matching size device value of a key in a data segment."""
    romsizes = {"a": "8KB", "b": "16KB", "c": "32KB", "d": "48KB", "e": "64KB", "f": "128KB",
                "0": "256KB", "1": "512KB", "2": "1024KB"}
    return romsizes[nibble_lsb(segment)]


def m3locale(segment):
    """Return the system and the region the software is meant to be published for."""
    regions = {"3": "SMS Japan", "4": "SMS Export", "5": "Game Gear Japan",
               "6": "Game Gear Export", "7": "Game Gear International"}
    return regions[nibble_msb(segment)]
