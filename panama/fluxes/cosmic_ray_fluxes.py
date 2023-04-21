from __future__ import annotations

from abc import ABC
from pathlib import Path
from typing import Any

import numpy as np
from particle import PDGID, Particle
from particle.pdgid import literals
from scipy.interpolate import CubicSpline

from .flux import Flux


class CosmicRayFlux(Flux, ABC):
    def __init__(self, validPDGIDs: list[PDGID]) -> None:
        self.valid_leptons = (literals.e_minus, literals.e_plus)

        for id in validPDGIDs:
            if not (id.is_nucleus or id in self.valid_leptons):
                raise ValueError(
                    f"{Particle.from_pdgid(id).name} (pdgid: {id}) is not a cosmic ray."
                )
        super().__init__(validPDGIDs)

    def total_p_and_n_flux(self, E: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Returns tuple with the total number of protons and neutrons in the flux."""

        p_flux = np.zeros(shape=E.shape)
        n_flux = np.zeros(shape=E.shape)

        for id in self.validPDGIDs:
            if id in self.valid_leptons:
                continue
            nucleon_flux = id.A * self.flux(
                id, E=E * id.A
            )  # extra factor of A, since flux is differential in E
            p_flux += id.Z * nucleon_flux
            n_flux += (id.A - id.Z) * nucleon_flux

        return p_flux, n_flux


class HillasGaisser(CosmicRayFlux):
    """Gaisser, T.K., Astroparticle Physics 35, 801 (2012)."""

    REFERENCE = "https://doi.org/10.1016/j.astropartphys.2012.02.010"
    # H He CNO MgAlSi Fe
    validPDGIDs = [
        Particle.from_nucleus_info(z, a).pdgid
        for z, a in [(1, 1), (2, 4), (6, 12), (14, 28), (26, 54)]
    ]
    rigidity_cutoff = [4e6, 30e6, 2e9]  # GeV

    def __init__(self, ai3: list[float], gamma_pop_3: float) -> None:
        super().__init__(HillasGaisser.validPDGIDs)
        self.aij = {}
        # see Table 1 of reference
        self.aij[self.validPDGIDs[0]] = [7860.0, 20.0]
        self.aij[self.validPDGIDs[1]] = [3550, 20]
        self.aij[self.validPDGIDs[2]] = [2200, 13.4]
        self.aij[self.validPDGIDs[3]] = [1430, 13.4]
        self.aij[self.validPDGIDs[4]] = [2120, 13.4]

        self.gammaij = {}
        self.gammaij[self.validPDGIDs[0]] = [1.66, 1.4]
        self.gammaij[self.validPDGIDs[1]] = [1.58, 1.4]
        self.gammaij[self.validPDGIDs[2]] = [1.63, 1.4]
        self.gammaij[self.validPDGIDs[3]] = [1.67, 1.4]
        self.gammaij[self.validPDGIDs[4]] = [1.63, 1.4]

        # These will come from the instances
        for id in self.validPDGIDs:
            self.gammaij[id].append(gamma_pop_3)

        for id, ai3_ in zip(self.validPDGIDs, ai3):
            self.aij[id].append(ai3_)

    def _flux(self, id: PDGID, E: np.ndarray, **kwargs: Any) -> np.ndarray:
        flux = np.zeros(E.shape)

        for j in range(3):
            flux += (
                self.aij[id][j]
                * E ** (-self.gammaij[id][j] - 1.0)
                * np.exp(-E / id.Z / self.rigidity_cutoff[j])
            )
        return flux


class H3a(HillasGaisser):
    def __init__(self) -> None:
        super().__init__([1.7, 1.7, 1.14, 1.14, 1.14], 1.4)


class H4a(HillasGaisser):
    def __init__(self) -> None:
        super().__init__([200, 0, 0, 0, 0], 1.6)


class BrokenPowerLaw(CosmicRayFlux):
    def __init__(
        self,
        validPDGIDs: list[PDGID],
        gammas: dict[PDGID, list[float]],
        normalizations: dict[PDGID, list[float]],
        energies: dict[PDGID, list[float]],
        cutoff: dict[PDGID, float | None],
    ) -> None:
        super().__init__(validPDGIDs)

        for id in self.validPDGIDs:
            for d in (gammas, normalizations, energies, cutoff):
                assert isinstance(d, dict)
                if id not in d:
                    raise ValueError(
                        "Every dict of BrokenPowerLaw must have an entry for each valid PDGID"
                    )
            if len(gammas[id]) != len(normalizations[id]) or len(gammas[id]) - 1 != len(
                energies[id]
            ):
                raise ValueError(
                    "Normalizations and indices must have the same length and energies must have one less value"
                )

        self.gammas = gammas
        self.normalizations = normalizations
        self.energies = energies
        self.cutoff = cutoff

    def _flux(self, id: PDGID, E: np.ndarray, **kwargs: Any) -> np.ndarray:
        flux = np.empty(shape=E.shape)

        lowest_mask = self.energies[id][0] >= E
        flux[lowest_mask] = self.normalizations[id][0] * E[lowest_mask] ** (
            -self.gammas[id][0]
        )

        for norm, gamma, e_low, e_high in zip(
            self.normalizations[id][1:-1],
            self.gammas[id][1:-1],
            self.energies[id][:-1],
            self.energies[id][1:],
        ):
            mask = e_low < E <= e_high
            flux[mask] = norm * E[mask] ** (-gamma)

        highest_mask = self.energies[id][-1] < E
        flux[highest_mask] = self.normalizations[id][-1] * E[highest_mask] ** (
            -self.gammas[id][-1]
        )

        if (co := self.cutoff[id]) is not None:
            flux[co < E] = 0

        return flux * 10_000  # for 1/m^2


class TIG(BrokenPowerLaw):
    REFERENCE = "https://doi.org/10.1103/PhysRevD.54.4385"

    def __init__(self) -> None:
        proton_pdgid: PDGID = literals.proton
        super().__init__(
            validPDGIDs=[proton_pdgid],
            gammas={proton_pdgid: [2.7, 3]},
            normalizations={proton_pdgid: [1.7, 174]},
            energies={proton_pdgid: [5e6]},
            cutoff={proton_pdgid: None},
        )


class TIGCutoff(BrokenPowerLaw):
    REFERENCE = "https://doi.org/10.1103/PhysRevD.54.4385"

    def __init__(self) -> None:
        proton_pdgid: PDGID = literals.proton
        super().__init__(
            validPDGIDs=[proton_pdgid],
            gammas={proton_pdgid: [2.7, 3]},
            normalizations={proton_pdgid: [1.7, 174]},
            energies={proton_pdgid: [5e6]},
            cutoff={proton_pdgid: 1e9},
        )


class GlobalSplineFit(CosmicRayFlux):
    REFERENCE = "https://doi.org/10.48550/arXiv.1711.11432"

    z_to_a = {
        1: 1,
        2: 4,
        3: 7,
        4: 9,
        5: 11,
        6: 12,
        7: 14,
        8: 16,
        9: 19,
        10: 20,
        11: 23,
        12: 24,
        13: 27,
        14: 28,
        15: 31,
        16: 32,
        17: 35,
        18: 40,
        19: 39,
        20: 40,
        21: 45,
        22: 48,
        23: 51,
        24: 52,
        25: 55,
        26: 56,
        27: 59,
        28: 59,
    }

    def __init__(self) -> None:
        data = np.genfromtxt(Path(__file__).parent / "gsf_data_table.txt")
        self.x = data.T[0]
        self.elements = data.T[1:]
        self.spline = CubicSpline(self.x, self.elements, extrapolate=False, axis=1)

        validPDGIDs = []
        for i in range(self.elements.shape[0]):
            z = i + 1
            validPDGIDs.append(Particle.from_nucleus_info(z, self.z_to_a[z]).pdgid)
        super().__init__(validPDGIDs)

    def _flux(self, id: PDGID, E: np.ndarray, **kwargs: Any) -> np.ndarray:
        return self.spline(E)[id.Z - 1]

    def flux_all_particles(self, E: np.ndarray) -> np.ndarray:
        return self.spline(E)
