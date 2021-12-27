# -*- coding: utf-8 -*-
#    Copyright Brandon Stafford
#
#    This file is part of Pysolar.
#
#    Pysolar is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
#    (at your option) any later version.
#
#    Pysolar is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with Pysolar. If not, see <http://www.gnu.org/licenses/>.

from datetime import \
    datetime, \
    timedelta
from . import numeric as math
from . import solar, constants

# Some default constants

AM_default = 2.0             # Default air mass is 2.0
TL_default = 1.0             # Default Linke turbidity factor is 1.0
SC_default = 1367.0          # Solar constant in W/m^2 is 1367.0. Note that this value could vary by +/-4 W/m^2
TY_default = 365             # Total year number from 1 to 365 days
elevation_default = 0.0      # Default elevation is 0.0

# Useful equations for analysis

def get_sunrise_sunset_transit(latitude_deg, longitude_deg, when):

    utc_offset = when.utcoffset()
    if utc_offset != None :
        utc_offset = utc_offset.total_seconds()
    else :
        utc_offset = 0
    #end if

    # hours (ignore DST) time diff between UTC and the standard meridian for the input longitude 
    time_diff = int(round(longitude_deg / 15., 0) - utc_offset / 3600)
    # the day, and therefore sunrise and sunset, may be different at the input longitude than at the input "when" 
    local_time = when - timedelta(seconds = utc_offset) + timedelta(hours = time_diff)

    day = local_time.timetuple().tm_yday # Day of the year

    SHA = utc_offset / 3600 * 15.0 - longitude_deg # Solar hour angle
    TT = 2 * math.pi * day / 366
    decl = \
        (
            0.322003
        -
            22.971 * math.cos(TT)
        -
            0.357898 * math.cos(2 * TT)
        -
            0.14398 * math.cos(3 * TT)
        +
            3.94638 * math.sin(TT)
        +
            0.019334 * math.sin(2 * TT)
        +
            0.05928 * math.sin(3 * TT)
        ) # solar declination in degrees
    TT = math.radians(279.134 + 0.985647 * day) # Time adjustment angle
    time_adst = \
        (
                (
                    5.0323
                -
                    100.976 * math.sin(TT)
                +
                    595.275 * math.sin(2 * TT)
                +
                    3.6858 * math.sin(3 * TT)
                -
                    12.47 * math.sin(4 * TT)
                -
                    430.847 * math.cos(TT)
                +
                    12.5024 * math.cos(2 * TT)
                +
                    18.25 * math.cos(3 * TT)
                )
            /
                3600
        ) # Time adjustment in hours
    TON = 12 + SHA / 15.0 - time_adst # Time of noon
    ha = \
        (
            math.acos(
                math.cos(math.radians(90.833))
            /
                (
                    math.cos(math.radians(latitude_deg))
                *
                    math.cos(math.radians(decl))
                )
            -
                math.tan(math.radians(latitude_deg))
            *
                math.tan(math.radians(decl))
            )
        *
            (12 / math.pi)
        )

    # tzinfo doesn't matter
    local_day = datetime(year = local_time.year, month = local_time.month, day = local_time.day, tzinfo = local_time.tzinfo)

    transit_time = local_day + timedelta(hours = time_diff + TON)
    transit_time = (transit_time + timedelta(seconds = utc_offset) - timedelta(hours = time_diff)).replace(tzinfo=when.tzinfo)
    sunrise_time = transit_time - timedelta(hours = ha)
    sunset_time = transit_time + timedelta(hours = ha)

    return sunrise_time, sunset_time, transit_time

def get_sunrise_sunset(latitude_deg, longitude_deg, when):
    "Wrapper for get_sunrise_sunset_transit that returns just the sunrise and the sunset time."
    return \
        get_sunrise_sunset_transit(latitude_deg, longitude_deg, when)[0:2]

def get_sunrise_time(latitude_deg, longitude_deg, when):
    "Wrapper for get_sunrise_sunset_transit that returns just the sunrise time."
    return \
        get_sunrise_sunset_transit(latitude_deg, longitude_deg, when)[0]

def get_sunset_time(latitude_deg, longitude_deg, when):
    "Wrapper for get_sunrise_sunset_transit that returns just the sunset time."
    return \
        get_sunrise_sunset_transit(latitude_deg, longitude_deg, when)[1]

def get_transit_time(latitude_deg, longitude_deg, when):
    "Wrapper for get_sunrise_sunset_transit that returns just the transit time."
    return \
        get_sunrise_sunset_transit(latitude_deg, longitude_deg, when)[2]

def mean_earth_sun_distance(when):
    return 1 - 0.0335 * math.sin(2 * math.pi * (when.utctimetuple().tm_yday - 94)) / 365

