from .flux import Flux
import numpy as np
from __future__ import annotations
from particle import PDGID, Particle, pdgid
from scipy.special import gamma

class MyonFlux(Flux):
    def __init__(self):
        super(validPDGids = [pdgid.literals.mu_plus, pdgid.literals.mu_minus])


class GaisserFlatEarthHighEnergy(MyonFlux): 

    REFERENCE = "ISBN: 978-0521016469, Page 134, Eq. 6.41"

    def __init__(self):
        super()

    def __flux(self, id: PDGID, E: np.ndarray, theta: float) -> np.ndarray :
        return 10_000*0.14*E**(-2.7)*(1/(1+1.11/115*E*np.cos(theta))+0.054/(1+1.11/850*E*np.cos(theta)))


class GaisserFlatEarth(MyonFlux): 

    REFERENCE = "ISBN: 978-0521016469, Page 134, Eq. 6.41"
    
    alphaX0 = 2 # GeV
    X0 = 1030 # g/cm^2
    gamma = 2.7
    LambdaN = 100 # g/cm^2 (VERY rough! ref: p. 123 of Gaisser, table 5.4)
    epsilon_mu = 1 # GeV table 5.3

    def __init__(self):
        super()

    def __flux(self, id: PDGID, E: np.ndarray, theta: float) -> np.ndarray :
        p1 = self.epsilon_mu/(E*np.cos(theta)+self.alphaX0)
        s = (self.LambdaN * np.cos(theta)/self.X0)**p1 * (E/(E+self.alphaX0/np.cos(theta)))**(p1+self.gamma+1)*gamma(p1+1)

        return s*10_000*0.14*E**(-2.7)*(1/(1+1.11/115*E*np.cos(theta))+0.054/(1+1.11/850*E*np.cos(theta)))
