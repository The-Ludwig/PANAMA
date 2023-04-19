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
    def flux(self, pdgid: PDGID, *args,  **kwargs) -> np.ndarray:
        pass

    def total_flux(self, E: np.ndarray , *args, **kwargs) -> np.ndarray:
        total_flux = np.zeros(E.shape)
        for id in self.validPDGIDs:
            total_flux += self.flux(id, E, *args, **kwargs)

        return total_flux
    
class CosmicRayFlux(Flux, ABC):

    def __init__(self, validPDGIDs: List[PDGID]):
        
        self.valid_leptons = (pdgid.literals.e_minus, pdgid.literals.e_plus)

        for id in validPDGIDs:
            if not (id.is_nucleus or id in self.valid_leptons):
                raise ValueError(f"{Particle.from_pdgid(id).name} (pdgid: {id}) is not a cosmic ray.")
        super(validPDGIDs)

    def total_p_and_n_flux(self, E: float | np.ndarray):
        """Returns tuple with the total number of protons and neutrons in the flux."""
        
        if isinstance(E, float):
            E = np.array([E])

        p_flux = np.zeros(shape=E.shape)
        n_flux = np.zeros(shape=E.shape)
        
        for id in self.validPDGIDs: 
            if id in self.valid_leptons:
                continue
            nucleon_flux = self.flux(id, E=E*id.A)     
            p_flux += id.Z*nucleon_flux
            n_flux += (id.A-id.Z)*nucleon_flux

        return p_flux, n_flux 

        za = self.Z_A
        nuc_flux = self.nucleus_flux

class HillasGaisser(CosmicRayFlux, ABC):
    """Gaisser, T.K., Astroparticle Physics 35, 801 (2012).

    Args:
      model (str): can be either H3a or H4a.
    """
    
    REFERENCE = "https://doi.org/10.1016/j.astropartphys.2012.02.010"

    def __init__(self):
        self.params = {}
        self.rid_cutoff = {}

        mass_comp = [14, 402, 1206, 2814, 5426]
        for mcomp in mass_comp:
            self.params[mcomp] = {}

        self.rid_cutoff[1] = 4e6
        self.rid_cutoff[2] = 30e6
        self.rid_cutoff[3] = 2e9
        self.params[14][1] = (7860, 1.66, 1)  # H
        self.params[402][1] = (3550, 1.58, 2)  # He
        self.params[1206][1] = (2200, 1.63, 6)  # CNO
        self.params[2814][1] = (1430, 1.67, 14)  # MgAlSi
        self.params[5426][1] = (2120, 1.63, 26)  # Fe

        self.params[14][2] = (20, 1.4, 1)  # H
        self.params[402][2] = (20, 1.4, 2)  # He
        self.params[1206][2] = (13.4, 1.4, 6)  # CNO
        self.params[2814][2] = (13.4, 1.4, 14)  # MgAlSi
        self.params[5426][2] = (13.4, 1.4, 26)  # Fe

        if self.model == "H3a":
            self.rid_cutoff[3] = 2e9
            self.params[14][3] = (1.7, 1.4, 1)  # H
            self.params[402][3] = (1.7, 1.4, 2)  # He
            self.params[1206][3] = (1.14, 1.4, 6)  # CNO
            self.params[2814][3] = (1.14, 1.4, 14)  # MgAlSi
            self.params[5426][3] = (1.14, 1.4, 26)  # Fe
        elif self.model == "H4a":
            self.rid_cutoff[3] = 60e9
            self.params[14][3] = (200.0, 1.6, 1)  # H
            self.params[402][3] = (0, 1.4, 2)  # He
            self.params[1206][3] = (0, 1.4, 6)  # CNO
            self.params[2814][3] = (0, 1.4, 14)  # MgAlSi
            self.params[5426][3] = (0, 1.4, 26)  # Fe
        else:
            raise Exception("HillasGaisser2012(): Unknown model version requested.")

        self.nucleus_ids = list(self.params.keys())

    def flux(self, id: PDGID, E: np.ndarray) -> np.ndarray:
        if corsika_id not in self.validPDGIDs:
            raise ValueError(f"Unknown PDGID {id} for model.")

        flux = np.zeros(E.shape)

        for i in range(1, 4):
            p = self.params[id][i]
            flux += p[0] * E ** (-p[1] - 1.0) * np.exp(-E / p[2] / self.rid_cutoff[i])
        return flux


