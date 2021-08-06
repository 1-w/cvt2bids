#!/usr/bin/env python
# -*- coding: utf-8 -*-
# type: ignore
# pylint: disable=exec-used

import os
from setuptools import setup, find_packages

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

def install_requires():
    """Get list of required modules"""
    required = []
    for module, meta in _VERSION["REQUIRED_MODULE_METADATA"]:
        required.append("{}>={}".format(module, meta["min_version"]))
    return required


#_VERSION = load_version()
DISTNAME = "cvt2bids"
VERSION = "0.1.0" #_VERSION["__version__"] TODO
ENTRY_POINTS = {
    "console_scripts": [
        "cvt2bids = src.cvt2bids:main",
    ],
}
AUTHOR = "Lennart Walger"
AUTHOR_EMAIL = "lennart.walger@ukbonn.de"
DESCRIPTION = (
        "everything around converting dicom data to bids compatible niftis"
)
with open("README.md", encoding="utf-8") as _:
    LONG_DESCRIPTION = _.read()
LICENSE = "GPLv3+"
PROJECT_URLS = {
    "Documentation": "https://github.com/1-w/cvt2bids",
    "Source Code": "https://github.com/1-w/cvt2bids",
}
CLASSIFIERS = [
    "Intended Audience :: Healthcare Industry",
    "Intended Audience :: Science/Research",
    "Operating System :: MacOS",
    "Operating System :: Microsoft :: Windows",
    "Operating System :: Unix",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Topic :: Scientific/Engineering",
    "Topic :: Scientific/Engineering :: Bio-Informatics",
    "Topic :: Scientific/Engineering :: Medical Science Apps.",
]


if __name__ == "__main__":
    setup(
        name=DISTNAME,
        version=VERSION,
        packages=find_packages(exclude=['data', 'figures', 'output', 'notebooks', 'build']),
        entry_points=ENTRY_POINTS,
        python_requires=">=3.6",
        use_scm_version=True,
        setup_requires=['setuptools_scm'],
        install_requires=[
          'future>=0.17.1',
          'numpy',
          'pydeface@git+https://github.com/1-w/pydeface.git',
          'pydicom',
          'nii2dcm@git+https://gitlab.com/lab_tni/projects/nii2dcm.git',
          'dcm2bids@git+https://github.com/1-w/Dcm2Bids.git@nameAsStringBugFix',
          'pandas',
          # TODO: drop this when py3.6 is end-of-life
          'importlib_resources ; python_version<"3.7"'
        ],
        include_package_data=True,
        author=AUTHOR,
        author_email=AUTHOR_EMAIL,
        description=DESCRIPTION,
        long_description=LONG_DESCRIPTION,
        long_description_content_type="text/markdown",
        # keywords="",
        license=LICENSE,
        project_urls=PROJECT_URLS,
        classifiers=CLASSIFIERS,
    )