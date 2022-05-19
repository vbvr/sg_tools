# Setup script for SG-Tools
# Tested on Python 2.3.5 to 3.9

import os
import sys

SCRIPTS = "src/scripts/"

if sys.version[0] == '2' and sys.version[2] < '4':
    VERSION = "legacy/"
else:
    VERSION = "current/"

SCRIPTDIR = SCRIPTS + VERSION
setup_data = {
    "name": "sg_tools",
    "version": "0.1.0",
    "description": "Collection of developer utilities dedicated to Sega platforms",
    "author": "Vadhym Beauvoir",
    "author_email": "vbeauvoir@gmail.com",
    "url": "https://github.com/vbvr/sg_tools",
    "license": "BSD",
    "package_dir": {"": "src"},
    "scripts": [SCRIPTDIR + "edsend", SCRIPTDIR + "sg-header"]
        }


try:
    fh = open("README.md", "r", encoding="utf-8")
except TypeError:
    try:
        if sys.version[0] == '2' and sys.version[2] >= '6':
            fh = open("README.md", "r")
        else:
            fh = open("README.txt", "r")
    except Exception:
        raise
long_description = fh.read()
fh.close()

#for file in os.listdir(SCRIPTDIR):
#    try:
#        fh = fileinput.FileInput(SCRIPTDIR + file, inplace=True, backup='.bkp')
#    except Exception:
#        raise
#    for line in fh:
#        sys.stdout.write(
#            line.replace("python ", "python" + sys.version[0] + "." + sys.version[2] + " ")
#        )
#        sys.stdout.flush()
#    fh.close()

if sys.version[0] >= '3' or (sys.version[0] == '2' and sys.version[2] >= '6'):
    import setuptools

    setuptools.setup(
        name=setup_data["name"],
        version=setup_data["version"],
        author=setup_data["author"],
        author_email=setup_data["author_email"],
        description=setup_data["description"],
        long_description=long_description,
        long_description_content_type="text/markdown",
        url=setup_data["url"],
        license=setup_data["name"],
        classifiers=[
            "Programming Language :: Python",
            "Programming Language :: Python :: 2",
            "Programming Language :: Python :: 2.3",
            "Programming Language :: Python :: 2.4",
            "Programming Language :: Python :: 2.5",
            "Programming Language :: Python :: 2.6",
            "Programming Language :: Python :: 2.7",
            "Programming Language :: Python :: 3",
            "License :: OSI Approved :: BSD License",
            "Operating System :: OS Independent",
            "Natural Language :: English",
            "Intended Audience :: Developers",
            "Intended Audience :: Science/Research",
            "Topic :: Scientific/Engineering :: Information Analysis",
            "Topic :: Software Development :: Embedded Systems",
            "Topic :: Software Development :: Testing",
            "Topic :: System :: Hardware :: Universal Serial Bus (USB)",
            "Topic :: Utilities",
        ],
        package_dir=setup_data["package_dir"],
        packages=setuptools.find_packages(where="src"),
        scripts=setup_data["scripts"],
        python_requires=">=2.3",
        install_requires=[
            "pyserial ==2.7; python_version<'2.7'",
            "pyserial >=3.0; python_version>='2.7'",
        ],
        options={"bdist_wheel": {"universal": True}},
    )
else:
    import fileinput
    from distutils.core import setup


    # Backport from wiki.python.org
    def is_package(path):
        return (
            os.path.isdir(path) and
            os.path.isfile(os.path.join(path, '__init__.py'))
        )

    def find_packages(path, base=""):
        """Find all packages in path."""
        packages = {}
        for item in os.listdir(path):
            filepath = os.path.join(path, item)
            if is_package(filepath):
                if base:
                    module_name = "%(base)s.%(item)s" % vars()
                else:
                    module_name = item
                packages[module_name] = filepath
                packages.update(find_packages(filepath, module_name))
        return packages

    #Script prep in case of multiple Python versions
    for file in os.listdir(SCRIPTDIR):
        try:
            fh = fileinput.FileInput(SCRIPTDIR + file, inplace=True, backup='.bkp')
        except Exception:
            raise
        for line in fh:
            sys.stdout.write(
                line.replace("python ", "python" + sys.version[0] + "." + sys.version[2] + " ")
            )
            sys.stdout.flush()
        fh.close()

    setup(
        name=setup_data["name"] + "-nopip",
        version=setup_data["version"],
        author=setup_data["author"],
        author_email=setup_data["author_email"],
        description=setup_data["description"],
        long_description=long_description,
        url=setup_data["url"],
        license=setup_data["name"],
        package_dir=setup_data["package_dir"],
        packages=find_packages(path="src"),
        scripts=setup_data["scripts"],
        platforms=["any", ]
    )
