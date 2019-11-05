from distutils.core import setup

setup(
    name="ems-simulator",
    version="0.1.5",
    packages=['ems',
              'ems.algorithms',
              'ems.analysis',
              'ems.datasets',
              'ems.generators',
              'ems.models',
              'ems.scenarios',
              'ems.simulators',
              'ems.triggers'],
    python_requires='>=3.4',

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
