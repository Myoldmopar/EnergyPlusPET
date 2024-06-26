import pathlib
from platform import system
from setuptools import setup

from energyplus_pet import VERSION

readme_file = pathlib.Path(__file__).parent.resolve() / 'README.md'
readme_contents = readme_file.read_text()

install_requires = ['tksheet==7.1.8', 'matplotlib', 'scipy', 'PLAN-Tools>=0.5', 'pillow>=8.0.0']
if system() == 'Windows':
    install_requires.append('pypiwin32')

setup(
    name="energyplus_pet",
    version=VERSION,
    packages=['energyplus_pet', 'energyplus_pet.forms', 'energyplus_pet.equipment'],
    description="Parameter Estimation Tools for Generating EnergyPlus Inputs from Raw Performance Data",
    package_data={"energyplus_pet": ["icons/*.png", "icons/*.ico", "icons/*.icns", "examples/*.ods"]},
    include_package_data=True,
    long_description=readme_contents,
    long_description_content_type='text/markdown',
    author='Edwin Lee, for NREL, for United States Department of Energy',
    url='https://github.com/Myoldmopar/EnergyPlusPet',
    license='ModifiedBSD',
    install_requires=install_requires,
    entry_points={
        'gui_scripts': ['energyplus_pet_gui=energyplus_pet.runner:main_gui'],
        'console_scripts': ['energyplus_pet_configure=energyplus_pet.configure:configure_cli',]
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Physics',
        'Topic :: Utilities',
    ],
    platforms=[
        'Linux (Tested on Ubuntu)', 'MacOSX', 'Windows'
    ],
    keywords=[
        'energyplus_launch', 'ep_launch',
        'EnergyPlus', 'eplus', 'Energy+',
        'Building Simulation', 'Whole Building Energy Simulation',
        'Heat Transfer', 'HVAC', 'Modeling',
    ]
)
