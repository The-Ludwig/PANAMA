# PAN*das* A*nd* M*ulticore utils for corsik*A*7*

[Documentation ![Read the Docs](https://img.shields.io/readthedocs/panama?style=for-the-badge)](https://panama.readthedocs.io/en/latest/)

[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/The-Ludwig/PANAMA/ci.yml?style=for-the-badge)](https://github.com/The-Ludwig/PANAMA/actions/workflows/ci.yml)
[![Codecov](https://img.shields.io/codecov/c/github/The-Ludwig/PANAMA?label=test%20coverage&style=for-the-badge)](https://app.codecov.io/gh/The-Ludwig/PANAMA)
[![PyPI](https://img.shields.io/pypi/v/corsika-panama?style=for-the-badge)](https://pypi.org/project/corsika-panama/)

[![GitHub issues](https://img.shields.io/github/issues-raw/The-Ludwig/PANAMA?style=for-the-badge)](https://github.com/The-Ludwig/PANAMA/issues)
[![GitHub](https://img.shields.io/github/license/The-Ludwig/PANAMA?style=for-the-badge)](https://github.com/The-Ludwig/PANAMA/blob/main/LICENSE)
[![Codestyle](https://img.shields.io/badge/codesyle-Black-black.svg?style=for-the-badge)](https://github.com/psf/black)

Thanks [@Jean1995](https://github.com/Jean1995) for the silly naming idea.

## Installation

```
pip install corsika-panama
```

## Features

### Run CORSIKA7 on multiple cores

You need to have [`CORSIKA7`](https://www.iap.kit.edu/corsika/79.php) installed to run this.

Running 100 showers on 4 cores with primary being proton:

```sh
$ panama run --corsika path/to/corsika7/executable -j4 ./tests/files/example_corsika.template
83%|████████████████████████████████████████████████████▋        | 83.0/100 [00:13<00:02, 6.36shower/s]
Jobs should be nearly finished, now we wait for them to exit
All jobs terminated, cleanup now
```

Injecting 5 different primaries (Proton, Helium-4, Carbon-12, Silicon-28, Iron-54 roughly aligning with grouping in H3a) with each primary shower taking 10 jobs:

```sh
$ panama run --corsika corsika-77420/run/corsika77420Linux_SIBYLL_urqmd --jobs 10 --primary ""{2212: 500, 1000020040: 250, 1000060120: 50, 1000140280: 50, 1000260540: 50}"" ./tests/files/example_corsika.template
...
```

### Convert CORSIKA7 DAT files to hdf5 files

```sh
$ panama hdf5 path/to/corsika/dat/files/DAT* output.hdf5
```

The data is available under the `run_header` `event_header` and `particles` key.

### Read CORSIKA7 DAT files to pandas dataframes

Example: Calculate mean energy in the corsika files created in the example above:

```
In [1]: import panama as pn

In [2]: run_header, event_header, particles = pn.read_DAT(glob="corsika_output/DAT*")
100%|████████████████████████████████████████████████████████████| 2000/2000.0 [00:00<00:00, 10127.45it/s]
In [3]: particles["energy"].mean()
Out[3]: 26525.611020413744
```

`run_header`, `event_header` and `particles` are all [pandas.DataFrames](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.html) and can conveniently be used.

If `CORSIKA7` is compiled with the `EHIST` option, then the mother particles are automatically deleted, by default (this behaviour can be changed with`drop_mothers=False`).
If you want additional columns in the real particles storing the mother information use `mother_columns=True`.

### Weighting to primary spectrum

This packages also provides facility to add a `weight` column to the dataframe, so you can look at corsika-output
in physical flux in terms of $(\mathrm{m^2} \mathrm{s}\ \mathrm{sr}\ \mathrm{GeV})^{-1}$.
Using the example above, to get the whole physical flux in the complete simulated energy region:

```
In [1]: import panama as pn

In [2]: run_header, event_header, particles = pn.read_DAT(glob="corsika_output/DAT*")
100%|████████████████████████████████████████████████████████████| 2000/2000.0 [00:00<00:00, 10127.45it/s]
In [3]: pn.add_weight(run_header, event_header, particles)

In [4]: particles["weight"].sum()*(run_header["energy_max"]-run_header["energy_min"])
Out[4]:
run_number
1.0    1234.693481
0.0    1234.693481
3.0    1234.693481
2.0    1234.693481
dtype: float32

```

Which is in units of $(\mathrm{m^2}\ \mathrm{s}\ \mathrm{sr})^{-1}$. We get a result for each run, since
in theory we could have different energy regions. Here, we do not, so the result is always equal.

Weighting can be applied to different primaries, also, if they are known by the flux model.

`add_weight` can also be applied to dataframes loaded in from hdf5 files produced with PANAMA.

TODO: Better documentation of weighting (what is weighted, how, proton/neutrons, area...?)

#### Notes:

This started a little while ago while I was looking into the `EHIST` option
of corsika.
I wanted a way of conveniently running CORSIKA7 on more than 1 core.
I ended in the same place where most CORSIKA7 users end (see e.g. [fact-project/corsika_wrapper](https://github.com/fact-project/corsika_wrapper))
and wrote a small wrapper.

read_DAT made possible by [cta-observatory/pycorsikaio](https://github.com/cta-observatory/pycorsikaio).

#### Pitfalls

- The whole `run` folder of CORSIKA7 must be copied for each process, so very high parallel runs have high overhead
- If you simulate to low energies, python can't seem to hold up with the corsika output to `stdin` and essentially slows down corsika this is still a bug in investigation #1

## What this is not

Bug-free or stable
