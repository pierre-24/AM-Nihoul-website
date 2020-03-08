"""
AM-Nihoul-website, a small website for an association with not intent of being something else
"""


# adapted over https://github.com/pypa/sampleproject/blob/master/setup.py

from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md')) as f:
    long_description = f.read()

with open(path.join(here, 'requirements/requirements.in')) as f:
    requirements = f.readlines()

with open(path.join(here, 'requirements/requirements-dev.in')) as f:
    requirements_dev = f.readlines()[1:]


setup(
    name='AM-Nihoul-website',
    version='0.1a0',
    
    # Description
    description=__doc__,
    long_description=long_description,
    long_description_content_type='text/markdown',
    keywords='website',

    project_urls={
        'Bug Reports': 'https://git.pierrebeaujean.net/pierre/AM-Nihoul-website/issues',
        'Source': 'https://git.pierrebeaujean.net/pierre/AM-Nihoul-website/',
    },
    
    url='http://www.annemarienihoul.be/',
    author='Pierre Beaujean',

    # Classifiers
    classifiers= [
        'Development Status :: 3 - Alpha',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'License :: OSI Approved :: MIT License',

        # Specify the Python versions:
        'Framework :: Flask'
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],


    packages=find_packages(),
    python_requires='>=3.5',

    # requirements
    install_requires=requirements,

    extras_require={  # Optional
        'dev': requirements_dev,
    },
)
