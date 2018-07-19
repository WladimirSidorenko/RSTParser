#!/usr/bin/env python
# -*- mode: python; coding: utf-8; -*-

##################################################################
# Libraries
from setuptools import setup
from os import path, walk
import codecs


##################################################################
# Variables and Constants
ENCODING = "utf-8"

PWD = path.abspath(path.dirname(__file__))

LONG_DESCRIPTION = ""
with codecs.open(path.join(PWD, "README.md"),
                 encoding=ENCODING) as ifile:
    LONG_DESCRIPTION = ifile.read()

INSTALL_REQUIRES = []
with codecs.open(path.join(PWD, "requirements.txt"),
                 encoding=ENCODING) as ifile:
    for iline in ifile:
        iline = iline.strip()
        if iline:
            INSTALL_REQUIRES.append(iline)

DSENSER_DATA = [path.join(path.basename(path.basename(iroot)), ifname)
                for iroot, _, ifnames in
                walk(path.join(path.dirname(__file__), "rstparser"))
                for ifname in ifnames
                if not ifname.startswith('.')]

##################################################################
# setup()
setup(
    name="rstparser",
    version="0.0.0a0",
    description=("shift-reduce RST parser of Ji and Eisenstein"),
    long_description=LONG_DESCRIPTION,
    author="Wladimir Sidorenko (Uladzimir Sidarenka)",
    author_email="sidarenk@uni-potsdam.de",
    license="MIT",
    url="https://github.com/WladimirSidorenko/RSTParser",
    include_package_data=True,
    packages=["rstparser"],
    package_data={"dsenser": DSENSER_DATA},
    install_requires=INSTALL_REQUIRES,
    scripts=[path.join("scripts", f)
             for f in ("rst_parser", "dis2edu")],
    entry_points={},
    classifiers=["Development Status :: 2 - Pre-Alpha",
                 "Environment :: Console",
                 "Intended Audience :: Science/Research",
                 "License :: OSI Approved :: MIT License",
                 "Natural Language :: English",
                 "Operating System :: Unix",
                 "Operating System :: MacOS",
                 "Programming Language :: Python :: 2",
                 "Programming Language :: Python :: 2.6",
                 "Programming Language :: Python :: 2.7",
                 "Programming Language :: Python :: 3",
                 "Topic :: Text Processing :: Linguistic"],
    keywords="discourse NLP linguistics"
)
