import pathlib
from setuptools import setup

from energyplus_pet import VERSION

readme_file = pathlib.Path(__file__).parent.resolve() / 'README.md'
readme_contents = readme_file.read_text()

setup(
    name="energyplus_pet",
    version=VERSION,
    packages=['energyplus_pet', 'energyplus_pet.forms', 'energyplus_pet.equipment'],
    description="Parameter Estimation Tools for Generating EnergyPlus Inputs from Raw Performance Data",
    package_data={"energyplus_pet.forms": ["*.png", "*.ico"], "energyplus_pet": ["examples/*.ods"]},
    include_package_data=True,
    long_description=readme_contents,
    long_description_content_type='text/markdown',
    author='Edwin Lee',
    author_email='a@a.a',
    url='https://github.com/Myoldmopar/EnergyPlusPet',
    license='UnlicensedForNow',
    install_requires=['pyperclip', 'tksheet', 'matplotlib', 'numpy', 'scipy', 'pyshortcuts'],
    entry_points={
        'console_scripts': ['energyplus_pet_gui=energyplus_pet.runner:main_gui']
    }
)
