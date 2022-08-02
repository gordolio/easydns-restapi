#!/usr/bin/env python

import re

from setuptools import setup

with open('easydns_restapi/__init__.py', 'r') as f:
    version_match = re.search(r'^__version__\s*=\s*\'([^\']*)\'',
                              f.read(), re.MULTILINE)

if version_match is None:
    raise RuntimeError('No version information found in client.py')
else:
    version = version_match.group(1)

with open('README.md') as file:
    long_description = file.read()

setup(name='EasyDns RestApi',
      version=version,
      description='A very simple python client for easydns',
      long_description=long_description,
      author='Puru Tuladhar',
      author_email='ptuladhar3@gmail.com',
      url='https://github.com/gordolio/easydns-restapi',
      packages=['easydns_restapi'],
      install_requiress=[
          'requests>=2.4'
      ],
      classifiers=[
          'Intended Audience :: Developers',
          'Intended Audience :: System Administrators'
      ],
      project_urls={
          'Source': 'https://github.com/tuladhar/easydns-restapi-cli',
          'Fork': 'https://github.com/gordolio/easydns-restapi'
      })

