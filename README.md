# EnergyPlus "PET"

This project is a cross platform Python (Tk) GUI and tool kit for generating EnergyPlus inputs from component performance data. 

## Code Quality

[![Flake8](https://github.com/Myoldmopar/EnergyPlusPET/actions/workflows/flake8.yml/badge.svg)](https://github.com/Myoldmopar/EnergyPlusPET/actions/workflows/flake8.yml)
[![Tests](https://github.com/Myoldmopar/EnergyPlusPET/actions/workflows/test.yml/badge.svg)](https://github.com/Myoldmopar/EnergyPlusPET/actions/workflows/test.yml)
[![Coverage Status](https://coveralls.io/repos/github/Myoldmopar/EnergyPlusPET/badge.svg?branch=main)](https://coveralls.io/github/Myoldmopar/EnergyPlusPET?branch=main)

Code is checked for style and with unit tests by GitHub Actions using nosetests to sniff out the tests.
Code coverage is exercised purely on Ubuntu and pushed to coveralls, available [here](https://coveralls.io/github/Myoldmopar/EnergyPlusPET?branch=main).

## Documentation

[![Sphinx docs to gh-pages](https://github.com/Myoldmopar/EnergyPlusPET/actions/workflows/docs.yml/badge.svg)](https://github.com/Myoldmopar/EnergyPlusPET/actions/workflows/docs.yml)

Docs are built from Sphinx by GitHub Actions and followed up with a deployment to GH-Pages using Actions, available [here](https://myoldmopar.github.io/EnergyPlusPET/).

## Releases

[![PyPIRelease](https://github.com/Myoldmopar/EnergyPlusPET/actions/workflows/release.yml/badge.svg)](https://github.com/Myoldmopar/EnergyPlusPET/actions/workflows/release.yml)

When a release is tagged, a GitHub Action workflow will create a Python wheel and upload it to the TestPyPi server.

To install into an existing Python environment, execute `pip install -i https://test.pypi.org/simple/ energyplus_pet`
