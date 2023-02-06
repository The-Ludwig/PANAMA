"""
Faster implementations of some fluxes from the crflux package.
I basically only used numpy at the right places, that was it.
"""
from crflux.models import PrimaryFlux
import numpy as np


class FastPrimaryFlux(PrimaryFlux):
    """
    Fast version of PrimaryFlux, which uses numpy where applicable.
    """

    def p_and_n_flux(self, E):
        """Returns tuple with proton fraction, proton flux and neutron flux.

        The proton fraction is defined as :math:`\\frac{\\Phi_p}{\\Phi_p + \\Phi_n}`.

        Args:
          E (float): laboratory energy of nucleons in GeV
        Returns:
          (float,float,float): proton fraction, proton flux, neutron flux
        """
        za = self.Z_A
        nuc_flux = self.nucleus_flux

        p_flux = sum(
            [
                za(corsika_id)[0]
                * za(corsika_id)[1]
                * nuc_flux(corsika_id, E * za(corsika_id)[1])
                for corsika_id in self.nucleus_ids
            ]
        )

        n_flux = sum(
            [
                (za(corsika_id)[1] - za(corsika_id)[0])
                * za(corsika_id)[1]
                * nuc_flux(corsika_id, E * za(corsika_id)[1])
                for corsika_id in self.nucleus_ids
            ]
        )

        return p_flux / (p_flux + n_flux), p_flux, n_flux


class FastHillasGaisser2012(FastPrimaryFlux):
    """Gaisser, T.K., Astroparticle Physics 35, 801 (2012).

    Fast version of HillasGaisser2012,if numpy is used.

    Args:
      model (str): can be either H3a or H4a.
    """

    def __init__(self, model="H4a"):

        self.name = "Hillas-Gaisser (" + model + ")"
        self.sname = model
        self.model = model
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

    def nucleus_flux(self, corsika_id, E):
        if corsika_id not in self.params:
            raise Exception("Unknown CorsikaID for model.")

        if isinstance(E, np.ndarray):
            flux = np.zeros(E.shape)
        else:
            flux = 0.0

        for i in range(1, 4):
            p = self.params[corsika_id][i]
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
            return np.zeros_like(E)

        le = E < self.params["trans"]
        he = E >= self.params["trans"]

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
            return np.zeros_like(E)

        if not isinstance(E, np.ndarray):
            E = np.atleast_1d(E)
        le = E < self.params["trans"]
        he = E >= self.params["trans"]
        co = E > self.params["cutoff"]

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
