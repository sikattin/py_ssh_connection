# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='connection',
    version='1.1',
    description='SSH Connection module.',
    long_description='',
    author='Takeki shikano',
    author_email='',
    url=None,
    license='MIT',
    packages=find_packages(exclude=('docs',))
)

