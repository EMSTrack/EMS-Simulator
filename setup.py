from distutils.core import setup
from setuptools import find_packages

setup(
    name="ems-simulator",
    version="0.1.7",
    packages=find_packages(),
    python_requires='>=3.7',

    # metadata
    author="Mauricio C. de Oliveira, Timothy Lam, Hans Yuan",
    author_email="mauricio@ucsd.edu",

    description="Python library for EMS simulations",
    license="MIT",

    keywords=["EMS", "Simulation"],
    install_requires=[
        'numpy',
        'scipy',
        'geopy',
        'pandas',
        'pyyaml',
        'shapely'
    ],
    url="https://github.com/EMSTrack/EMS-Simulator",
    download_url="https://github.com/EMSTrack/EMS-Simulator/archive/v0.1.tar.gz",

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Other Audience',
        'Topic :: Scientific/Engineering',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.4',
    ],
)
