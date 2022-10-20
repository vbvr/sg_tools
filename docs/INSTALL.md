# SG-Tools Install Guide

### Prerequisites

 Python 2.4 or newer (needed for pip)  
 [pySerial 2.7 or newer](https://github.com/pyserial/pyserial) for communicating with the Mega
  Everdrive. This package is hosted on pyPI.  
 _On some systems, the [FTDI driver](https://www.ftdichip.com/old2020/Drivers/VCP.htm) may need to
 be installed, as well._

### Installing

 Create your virtual environment:

  ```bash
  mkdir sg_tools
  python -m virtualenv sg_tools
  . sg_tools/bin/activate
  ```
  
 Install the package or wheel:

 `pip install /path/to/sg_tools-X.XX.tar.gz`  
 `pip install /path/to/sg_tools-X.XX-py2.py3-none-any.whl`

 _Alternatively, install this directly into your user environment with `--user`_

### __Notes for obsolete versions of Python__ 

  pySerial needs patching for Python 2.5 and below:

  ```bash
  sed -Ei 's/0o/0/' $(python2 -c "import serial as _; print(_.__path__)[0]")/serialposix.py
  ```
  __Note:__ Use of `sudo` might be required on your system for this command.  

 If there are issues obtaining or running pip on Python versions below 2.6, see the [`setup.py` method](INSTALL2.md).

