#!/usr/bin/env python3

from setuptools import setup, find_packages

setup(
    name="finian",
    version="0.2",
    packages=find_packages(),

    install_requires=[
        "rsa"
    ],

    author=""Byron"",
    author_email="37745048+byhowe@users.noreply.github.com",
    description="A library that utilizes RSA encryption to make sockets secure.",
    url="https://github.com/byhowe/python-networking"
)
