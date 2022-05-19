#!/usr/bin/python
# -*- coding: utf8 -*-
"""Image File Header Analyzer for Sega 8-bit and 16-bit."""

import sys
from struct import unpack

from sg_tools import decoder

if sys.version[0] in '2':
    from backport.ordereddict import OrderedDict

    # pylint: disable-next=redefined-builtin, invalid-name
    dict = OrderedDict


class Header:
    """
    Header information for an image file of Sega 8-bit and 16-bit consoles.

    The Header object holds the header information for either Sega Genesis/Mega Drive, Master
    System/Mark III, or Game Gear consoles. 32X is an attachment to Genesis/Mega Drive that uses
    the same header format in their images. All official headers contain the SEGA TMSS string, a
    checksum, a region, a size, a version number and a product number. Genesis/Mega Drive software
    contain additional details. Upon instance creation, the type of image is determined.

    Attributes:
        block -- dict
    Header block information for each metadata category of the detected image type.
    """

    def __init__(self, block):
        self.block = block

    # pylint: disable-next=invalid-name
    def smd(cls):
        """Header format for 16-bit (and 32X) images."""
        return cls(dict([("system", [0x100, 0x10, "System Type"]),
                         ("copyright", [0x110, 0x10, "Copyright"]),
                         ("domestic", [0x120, 0x30, "Japan Title"]),
                         ("export", [0x150, 0x30, "Export Title"]),
                         ("serial", [0x180, 0xe, "Serial"]),
                         ("checksum", [0x18e, 0x2, "Checksum"]),
                         ("device", [0x190, 0x10, "Devices Supported"]),
                         ("romrange", [0x1a0, 0x8, ["ROM", "Min Offset", "Max offset", "kB"]]),
                         ("ramrange", [0x1a8, 0x8, ["RAM", "Min Offset", "Max offset", "kB"]]),
                         ("extra", [0x1b0, 0xc, ["SRAM", "Type", "Width", "Min", "Max", "kB"]]),
                         ("modem", [0x1bc, 0xc, ["Modem", "Publisher", "Game Number", "Version",
                                                 "Japan Support", "Export Support"]]),
                         ("region", [0x1f0, 0x3, "Regions"])]))
    # pylint: disable-next=no-classmethod-decorator
    smd = classmethod(smd)

    def sms(cls, qword):
        """Header format for 8=bit images. There are two known offsets with header information."""
        return cls(dict([("system", [decoder.join(qword, "f0"), 0x8]),
                         ("checksum", [decoder.join(qword, "fa"), 0x2, "Checksum"]),
                         ("prod", [decoder.join(qword, "fc"), 0x3, "Product Number"]),
                         ("version", [decoder.join(qword, "fe"), 0x1, "Version"]),
                         ("size", [decoder.join(qword, "ff"), 0x1, "Size"]),
                         ("m3region", [decoder.join(qword, "ff"), 0x1, "Region"])]))
    # pylint: disable-next=no-classmethod-decorator
    sms = classmethod(sms)

    def fields(self):
        """List Header object's segment fields."""
        for field in list(self.block):
            print(field)

    def display(self, field):
        """
        Display the header metadata of the file.

        Keyword:
            field -- string
        Display metadata of segment name given
        """
        if len(self.block[field]) > 3:
            if isinstance(self.block[field][-1], list):
                if isinstance(self.block[field][2], list):
                    print("%s" % self.block[field][2][0])
                    for title, meta in zip(self.block[field][2][1:], self.block[field][3]):
                        print("\t%s: %s" % (title, meta))
                else:
                    print("%s" % self.block[field][2])
                    for meta in self.block[field][3]:
                        print("\t%s" % meta)
            elif isinstance(self.block[field][2], list):
                print("%s: %s" % (self.block[field][2][0], self.block[field][-1]))
            else:
                try:
                    print("%s: %s" % (self.block[field][2], self.block[field][-1]))
                except UnicodeEncodeError:
                    print("%s: %s" % (self.block[field][2], self.block[field][-1].encode('utf8')))

    def metadata(self, segment=None):
        """
        Display the header metadata of the file.

        Keyword:
            segment -- string
        Display metadata of decoded segment name given. If none given, all display all decoded
        segments.
        """
        if segment is None:
            for field in self.block:
                self.display(field)
        else:
            try:
                self.display(segment)
            except KeyError:
                print("Invalid field entered")
                print("Valid fields:")
                self.fields()

    def retrieve(self, data):
        """
        Retrieve decoded header information.

        Keyword:
            data -- tuple
        Pass through all metadata fields of Header to decoder and append results to Header
        """
        for field in self.block:
            offset = self.block[field][0]
            length = self.block[field][1]
            self.block[field].append(decoder.decode(field, data[offset: offset + length]))


def abort(message):
    """Print a message to screen and quit module."""
    print(message)
    if __name__ == "__main__":
        raise SystemExit(1)


def load(filename=sys.argv[-1]):
    """Open and prepare file image."""
    try:
        # pylint: disable-next=consider-using-with
        file = open(filename, "rb")
        image = file.read()
        file.close()
        if filename in sys.argv[-1]:
            print("Read %d bytes from file\n" % len(image))
        raw = unpack("B"*len(image), image)
    except IOError:
        abort("%s not found" % sys.argv[-1])
    return populate(raw)


def populate(image):
    """Populate key data for header being accessed."""
    mode, section = decoder.scan(image)
    if mode in "md":
        print("Image type: 16-bit image")
        keys = Header.smd()
    if mode in "sms":
        print("Image type: 8-bit image")
        keys = Header.sms(section)
    keys.retrieve(image)
    return keys


if __name__ == "__main__":
    if len(sys.argv) <= 1:
        abort("No filename")
    header = load()
    header.metadata()
