# SG-Tools Install Guide (for Python 2 versions)

### Prerequisites

 Python 2.3.5 or newer (For Python 2.6 and newer, the [recommended instructions using pip]
 (INSTALL.md) might work better.)  
 [pySerial 2.7](https://github.com/pyserial/pyserial) for communicating with the Mega
  Everdrive. 
 _On some systems, the [FTDI driver](https://www.ftdichip.com/old2020/Drivers/VCP.htm) may need to
 be installed, as well._

### Installing

 pip is not available for Python below 2.4, so each package needs to be installed with `setup.py`.

#### Installing PySerial

 ```bash
 wget --no-check-certificate --content-disposition https://files.pythonhosted.org/packages/df/c9/d9da7fafaf2a2b323d20eee050503ab08237c16b0119c7bbf1597d53f793/ pyserial-2.7.tar.gz
 tar -xzf pyserial-2.7.tar.gz && cd pyserial-2.7 && python2 setup.py install
 ```
  
 __Note:__ _pySerial needs patching for Python 2.5 and below:_

 ```bash
 sed -Ei 's/0o/0/' $(python2 -c "import serial as _; print(_.__path__)[0]")/serialposix.py
 ```

#### Installing SG-Tools

 ```bash
 tar -xzf sg_tools-X.XX-nopip.tar.gz && cd sg_tools-X.XX-nopip && python2 setup.py install
 ```

#### Notes

 Use of `sudo` might be required on your system for any of these commands.  

 Some installations of Python need their `bin` directory manually added to `$PATH`, to
 get `edsend` and `sg-header` to show in your terminal's global list of Bash commands.