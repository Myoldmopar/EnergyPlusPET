# EnergyPlus "PET"

This project is a cross platform Python (Tk) GUI and tool kit for generating EnergyPlus inputs from component performance data. 

## Code Quality

[![Flake8](https://github.com/Myoldmopar/EnergyPlusPET/actions/workflows/flake8.yml/badge.svg)](https://github.com/Myoldmopar/EnergyPlusPET/actions/workflows/flake8.yml)
[![Tests](https://github.com/Myoldmopar/EnergyPlusPET/actions/workflows/test.yml/badge.svg)](https://github.com/Myoldmopar/EnergyPlusPET/actions/workflows/test.yml)

Code is checked for style and with unit tests by GitHub Actions using nosetests to sniff out the tests.

## Documentation

[![Sphinx docs to gh-pages](https://github.com/Myoldmopar/EnergyPlusPET/actions/workflows/docs.yml/badge.svg)](https://github.com/Myoldmopar/EnergyPlusPET/actions/workflows/docs.yml)

[![gh-pages](https://github.com/Myoldmopar/EnergyPlusPET/actions/workflows/pages/pages-build-deployment/badge.svg?branch=gh-pages)](https://github.com/Myoldmopar/EnergyPlusPET/actions/workflows/pages/pages-build-deployment)

Docs are built from Sphinx by GitHub Actions and followed up with a deployment to GH-Pages using Actions, available at https://myoldmopar.github.io/EnergyPlusPET/

## Releases

[![PyPIRelease](https://github.com/Myoldmopar/EnergyPlusPET/actions/workflows/release.yml/badge.svg)](https://github.com/Myoldmopar/EnergyPlusPET/actions/workflows/release.yml)

When a release is tagged, a GitHub Action workflow will create a Python wheel and upload it to the TestPyPi server.

To install into an existing Python environment, execute `pip install -i https://test.pypi.org/simple/ energyplus_pet`
