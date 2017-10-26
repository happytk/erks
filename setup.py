#!/usr/bin/env python

from setuptools import setup, find_packages
import versioneer
setup(
    name='ercc',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description='ercc',
    author='skcc-da',
    author_email='chazzy1@gmail.com;einslib@sk.com;wecanfly@sk.com',
    url='https://www.nexcore-erc.com/',
    packages=find_packages(),
    include_package_data=True,
)
