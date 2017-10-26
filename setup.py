"""
Converts a notebook with student written answers to a PDF for Gradescope.
Ensures that each question has a constant number of pages.
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='gs100',
    version='0.0.2',
    description='Converts a notebook with student written answers to a '
                'PDF for Gradescope.',
    long_description=long_description,
    url='https://github.com/DS-100/nb-to-gradescope',

    author='Sam Lau',
    author_email='samlau95@gmail.com',

    license='BSD 3-Clause',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 3 - Alpha',

        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',

        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Framework :: Jupyter',
    ],
    keywords='jupyter ds100 gradescope',

    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    install_requires=[
        'toolz>=0.8',
        'nbformat>=4',
        'nbconvert>=5',
        'beautifulsoup4>=4',
        'pdfkit>=0.6',
        'PyPDF2>=1.26',
    ],

    extras_require={
        'dev': ['check-manifest'],
        'test': ['coverage'],
    },
)
