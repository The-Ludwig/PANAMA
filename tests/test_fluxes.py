from panama.fluxes import H3a, H4a, TIG, TIGCutoff, GlobalSplineFit
from panama.fluxes import muon_fluxes
import numpy as np
from particle.pdgid import literals

DEFAULT_ENERGY_RANGE = np.geomspace(10, 1e10)

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


def test_MuonFlux_HighEnergy(e = DEFAULT_ENERGY_RANGE):
    model = muon_fluxes.GaisserFlatEarthHighEnergy()

    model.flux(literals.mu_minus, e)
    model.total_flux(e)


def test_MuonFlux(e = DEFAULT_ENERGY_RANGE):
    model = muon_fluxes.GaisserFlatEarth()

    model.flux(literals.mu_plus, e)
    model.total_flux(e)
