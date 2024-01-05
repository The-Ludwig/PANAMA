```
,-.----.                           ,--.das     nd               ____ ulticore utils for corsik  7
\    /  \     ,---,              ,--.'|   ,---,               ,'  , `.                    ,---,
|   :    \   '  .' \         ,--,:  : |  '  .' \           ,-+-,.' _ |                   '  .' \
|   |  .\ : /  ;    '.    ,`--.'`|  ' : /  ;    '.      ,-+-. ;   , ||                  /  ;    '.
.   :  |: |:  :       \   |   :  :  | |:  :       \    ,--.'|'   |  ;|                 :  :       \
|   |   \ ::  |   /\   \  :   |   \ | ::  |   /\   \  |   |  ,', |  ':                 :  |   /\   \
|   : .   /|  :  ' ;.   : |   : '  '; ||  :  ' ;.   : |   | /  | |  ||                 |  :  ' ;.   :
;   | |`-' |  |  ;/  \   \'   ' ;.    ;|  |  ;/  \   \'   | :  | :  |,                 |  |  ;/  \   \
|   | ;    '  :  | \  \ ,'|   | | \   |'  :  | \  \ ,';   . |  ; |--'                  '  :  | \  \ ,'
:   ' |    |  |  '  '--'  '   : |  ; .'|  |  '  '--'  |   : |  | ,                     |  |  '  '--'
:   : :    |  :  :        |   | '`--'  |  :  :        |   : '  |/                      |  :  :
|   | :    |  | ,'        '   : |      |  | ,'        ;   | |`-'                       |  | ,'
`---'.|    `--''          ;   |.'      `--''          |   ;/                           `--''
  `---`                   '---'                       '---'
```

PANAMA - A python toolkit for CORSIKA7.

[![Read the Docs](https://img.shields.io/readthedocs/panama?style=for-the-badge)](https://panama.readthedocs.io/en/latest/)

[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/The-Ludwig/PANAMA/ci.yml?style=for-the-badge)](https://github.com/The-Ludwig/PANAMA/actions/workflows/ci.yml)
[![Codecov](https://img.shields.io/codecov/c/github/The-Ludwig/PANAMA?label=test%20coverage&style=for-the-badge)](https://app.codecov.io/gh/The-Ludwig/PANAMA)
[![PyPI](https://img.shields.io/pypi/v/corsika-panama?style=for-the-badge)](https://pypi.org/project/corsika-panama/)
[![DOI](https://img.shields.io/badge/DOI-10.5281%20%2F%20zenodo.10210623-blue.svg?style=for-the-badge)](https://doi.org/10.5281/zenodo.10210623)

[![GitHub issues](https://img.shields.io/github/issues-raw/The-Ludwig/PANAMA?style=for-the-badge)](https://github.com/The-Ludwig/PANAMA/issues)
[![GitHub](https://img.shields.io/github/license/The-Ludwig/PANAMA?style=for-the-badge)](https://github.com/The-Ludwig/PANAMA/blob/main/LICENSE)
[![Codestyle](https://img.shields.io/badge/codesyle-Black-black.svg?style=for-the-badge)](https://github.com/psf/black)

## Features

This python package provides multiple features -- each feature can be used independently, but they also work great together.

- Execute CORSIKA7 on multiple cores
- Read CORSIKA7 DAT files ("particle files") to [`pandas DataFrame`s](https://pandas.pydata.org/docs/)
  - Compatible with CORSIKA7's `EHIST` option
- Calculate weights for a multiple primary spectra

To see some examples on how to use panama, see the introduction in the documentation.
To get an overview of how the features play together, have a look at the example notebook in the documentation.
In-depth explanation is provided in the API documentation.

## Installation

```bash
pip install corsika-panama
```

If you want to convert Corsikas DAT files to HDF5 files, you need to install the optional `hdf` dependency

```
pip install corsika-panama[hdf]
```

## Further Notes

Naming idea goes back to [@Jean1995](https://github.com/Jean1995), thanks for that!
He originally proposed "PArallel ruN of corsikA on MAny cores", as
the scope of this library grew bigger, it evolved into the current name.

This started as part of the code I wrote for [my master thesis](https://ludwigneste.space/masterthesis_ludwig_neste.pdf).
I ended in the same place where most CORSIKA7 users end when running large CORSIKA7 simulations and wrote small scripts
to split one simulation request into multiple CORSIKA7 processes with different seeds.
The FACT software ([fact-project/corsika_wrapper](https://github.com/fact-project/corsika_wrapper))
and the IceCube software does essentially the same thing (and I am sure, MAGIC, CTA and other air-shower based observatories do the same).
I hope this package provides a more experiment-independent and better documented version of internal software packages.

## Related Repositories

- Reading DAT files uses [cta-observatory/pycorsikaio](https://github.com/cta-observatory/pycorsikaio).
- Cosmic Ray models implemented in [The-Ludwig/FluxComp](https://github.com/The-Ludwig/FluxComp/).