def extraterrestrial_irrad(latitude_deg, longitude_deg, when, SC=SC_default):
    day = when.utctimetuple().tm_yday
    ab = math.cos(2 * math.pi * (day - 1.0)/(365.0))
    bc = math.sin(2 * math.pi * (day - 1.0)/(365.0))
    cd = math.cos(2 * (2 * math.pi * (day - 1.0)/(365.0)))
    df = math.sin(2 * (2 * math.pi * (day - 1.0)/(365.0)))
    decl = math.radians(solar.get_declination(day))
    ha = math.radians(solar.get_hour_angle(when, longitude_deg))
    ZA = math.sin(math.radians(latitude_deg)) * math.sin(decl) + math.cos(math.radians(latitude_deg)) * math.cos(decl) * math.cos(ha)

    return SC * ZA * (1.00010 + 0.034221 * ab + 0.001280 * bc + 0.000719 * cd + 0.000077 * df) if ZA > 0 else 0.0


def declination_degree(when, TY = TY_default):
    return constants.earth_axis_inclination * math.sin((2 * math.pi / (TY)) * ((when.utctimetuple().tm_yday) - 81))


def solarelevation_function_clear(latitude_deg, longitude_deg, when, temperature = constants.standard_temperature,
                                  pressure = constants.standard_pressure,  elevation = elevation_default):
    altitude = solar.get_altitude(latitude_deg, longitude_deg,when, elevation, temperature,pressure)
    return (0.038175 + (1.5458 * (math.sin(altitude))) + ((-0.59980) * (0.5 * (1 - math.cos(2 * (altitude))))))

def solarelevation_function_overcast(latitude_deg, longitude_deg, when,
                                     elevation = elevation_default, temperature = constants.standard_temperature,
                                     pressure = constants.standard_pressure):
    altitude = solar.get_altitude(latitude_deg, longitude_deg,when, elevation, temperature,pressure)
    return ((-0.0067133) + (0.78600 * (math.sin(altitude)))) + (0.22401 * (0.5 * (1 - math.cos(2 * altitude))))


def diffuse_transmittance(TL = TL_default):
    return ((-21.657) + (41.752 * (TL)) + (0.51905 * (TL) * (TL)))


def diffuse_underclear(latitude_deg, longitude_deg, when, elevation = elevation_default,
                       temperature = constants.standard_temperature, pressure = constants.standard_pressure, TL=TL_default):
    altitude = solar.get_altitude(latitude_deg, longitude_deg,when, elevation, temperature,pressure)
    return diffuse_underclear_from_altitude(altitude, when, TL)

def diffuse_underclear_from_altitude(altitude, when=datetime.now(), TL=TL_default):
    DT = ((-21.657) + (41.752 * (TL)) + (0.51905 * (TL) * (TL)))
    return mean_earth_sun_distance(when) * DT * altitude

def diffuse_underovercast(latitude_deg, longitude_deg, when, elevation = elevation_default,
                          temperature = constants.standard_temperature, pressure = constants.standard_pressure,TL=TL_default):
    DT = ((-21.657) + (41.752 * (TL)) + (0.51905 * (TL) * (TL)))

    DIFOC = ((mean_earth_sun_distance(when)
              )*(DT)*(solar.get_altitude(latitude_deg,longitude_deg, when, elevation,
                                        temperature, pressure)))
    return DIFOC

def direct_underclear(latitude_deg, longitude_deg, when,
                      TY = TY_default, AM = AM_default, TL = TL_default, elevation = elevation_default, 
                      temperature = constants.standard_temperature, pressure = constants.standard_pressure):
    KD = mean_earth_sun_distance(when)

    DEC = declination_degree(when,TY)

    DIRC = (1367 * KD * math.exp(-0.8662 * (AM) * (TL) * (DEC)
                             ) * math.sin(solar.get_altitude(latitude_deg,longitude_deg,
                                                          when,elevation ,
                                                          temperature , pressure )))

    return DIRC

def global_irradiance_clear(latitude_deg, longitude_deg, when,
                            TY = TY_default, AM = AM_default, TL = TL_default, elevation = elevation_default, 
                            temperature = constants.standard_temperature, pressure = constants.standard_pressure):
    DIRC =  direct_underclear(latitude_deg, longitude_deg, when,
                              TY, AM, TL, elevation, temperature = constants.standard_temperature,
                              pressure = constants.standard_pressure)

    DIFFC = diffuse_underclear(latitude_deg, longitude_deg, when,
                               elevation, temperature = constants.standard_temperature, 
                               pressure= constants.standard_pressure)

    ghic = (DIRC + DIFFC)

    return ghic


def global_irradiance_overcast(latitude_deg, longitude_deg, when,
                               elevation = elevation_default, temperature = constants.standard_temperature,
                               pressure = constants.standard_pressure):
    ghioc = (572 * (solar.get_altitude(latitude_deg, longitude_deg, when,
                                    elevation , temperature , pressure )))

    return ghioc


def diffuse_ratio(DIFF_data, ghi_data):
    K = DIFF_data/ghi_data

    return K


def clear_index(ghi_data, latitude_deg, longitude_deg, when):
    EXTR1 = extraterrestrial_irrad(latitude_deg, longitude_deg, when)

    KT = (ghi_data / EXTR1)

    return KT
