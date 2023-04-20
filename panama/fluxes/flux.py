"""
Implementations of some fluxes, heavily inspired from the crflux package.
Care is taken to make the flux models fast enough to be able to apply them 
to millions of data points when using numpy.
This should make them applicable for reweighting.
"""
from __future__ import annotations

import numpy as np
from abc import ABC, abstractmethod
from crflux.models import PrimaryFlux
from particle import Particle, PDGID, pdgid
from typing import List

class Flux(ABC):
    """
    Abstract class to model a particle flux of some sort.
    """
    
    REFERENCE = ""
    
    def __init__(self, validPDGIDs: List[PDGID]):
        self.validPDGIDs = validPDGIDs

    @abstractmethod
    def __flux(self, id: PDGID, *args,  **kwargs) -> np.ndarray:
        """ Return a numpy array of the flux in $\frac{1}{m^2 s sr GeV}$ 
        This should not be used directly and should not throw any error for non-valid PDGids.
        This is handled by Flux.flux
        """
        raise NotImplemented("Derived class from Flux does not implement the __flux method, which is required.")

    def flux(self, id: PDGID, E: np.ndarray, *args, check_valid_pdgid: bool=True, **kwargs) -> np.ndarray:
        """ Returns the differential flux in $\frac{1}{m^2 s sr GeV}$ for particle with PDGid id. """
        if id not in self.validPDGIDs:
            if check_valid_pdgid:
                raise ValueError(f"PDGid {id} ({Particle.from_pdgid(pdgid).name}) not valid for model {self.__class__}. If you want to return flux 0 for invalid PDGids use `check_valid_pdgid = False`.")
            else:
                return np.zeros(shape=E.shape)

        return self.__flux(id, E=E, *args, **kwargs)


    def total_flux(self, E: np.ndarray , *args, **kwargs) -> np.ndarray:
        """ Returns the total differential flux in $\frac{1}{m^2 s sr GeV}$."""
        total_flux = np.zeros(E.shape)
        for id in self.validPDGIDs:
            total_flux += self.__flux(id, E=E, *args, **kwargs)

        return total_flux
    
