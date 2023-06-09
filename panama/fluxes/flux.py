"""
Implementations of some fluxes, heavily inspired from the crflux package.
Care is taken to make the flux models fast enough to be able to apply them
to millions of data points when using numpy.
This should make them applicable for reweighting.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import numpy as np
from numpy.typing import ArrayLike
from particle import PDGID, Particle

from ..constants import PDGID_PROTON_1, PDGID_PROTON_2


class Flux(ABC):
    """
    Abstract class to model a particle flux of some sort.
    """

    REFERENCE = ""

    def __init__(self, validPDGIDs: list[PDGID]):
        self.validPDGIDs = validPDGIDs

    @abstractmethod
    def _flux(self, id: PDGID, E: ArrayLike, **kwargs: Any) -> ArrayLike:
        """Return a numpy array of the flux in $\frac{1}{m^2 s sr GeV}$
        This should not be used directly and should not throw any error for non-valid PDGids.
        This is handled by Flux.flux
        """
        raise NotImplementedError(
            "Derived class from Flux does not implement the _flux method, which is required."
        )

    def flux(
        self, id: PDGID, E: ArrayLike, check_valid_pdgid: bool = True, **kwargs: Any
    ) -> ArrayLike:
        """Returns the differential flux in $\frac{1}{m^2 s sr GeV}$ for particle with PDGid id."""

        # the proton has 2 valid PDGIDs: as a proton (2212) or as a Hydrogen nucleus (1000010010)
        # correct for that fact
        if (
            id == PDGID_PROTON_1
            and id not in self.validPDGIDs
            and PDGID_PROTON_2 in self.validPDGIDs
        ):
            id = PDGID_PROTON_2
        elif (
            id == PDGID_PROTON_2
            and id not in self.validPDGIDs
            and PDGID_PROTON_1 in self.validPDGIDs
        ):
            id = PDGID_PROTON_1

        if id not in self.validPDGIDs:
            if check_valid_pdgid:
                raise ValueError(
                    f"PDGid {id} ({Particle.from_pdgid(id).name}) not valid for model {self.__class__}. If you want to return flux 0 for invalid PDGids use `check_valid_pdgid = False`."
                )
            else:
                return np.zeros(shape=E.shape)

        return self._flux(id, E=E, **kwargs)

    def total_flux(self, E: ArrayLike, **kwargs: Any) -> ArrayLike:
        """Returns the total differential flux in $\frac{1}{m^2 s sr GeV}$."""
        total_flux = self._flux(self.validPDGIDs[0], E=E, **kwargs)
        for id in self.validPDGIDs[1:]:
            total_flux += self._flux(id, E=E, **kwargs)

        return total_flux
