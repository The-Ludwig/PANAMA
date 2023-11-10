from fluxcomp import (
    H3a,
    H4a,
    TIG,
    TIGCutoff,
    GlobalSplineFit,
    GlobalFitGST,
    CosmicRayFlux,
    muon_fluxes,
)
from fluxcomp.cosmic_ray_fluxes import BrokenPowerLaw
from fluxcomp.flux import Flux
import numpy as np
from particle.pdgid import literals
from typing import ClassVar
import pytest
from panama.constants import PDGID_PROTON_1, PDGID_PROTON_2

DEFAULT_ENERGY_RANGE = np.geomspace(10, 1e10)


def test_electron_flux(e=DEFAULT_ENERGY_RANGE):
    class EFlux(CosmicRayFlux):
        VALID_PDGIDS: ClassVar = [literals.e_minus]

        def __init__(self):
            super().__init__(EFlux.VALID_PDGIDS)

        def _flux(self, id, E, **kwargs):
            if id in self.VALID_PDGIDS:
                return E**-2
            else:
                return E**0 - 1

    model = EFlux()

    assert np.sum(model.flux(literals.proton, e, check_valid_pdgid=False)) == 0
    assert np.all(model.total_flux(e, check_valid_pdgid=False) == e**-2)
    assert np.sum(model.total_p_and_n_flux(e)) == 0


def test_broken_power_law(e=DEFAULT_ENERGY_RANGE):
    with pytest.raises(ValueError, match="Every dict"):
        _model = BrokenPowerLaw(
            validPDGIDs=[11],
            gammas={12: [3]},
            normalizations={11: [1.7, 174]},
            energies={11: [5e6]},
            cutoff={11: None},
        )

    with pytest.raises(ValueError, match="same length"):
        _model = BrokenPowerLaw(
            validPDGIDs=[11],
            gammas={11: [3]},
            normalizations={11: [1.7, 174]},
            energies={11: [5e6]},
            cutoff={11: None},
        )

    model = BrokenPowerLaw(
        validPDGIDs=[11, 12],
        gammas={11: [3, 7, 9], 12: [1, 8]},
        normalizations={11: [1.7, 174, 1740], 12: [1.7, 174]},
        energies={11: [5e6, 5e8], 12: [5e6]},
        cutoff={11: None, 12: None},
    )

    model.flux(12, e)
    model.flux(11, e)


def test_not_implemented(e=DEFAULT_ENERGY_RANGE):
    class QuatschFlux(CosmicRayFlux):
        VALID_PDGIDS: ClassVar = [literals.e_minus]

        def __init__(self):
            super().__init__(QuatschFlux.VALID_PDGIDS)

        def _flux(self, id, E, **kwargs):
            return super()._flux(id, E)

    model = QuatschFlux()

    with pytest.raises(NotImplementedError, match="Derived class from Flux does not"):
        model.total_flux(e)


def test_H3a(e=DEFAULT_ENERGY_RANGE):
    model = H3a()

    model.flux(literals.proton, e)
    model.total_flux(e)
    model.total_p_and_n_flux(e)


def test_not_valid_pdgid(e=DEFAULT_ENERGY_RANGE):
    model = H3a()

    with pytest.raises(ValueError, match="check_valid_pdgid"):
        model.flux(1, e)


def test_proton_pdg_degeneracy(e=DEFAULT_ENERGY_RANGE):
    model_1 = BrokenPowerLaw(
        validPDGIDs=[PDGID_PROTON_1],
        gammas={PDGID_PROTON_1: [3, 7, 9]},
        normalizations={PDGID_PROTON_1: [1.7, 174, 1740]},
        energies={PDGID_PROTON_1: [5e6, 5e8]},
        cutoff={PDGID_PROTON_1: None},
    )
    f_1 = model_1.flux(PDGID_PROTON_2, e)

    model_2 = BrokenPowerLaw(
        validPDGIDs=[PDGID_PROTON_2],
        gammas={PDGID_PROTON_2: [3, 7, 9]},
        normalizations={PDGID_PROTON_2: [1.7, 174, 1740]},
        energies={PDGID_PROTON_2: [5e6, 5e8]},
        cutoff={PDGID_PROTON_2: None},
    )
    f_2 = model_1.flux(PDGID_PROTON_1, e)

    assert np.all(f_1 == f_2)


def test_H4a(e=DEFAULT_ENERGY_RANGE):
    model = H4a()

    model.flux(literals.proton, e)
    model.total_flux(e)
    model.total_p_and_n_flux(e)


def test_TIG(e=DEFAULT_ENERGY_RANGE):
    model = TIG()

    model.flux(literals.proton, e)
    model.total_flux(e)
    model.total_p_and_n_flux(e)


def test_TIGCutoff(e=DEFAULT_ENERGY_RANGE):
    model = TIGCutoff()

    model.flux(literals.proton, e)
    model.total_flux(e)
    model.total_p_and_n_flux(e)


def test_GlobalSplineFit(e=DEFAULT_ENERGY_RANGE):
    model = GlobalSplineFit()

    model.flux(literals.proton, e)
    model.total_flux(e)
    model.total_p_and_n_flux(e)


def test_GST(e=DEFAULT_ENERGY_RANGE):
    model = GlobalFitGST()

    model.flux(literals.proton, e)
    model.total_flux(e)
    model.total_p_and_n_flux(e)


def test_MuonFlux_HighEnergy(e=DEFAULT_ENERGY_RANGE):
    model = muon_fluxes.GaisserFlatEarthHighEnergy()

    model.flux(literals.mu_minus, e)
    model.total_flux(e)


def test_MuonFlux(e=DEFAULT_ENERGY_RANGE):
    model = muon_fluxes.GaisserFlatEarth()

    model.flux(literals.mu_plus, e)
    model.total_flux(e)