class FastThunman(FastPrimaryFlux):
    """Popular broken power-law flux model.
    The parameters of this model are taken from the prompt flux calculation
    paper by M. Thunman, G. Ingelman, and P. Gondolo, Astroparticle Physics 5, 309 (1996).
    The model contians only protons with a power-law index of -2.7 below the knee,
    located at 5 PeV, and -3.0 for energies higher than that.
    """

    name = "Thunman et al. ('96)"
    sname = "TIG"

    def __init__(self, *args, **kwargs):
        self.params = {}
        self.params["low_e"] = (1e4 * 1.7, -2.7)
        self.params["high_e"] = (1e4 * 174, -3.0)
        self.params["trans"] = 5e6

        self.nucleus_ids = [14]

    def nucleus_flux(self, corsika_id, E):
        """Broken power law spectrum for protons."""
        #         E = np.atleast_1d(E)
        if corsika_id != 14:
            flux = np.zeros(E.shape) if isinstance(E, np.ndarray) else 0.0
            return flux

        le = self.params["trans"] > E
        he = self.params["trans"] <= E

        flux = E.copy()
        flux[le] = self.params["low_e"][0] * E[le] ** self.params["low_e"][1]
        flux[he] = self.params["high_e"][0] * E[he] ** self.params["high_e"][1]
        return flux

        #     self.flux(E[he], corsika_id)))

        # if np.atleast_1d(E) < self.params["trans"]:
        #     return self.params['low_e'][0] * E**(self.params['low_e'][1])
        # else:
        #     return self.params['high_e'][0] * E**(self.params['high_e'][1])


class FastThunmanCO(FastPrimaryFlux):
    """Popular broken power-law flux model.
    The parameters of this model are taken from the prompt flux calculation
    paper by M. Thunman, G. Ingelman, and P. Gondolo, Astroparticle Physics 5, 309 (1996).
    The model contians only protons with a power-law index of -2.7 below the knee,
    located at 5 PeV, and -3.0 for energies higher than that.
    """

    name = "Thunman et al. ('96)"
    sname = "TIG"

    def __init__(self, cutoff=1e9, *args, **kwargs):
        self.params = {}
        self.params["low_e"] = (1e4 * 1.7, -2.7)
        self.params["high_e"] = (1e4 * 174, -3.0)
        self.params["trans"] = 5e6
        self.params["cutoff"] = cutoff

        self.nucleus_ids = [14]

    def nucleus_flux(self, corsika_id, E):
        """Broken power law spectrum for protons."""
        #         E = np.atleast_1d(E)
        if corsika_id != 14:
            flux = np.zeros(E.shape) if isinstance(E, np.ndarray) else 0.0
            return flux

        if not isinstance(E, np.ndarray):
            E = np.atleast_1d(E)
        le = self.params["trans"] > E
        he = self.params["trans"] <= E
        co = self.params["cutoff"] < E

        flux = E.copy()
        flux[le] = self.params["low_e"][0] * E[le] ** self.params["low_e"][1]
        flux[he] = self.params["high_e"][0] * E[he] ** self.params["high_e"][1]
        flux[co] = 0
        return flux

        #     self.flux(E[he], corsika_id)))

        # if np.atleast_1d(E) < self.params["trans"]:
        #     return self.params['low_e'][0] * E**(self.params['low_e'][1])
        # else:
        #     return self.params['high_e'][0] * E**(self.params['high_e'][1])
