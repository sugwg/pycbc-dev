# Copyright (C) 2012  Alex Nitz
#
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 3 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
# Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.


#
# =============================================================================
#
#                                   Preamble
#
# =============================================================================
#
"""
"""
from __future__ import division
import lal


def mass1_mass2_to_tau0_tau3(mass1, mass2, f_lower):
    m_total = mass1 + mass2
    mu = mass1 * mass2 / m_total
    eta = mu / m_total
    tau3 = 1.0 / (8.0 * (lal.LAL_PI * lal.LAL_PI * f_lower**5)**(1.0/3.0) * m_total**(2.0/3.0) * eta)
    tau0 = 5.0 / (256.0 * (lal.LAL_PI * f_lower) ** (8.0/3.0) * m_total**(5.0/3.0) * eta)
    return tau0,tau3


def tau0_tau3_to_mtotal_eta(tau0, tau3, f_lower):
    t0q = 5.0 / (256.0 * (lal.LAL_PI * f_lower) ** (8.0/3.0) * tau0)
    t3q = 1.0 / (8.0 * (lal.LAL_PI * lal.LAL_PI * f_lower**5) ** (1.0/3.0 ) * tau3)
    eta = t3q * ( t0q / t3q ) ** (-2.0/3.0) ;
    m_total = t0q / t3q;
    return m_total,eta


def tau0_tau3_to_mass1_mass2(tau0, tau3, f_lower):
    t0q = 5.0 / (256.0 * ( lal.LAL_PI * f_lower)**( 8.0/3.0) * tau0)
    t3q = 1.0 / (8.0 * (lal.LAL_PI * lal.LAL_PI * f_lower **5.0)**(1.0/3.0 ) * tau3)
    eta = t3q * (t0q/t3q)**( -2.0/3.0 )
    m_total = t0q / t3q
    mass1 = 0.5 * m_total * (1.0 + (1.0-4.0*eta)**( 0.5 ))
    mass2 = 0.5 * m_total * (1.0 - (1.0-4.0*eta)**( 0.5 ))
    return mass1,mass2


def mass1_mass2_to_mtotal_eta(mass1, mass2):
    m_total = mass1 + mass2;
    eta = (mass1 * mass2) / (m_total * m_total)
    return m_total,eta


def mtotal_eta_to_mass1_mass2(m_total, eta):
    mass1 = 0.5 * m_total * (1.0 + (1.0 - 4.0 * eta)**0.5)
    mass2 = 0.5 * m_total * (1.0 - (1.0 - 4.0 * eta)**0.5)
    return mass1,mass2


def mchirp_eta_to_mass1_mass2(m_chirp, eta):
    M = m_chirp / (eta ** (3.0/5.0))
    return mtotal_eta_to_mass1_mass2( M, eta )


def mass1_mass2_to_mchirp_eta(mass1, mass2):
    M = mass1 + mass2
    mu = mass1 * mass2 / M
    eta = mu / M
    m_chirp = mu ** (3.0/5.0) * M ** (2.0/5.0)
    return m_chirp, eta


def solar_mass_to_kg(solar_masses):
    return solar_masses * lal.LAL_MSUN_SI

    
def parsecs_to_meters(distance):
    return distance *lal.LAL_PC_SI
