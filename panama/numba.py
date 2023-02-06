"""
I just dump my old experiments with using numba to make the row dependend calculation faster.
In the end I stayed in pure numpy using np.roll, for the better or the worse
"""

# @njit
def _mother_idx_numba(
    is_mother: np.ndarray,
    run_idx: np.ndarray,
    event_idx: np.ndarray,
    particle_idx: np.ndarray,
) -> tuple[np.ndarray]:
    """
    Numba-compatible version of mother_idx, performance boost is approx x6 (6secs->1secs),
    But UI is worse since the index can't be None (no object...), so I am just gonna eat the 6 seconds
    """
    mi_run = np.empty(run_idx.shape, dtype=run_idx.dtype)
    mi_event = np.empty(event_idx.shape, dtype=event_idx.dtype)
    mi_parti = np.empty(particle_idx.shape, dtype=particle_idx.dtype)

    mi_run[0] = -1
    mi_run[1] = -1
    mi_event[0] = -1
    mi_event[1] = -1
    mi_parti[0] = -1
    mi_parti[1] = -1

    for i in range(2, len(is_mother)):
        mi_run[i] = run_idx[i - 2] if is_mother[i - 1] and is_mother[i - 2] else -1
        mi_event[i] = event_idx[i - 2] if is_mother[i - 1] and is_mother[i - 2] else -1
        mi_parti[i] = (
            particle_idx[i - 2] if is_mother[i - 1] and is_mother[i - 2] else -1
        )

    return (mi_run, mi_event, mi_parti)


# @njit
def _mother_idx_numba_ez(
    is_mother: np.ndarray, index: np.ndarray, none_val: np.ndarray
) -> np.ndarray:
    """
    Numba-compatible version of mother_idx, performance boost is approx x6 (6secs->1secs),
    But UI is worse since the index can't be None (no object...), so I am just gonna eat the 6 seconds
    """
    mi = np.empty(index.shape, dtype=index.dtype)

    mi[0] = none_val
    mi[0] = none_val

    for i in range(2, len(is_mother)):
        mi[i] = index[i - 2] if is_mother[i - 1] and is_mother[i - 2] else none_val
    return mi


def _mother_idx(is_mother: np.ndarray, index: np.ndarray) -> np.ndarray:
    mi = np.empty(index.shape, dtype=index.dtype)
    mi[0] = None
    mi[1] = None
    for i in range(2, len(is_mother)):
        mi[i] = index[i - 2] if is_mother[i - 1] and is_mother[i - 2] else None
    return mi
