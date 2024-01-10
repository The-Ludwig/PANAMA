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

PANAMA - A python toolkit for [CORSIKA7](https://www.iap.kit.edu/corsika/index.php).

[![Read the Docs](https://img.shields.io/readthedocs/panama?style=for-the-badge)](https://panama.readthedocs.io/en/latest/)

[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/The-Ludwig/PANAMA/ci.yml?style=for-the-badge)](https://github.com/The-Ludwig/PANAMA/actions/workflows/ci.yml)
[![GitHub issues](https://img.shields.io/github/issues-raw/The-Ludwig/PANAMA?style=for-the-badge)](https://github.com/The-Ludwig/PANAMA/issues)
[![Codecov](https://img.shields.io/codecov/c/github/The-Ludwig/PANAMA?label=test%20coverage&style=for-the-badge)](https://app.codecov.io/gh/The-Ludwig/PANAMA)

[![PyPI](https://img.shields.io/pypi/v/corsika-panama?style=for-the-badge)](https://pypi.org/project/corsika-panama/)
[![DOI](https://img.shields.io/badge/DOI-10.5281%20%2F%20zenodo.10210623-blue.svg?style=for-the-badge)](https://doi.org/10.5281/zenodo.10210623)
[![GitHub](https://img.shields.io/github/license/The-Ludwig/PANAMA?style=for-the-badge)](https://github.com/The-Ludwig/PANAMA/blob/main/LICENSE)
[![Codestyle](https://img.shields.io/badge/codesyle-Black-black.svg?style=for-the-badge)](https://github.com/psf/black)

## Features

This python package provides multiple features -- each feature can be used independently, but they also work great together.

- Execute CORSIKA7 on multiple cores
- Read CORSIKA7 DAT files ("particle files") to [pandas DataFrames](https://pandas.pydata.org/docs/)
  - Correctly parse output from the `EHIST` option
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

### CORSIKA7

For usage and installation of CORSIKA7, please refer to [its website](https://www.iap.kit.edu/corsika/index.php) and its [userguide](https://www.iap.kit.edu/corsika/downloads/CORSIKA_GUIDE7.7500.pdf).
To properly use this package, knowledge of CORSIKA7 is required.

If you want to install CORSIKA7, you need to request access to their CORSIKA7 mailing list, [as described on their website](https://www.iap.kit.edu/corsika/79.php), then you will receive the CORSIKA7
password.
If you want to skip the process of getting familiar with the software and compiling it with coconut, panama provides a (linux) script for compiling
it.
You will need a `fortran` compiler. CORSIKA7 will then be pre-configured with the curved earth, EHIST, SIBYLL2.3d and URQDM options.
For finer control over the used options, please compile CORSIKA7 yourself.
After cloning this repository, you can then execute

```bash
CORSIKA_VERSION=77500 CORSIKA_PW=CORSIKA_PASSWORD_YOU_WILL_RECEIVE_BY_MAIL admin/download_corsika.sh
```

which will download and compile CORSIKA7 version 77500.
If you are interested in automatically testing software using CORSIKA7, using GitHub actions,
have a look at the `.github` folder of this project in combination with the admin script.

## Contributing

Contributions and suggestions are very welcome.
Feel free to open an [issue](https://github.com/The-Ludwig/PANAMA/issues) or [pull request](https://github.com/The-Ludwig/PANAMA/pulls).
This project uses [pdm](https://pdm-project.org/latest/) for the build system as well as a
dependency and virtual environment manager.
For suggestions on how to set up a development environment, have a look at `CONTRIBUTING.md`.

## Further Notes

This project tries to stay compatible with the suggestions from [Scikit hep](https://learn.scientific-python.org/development/guides/repo-review/?repo=The-Ludwig%2Fpanama&branch=main).

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
