# Only available in python 3.10
try:
    from importlib.metadata import packages_distributions  # , version

    pkgs = packages_distributions()  # pragma: no cover
except ImportError:
    pkgs = {}

__distribution__ = pkgs["panama"][0] if "panama" in pkgs else "corsika-panama"

# __version__ = version(__distribution__)
__version__ = "1.0.0"

LOGO_TEMPLATE = r"""
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
  `---`                   '---'                       '---'                                     {}
"""

__logo__ = LOGO_TEMPLATE.format(f"v{__version__}")
