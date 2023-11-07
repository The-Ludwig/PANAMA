from panama.fluxes import H3a, H4a, TIG, TIGCutoff, GlobalSplineFit, GlobalFitGST, CosmicRayFlux
from panama.fluxes import muon_fluxes
import numpy as np
from particle.pdgid import literals
from typing import ClassVar

DEFAULT_ENERGY_RANGE = np.geomspace(10, 1e10)

def test_electron_flux(e = DEFAULT_ENERGY_RANGE):
    class EFlux(CosmicRayFlux):
        VALID_PDGIDS: ClassVar = [literals.e_minus]
        
        def __init__(self):
            super().__init__(EFlux.VALID_PDGIDS)

        def _flux(self, id, E, **kwargs):
            if id in self.VALID_PDGIDS:
                return E**-2
            else:
                return E**0-1

    model = EFlux()

    assert np.sum(model.flux(literals.proton, e, check_valid_pdgid=False)) == 0
    assert np.all(model.total_flux(e, check_valid_pdgid=False) == e**-2)
    assert np.sum(model.total_p_and_n_flux(e)) == 0

def test_H3a(e = DEFAULT_ENERGY_RANGE):
    model = H3a()

    model.flux(literals.proton, e)
    model.total_flux(e)
    model.total_p_and_n_flux(e)


def test_H4a(e = DEFAULT_ENERGY_RANGE):
    model = H4a()

    model.flux(literals.proton, e)
    model.total_flux(e)
    model.total_p_and_n_flux(e)


def test_TIG(e = DEFAULT_ENERGY_RANGE):
    model = TIG()

    model.flux(literals.proton, e)
    model.total_flux(e)
    model.total_p_and_n_flux(e)


def test_TIGCutoff(e = DEFAULT_ENERGY_RANGE):
    model = TIGCutoff()

    model.flux(literals.proton, e)
    model.total_flux(e)
    model.total_p_and_n_flux(e)


def test_GlobalSplineFit(e = DEFAULT_ENERGY_RANGE):
    model = GlobalSplineFit()

    model.flux(literals.proton, e)
    model.total_flux(e)
    model.total_p_and_n_flux(e)


def test_GST(e = DEFAULT_ENERGY_RANGE):
    model = GlobalFitGST()

    model.flux(literals.proton, e)
    model.total_flux(e)
    model.total_p_and_n_flux(e)


def test_MuonFlux_HighEnergy(e = DEFAULT_ENERGY_RANGE):
    model = muon_fluxes.GaisserFlatEarthHighEnergy()

    model.flux(literals.mu_minus, e)
    model.total_flux(e)


def test_MuonFlux(e = DEFAULT_ENERGY_RANGE):
    model = muon_fluxes.GaisserFlatEarth()

    model.flux(literals.mu_plus, e)
    model.total_flux(e)
