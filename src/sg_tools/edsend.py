#!/usr/bin/python
"""
Python port to beardedfoo's Golang port to krikzz's Mega EverDrive .NET-based usb tool v2.0.

This port is intended to increase compatibility with computers even further than possible with
Golang can, particularly, with older devices.

Tested working on Python 2.3.5+ with pyserial 2.7+
Python 2.6+ required for autoscanning of USB port
"""

import sys
from struct import pack, unpack
from sys import argv
from time import sleep

import serial

from sg_tools import decoder
from sg_tools.decoder import ValidationError
from sg_tools.header import Header

if sys.version[0] in '2':
    # pylint: disable-next=redefined-builtin, invalid-name
    bytes = str

USAGE = """Usage: %s [options] file
Send a file to a Mega Everdrive X7
Options:
    -p  Serial port (i.e. /dev/ttyUSB0, COM11, etc.)
    -b  Baud rate (bps)
    -t  Serial read timeout (s)
    -m  Everdrive run mode (cd, m10, md, os, sms, or ssf)

    -h  Print this help message

Example using all the options on Ubuntu:
    %s -p "/dev/ttyUSB0" -b 9600 -t 1 -m md /path/to/file.bin"""

BLOCK = 512 * 128
MAXROM = 0xf00000


class Loader:
    """
    Class for Everdrive loader.

    Locate Everdrive if no path given for it. Initiate connection to Everdrive. Open and identify
    file being loaded. Load file to Everdrive. Run the image.

    Attributes:
        link -- object
    Connection to Everdrive
        file -- string
    Filepath of image to load
        parser -- object
    File parser
        baud_rate -- integer
    Baud rate for connection to Everdrive. Typically ignored for USB. Default is 9600.
        serial_port -- string
    Path to Everdrive connection. If not supplied, a scan is done to find one. Scanning not
    supported for Python earlier than 2.6.
        read_timeout -- integer
    Optional read timeout settings for Everdrive connection. Default is 1.
        run_mode -- string
    Mode for launching the image file. Default is Mega Drive/Genesis
    """

    def __init__(self, filepath=None, port=None, cxn=(9600, 1, ), mode="md", **kwargs):
        # baud=9600, port=None, timeout=1, mode="md", **kwargs):
        self.link = None
        self.parser = None
        self.error = None
        self.file = filepath
        self.serial_port = kwargs.pop("-p", port)
        self.cxn = (kwargs.pop("-b", cxn[0]), kwargs.pop("-t", cxn[1]), )
        self.run_mode = kwargs.pop("-m", mode)
        if not self.serial_port or self.serial_port == "None":
            if sys.version[0] in '2' and int(sys.version[2]) < 6:
                abort("ERROR: No port path entered.\n%s" % USAGE % (argv[0], argv[0]))
            print("Scanning for MegaEverdrive...")
            self.scan()

    def scan(self):
        """Scan for first available FTDI device to use."""
        # pylint: disable-next=import-outside-toplevel
        from serial.tools import list_ports
        ports = list_ports.comports(include_links=True)
        for port in ports:
            if port.manufacturer == "FTDI":
                self.serial_port = port.device
                print("Found serial port: %s" % port.device)
                break
        if not self.serial_port:
            abort("ERROR: No compatible serial port found.")

    def connect(self):
        """Create a link, initiate, and test connection."""
        self.link = Link(self.serial_port, self.cxn[0], self.cxn[1])
        self.link.setup()
        self.error = self.link.test()

    def load(self):
        """Load file image to application."""
        self.parser = Parser(self.file)
        self.parser.ident(self.run_mode)

    def send(self):
        """Send loaded image to Everdrive link."""
        self.error = self.link.transfer(self.parser.raw)

    def run(self):
        """Launch image, using specified run mode of application."""
        self.error = self.link.run(self.run_mode)
        if not self.error:
            print("Starting....")

    def init(self):
        """Load file and connect to Everdrive."""
        self.load()
        self.connect()

    def start(self):
        """Send and tell Everdrive to start."""
        if not self.error:
            self.send()
        if not self.error:
            self.run()


class Parser:
    """
    Object for loading and validating image file.

    Attributes:
        path -- string
    Filepath of image being accessed
        header -- object
    Header of the loaded image, if valid
    """

    def __init__(self, filename):
        self.header = None
        self.path = filename
        self.load()
        print("Read %d bytes from file\n" % len(self.data))
        self.format()

    def load(self):
        """Load image into parser."""
        try:
            # pylint: disable-next=consider-using-with
            file = open(self.path, "rb")
            self.data = file.read()
            file.close()
        except IOError:
            abort("%s not found" % self.path)

    def format(self):
        """
        Format image into a raw tuple of bytes, padded with 0s to nearest block size.

        Max image size 15MB.
        """
        self.raw = unpack("B"*len(self.data), self.data)
        if len(self.data) % BLOCK != 0:
            self.raw = self.raw + (0,) * (BLOCK - len(self.raw) % BLOCK)
        if len(self.raw) > MAXROM:
            abort("ERROR: ROM file is too large, %dbytes (%dMB) is the maximum"
                  % (MAXROM, MAXROM/(1024**2)))

    def ident(self, option):
        """
        Load header information of the file and determine whether it is valid and would pass TMSS.

        Sending to the Everdrive still takes place if image is deemed invalid.
        """
        try:
            match, section = decoder.scan(self.raw, option)
            if option in "md" and match in "md":
                self.header = Header.smd()
            if option in "sms" and match in "sms":
                self.header = Header.sms(section)
        except ValidationError:
            print("WARNING: Unofficial image")
            return
        self.header.retrieve(self.raw)
        self.header.metadata()


