# ==================================================================
# File: addons/md2docx-python-main/setup.py
# Description: 
# ==================================================================

from setuptools import setup, find_packages
from os import path
working_directory = path.abspath(path.dirname(__file__))

with open(path.join(working_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='md2docx_python',
    version='1.0.0',
    url='https://github.com/shloktech/md2docx-python',
    author='Shlok Tadilkar',
    author_email='shloktadilkar@gmail.com',
    license='MIT',
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.9",
        "Operating System :: OS Independent",
    ],
    description="""Markdown to Word Converter.
                Simple and straight forward Python utility 
                that converts a Markdown file (`.md`) to a Microsoft 
                Word document (`.docx`). It supports multiple Markdown 
                elements, including headings, bold and italic text, 
                both unordered and ordered lists and many more.""",
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=find_packages(),
    install_requires=['markdown>=3.7', 'python-docx>=1.1.2', 'beautifulsoup4>=4.13.3'],
    python_requires=">=3.9.0",
)


