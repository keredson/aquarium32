
#    Copyright François Steinmetz
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



from math import degrees, cos, sin, radians, tan, pi
from math import acos, atan, asin, atan2, exp, e


def where_math(condition, x, y):
    """ scalar version of numpy.where """
    if condition:
        return x
    else:
        return y

where = where_math

