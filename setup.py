import pathlib
from setuptools import setup

from energyplus_pet import VERSION

readme_file = pathlib.Path(__file__).parent.resolve() / 'README.md'
readme_contents = readme_file.read_text()

setup(
    name="EnergyPlus P.E.T.",
    version=VERSION,
    packages=['energyplus_pet'],
    description="Parameter Estimation Tools for Generating EnergyPlus Inputs from Raw Performance Data",
    long_description=readme_contents,
    long_description_content_type='text/markdown',
    author='Edwin Lee',
    author_email='a@a.a',
    url='https://github.com/Myoldmopar/EnergyPlusPet',
    license='UnlicensedForNow',
    entry_points={
        'console_scripts': ['ep_pet_gui=energyplus_pet.main:main_gui']
    }
)
