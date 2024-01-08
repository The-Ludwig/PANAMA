"""
Some constants used across multiple modules
"""
from particle import PDGID, Particle

D0_LIFETIME = Particle.from_name("D0").lifetime

DEFAULT_RUN_HEADER_FEATURES = [
    "run_number",
    "date",
    "version",
    "n_observation_levels",
    "observation_height",
    "energy_spectrum_slope",
    "energy_min",
    "energy_max",
    "energy_cutoff_hadrons",
    "energy_cutoff_muons",
    "energy_cutoff_electrons",
    "energy_cutoff_photons",
    "n_showers",
]
DEFAULT_EVENT_HEADER_FEATURES = [
    "event_number",
    "run_number",
    "particle_id",
    "total_energy",
    "starting_altitude",
    "first_interaction_height",
    "momentum_x",
    "momentum_y",
    "momentum_minus_z",
    "zenith",
    "azimuth",
    "low_energy_hadron_model",
    "high_energy_hadron_model",
    "sybill_interaction_flag",
    "sybill_cross_section_flag",
    "explicit_charm_generation_flag",
]
CORSIKA_FIELD_BYTE_LEN = 4

PDGID_ERROR_VAL = 0

PDGID_PROTON_1 = PDGID(2212)
PDGID_PROTON_2 = PDGID(1000010010)

# pion, kaon, 0, K(L), K(S)
PDGIDS_PION_KAON = [211, 321, PDGID_ERROR_VAL, 130, 310]
