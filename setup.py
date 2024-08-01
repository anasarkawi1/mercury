# MercuryFramework setup.py
# By Anas Arkawi, 2024.

# This file contains information regarding the mercuryFramework package

from setuptools import setup, find_packages


# Project metadata
VERSION = '0.0.1'

DESCRIPTION = 'Mercury Framework for Quantitative and Algorithmic Trading.'

LONG_DESCRIPTION = 'A currently in development Python module made for algorithmic trading and sits at heart of Lycon.io and powers the platform.'

setup(
    name='mercuryFramework',
    version=VERSION,
    author='Anas Arkawi',
    author_email='anas@lycon.io',
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    packages=find_packages(),
    install_requires=[]
)