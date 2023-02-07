**PAN**das **A**nd **M**ulticore utils for corsik**A**7
===
[![GitHub](https://img.shields.io/github/license/The-Ludwig/PANAMA?style=for-the-badge)](https://github.com/The-Ludwig/PANAMA/blob/main/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/corsika-panama?style=for-the-badge)](https://pypi.org/project/corsika-panama/)
[![GitHub issues](https://img.shields.io/github/issues-raw/The-Ludwig/PANAMA?style=for-the-badge)](https://github.com/The-Ludwig/PANAMA/issues)
[![Codecov](https://img.shields.io/codecov/c/github/The-Ludwig/PANAMA?label=test%20coverage&style=for-the-badge)](https://app.codecov.io/gh/The-Ludwig/PANAMA)

Thanks [@Jean1995](https://github.com/Jean1995) for the silly naming idea.

# What this is

## CORSIKA7 parallelization
This started a little while ago while I was looking into the `EHIST` option
of corsika.
I wanted a way of conveniently running CORSIKA7 on more than 1 core.
I ended in the same place where most CORSIKA7 users end (see e.g. [fact-project/corsika_wrapper](https://github.com/fact-project/corsika_wrapper))
and wrote a small wrapper. Once this package is installed, you can use it with the `panama` command (see `panama --help` for options).

This wrapper has a nice progress bar, so you get an estimate for how long your simulation needs.

### Pitfalls
- The whole `run` folder of CORSIKA7 must be copied for each proccess, so very high parallel runs have high overhead
- If you simulate to low energies, python can't seem to hold up with the corsika output to `stdin` and essentially slows down corsika this is still a bug in investigation #1

## CORSIKA7 DAT files to pandas dataframe with working EHIST
Made possible by [cta-observatory/pycorsikaio](https://github.com/cta-observatory/pycorsikaio).

# What this is not
Bug-free or stable

# Installation
This package is available on pypi:
```
pip install corsika-panama
```