class Link:
    """
    Communication interface to Everdrive.

    Attributes:
        cxn -- object
    The serial connection to the Everdrive.
        port -- string
    Logical path to the serial connection.
        baud -- integer
    Baudrate to use for connection. Since this is USB, this normally does not need setting.
        timeout -- integer
    Read timeout for connection. Transfers usually work without setting this.
        message -- dict
    Bank of messages for communicating with Everdrive.
    """

    def __init__(self, *args):
        self.cxn = None
        self.port = args[0]
        self.baud = args[1]
        self.timeout = args[2]
        self.message = {"INIT": "    *T", "LD": "*g", "OK": "k", "DOK": "d", "SMS": "*rs",
                        "OS": "*ro", "CD": "*rc", "M10": "*rM", "SSF": "*rS", "MD": "*rm"}

    def setup(self):
        """Initiate connection to Everdrive."""
        print("Connecting to serial...")
        try:
            self.cxn = serial.Serial(self.port, self.baud, timeout=self.timeout, write_timeout=120)
        except serial.serialutil.SerialException:
            abort("ERROR: Cannot find or open serial port %s" % self.port)
        except ValueError:
            abort("ERROR: Invalid serial parameters entered")
        except TypeError:
            try:
                self.cxn = serial.Serial(self.port, self.baud, timeout=self.timeout,
                                         writeTimeout=120)
            except OSError:
                abort("ERROR: Cannot find or open serial port %s" % self.port)
        print("\t %s OK" % self.cxn.port)

    def post(self, data, error):
        """
        Write data to Everdrive connection.

        Keyword:
            data - string of bytes
        """
        if not error:
            try:
                self.cxn.write(data)
                sleep(0.01)
            except serial.SerialException:
                print("ERROR: Sending to MegaED failed")
                try:
                    print(bytes.decode(self.cxn.read(50)))
                    self.cxn.close()
                except serial.serialutil.SerialException:
                    abort("Connection has closed prematurely")
                return 1
        return None

    def response(self, ack, error):
        """
        Read response from Everdrive connection.

        Quit application if decoded response is not an expected ack.

        Keyword:
            ack -- string
        """
        if not error:
            message = self.cxn.read()
            if bytes.decode(message) != ack:
                abort("ERROR: Invalid response from MegaED")
                return 1
        return None

    def test(self):
        """Send init string and check for expected response."""
        print("Testing connection...")
        error = self.post(str.encode(self.message["INIT"]), 0)
        error = self.response(self.message["OK"], error)
        if error:
            return 1
        print("\t OK")
        return None

    def transfer(self, raw):
        """
        Send file to Everdrive.

        Keyword:
            raw -- tuple of bytes

        Send command to receive a payload. Send size of image in 64k block units. Check for ack.
        Send image file. Check for ack.
        """
        raw = pack("B"*len(raw), *raw)
        error = self.post(str.encode(self.message["LD"]), 0)
        error = self.post(pack("B", (int(len(raw)/BLOCK))), error)
        error = self.response(self.message["OK"], error)
        if not error:
            print("Sending image data...")
        error = self.post(serial.to_bytes(raw), error)
        if not error:
            print("Checking reponse...")
        error = self.response(self.message["DOK"], error)
        return error

    def run(self, mode):
        """
        Post run mode.

        Keyword:
            mode -- string
        """
        error = self.post(str.encode(self.message[mode.upper()]), 0)
        error = self.response(self.message["OK"], error)
        return error


def abort(message, level=1):
    """Print a message to screen and quit module."""
    print(message)
    if __name__ == "__main__":
        raise SystemExit(level)


def parse_options():
    """Parse arguments from command line."""
    if "-h" in argv:
        abort(USAGE % (argv[0], argv[0]), 0)
    if len(argv) < 2 or argv[-1].startswith("-"):
        abort("Usage: %s [options] file" % argv[0])
    options = {"file": argv[-1], }
    pos = 1
    for arg in argv[pos:]:
        if arg[0].startswith("-"):
            if arg[1] in ["b", "m", "p", "t"] and not argv[pos+1][0].startswith("-"):
                options[arg] = argv[pos+1]
        pos += 1
    return options


if __name__ == "__main__":
    opts = parse_options()
    image = opts.pop("file")
    app = Loader(image, **opts)
    app.init()
    app.start()
