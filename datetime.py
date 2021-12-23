import time as _time
import math as _math


def _cmp(x, y):
    return 0 if x == y else 1 if x > y else -1
MINYEAR = 1
MAXYEAR = 9999

_MAXORDINAL = 3652059  # date.max.toordinal()
_DAYS_IN_MONTH = [None, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
_DAYS_BEFORE_MONTH = [None]
dbm = 0
for dim in _DAYS_IN_MONTH[1:]:
    _DAYS_BEFORE_MONTH.append(dbm)
    dbm += dim
del dbm, dim
def _is_leap(year):
    "year -> 1 if leap year, else 0."
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
def _days_before_year(year):
    "year -> number of days before January 1st of year."
    y = year - 1
    return y * 365 + y // 4 - y // 100 + y // 400
def _days_in_month(year, month):
    "year, month -> number of days in that month in that year."
    assert 1 <= month <= 12, month
    if month == 2 and _is_leap(year):
        return 29
    return _DAYS_IN_MONTH[month]
def _days_before_month(year, month):
    "year, month -> number of days in year preceding first day of month."
    assert 1 <= month <= 12, "month must be in 1..12"
    return _DAYS_BEFORE_MONTH[month] + (month > 2 and _is_leap(year))
def _ymd2ord(year, month, day):
    "year, month, day -> ordinal, considering 01-Jan-0001 as day 1."
    assert 1 <= month <= 12, "month must be in 1..12"
    dim = _days_in_month(year, month)
    assert 1 <= day <= dim, "day must be in 1..%d" % dim
    return _days_before_year(year) + _days_before_month(year, month) + day
_DI400Y = _days_before_year(401)  # number of days in 400 years
_DI100Y = _days_before_year(101)  #    "    "   "   " 100   "
_DI4Y = _days_before_year(5)  #    "    "   "   "   4   "
assert _DI4Y == 4 * 365 + 1
assert _DI400Y == 4 * _DI100Y + 1
assert _DI100Y == 25 * _DI4Y - 1
def _ord2ymd(n):
    "ordinal -> (year, month, day), considering 01-Jan-0001 as day 1."
    n -= 1
    n400, n = divmod(n, _DI400Y)
    year = n400 * 400 + 1  # ..., -399, 1, 401, ...
    n100, n = divmod(n, _DI100Y)
    n4, n = divmod(n, _DI4Y)
    n1, n = divmod(n, 365)
    year += n100 * 100 + n4 * 4 + n1
    if n1 == 4 or n100 == 4:
        assert n == 0
        return year - 1, 12, 31
    leapyear = n1 == 3 and (n4 != 24 or n100 == 3)
    assert leapyear == _is_leap(year)
    month = (n + 50) >> 5
    preceding = _DAYS_BEFORE_MONTH[month] + (month > 2 and leapyear)
    if preceding > n:  # estimate is too large
        month -= 1
        preceding -= _DAYS_IN_MONTH[month] + (month == 2 and leapyear)
    n -= preceding
    assert 0 <= n < _days_in_month(year, month)
    return year, month, n + 1
_MONTHNAMES = [
    None,
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]
_DAYNAMES = [None, "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


class timedelta:
    def __init__(
        self, hours=0, minutes=0
    ):
      self.seconds = 0
      self.seconds += hours * 60
      self.seconds += minutes * 60
  
class date:

    __slots__ = "_year", "_month", "_day"

    def __new__(cls, year, month=None, day=None):
        if (
            isinstance(year, bytes) and len(year) == 4 and 1 <= year[2] <= 12 and month is None
        ):  # Month is sane
            # Pickle support
            self = object.__new__(cls)
            self.__setstate(year)
            return self
        _check_date_fields(year, month, day)
        self = object.__new__(cls)
        self._year = year
        self._month = month
        self._day = day
        return self

    @property
    def year(self):
        return self._year
    @property
    def month(self):
        return self._month
    @property
    def day(self):
        return self._day

    def strftime(self, fmt):
        "Format using strftime()."
        return _wrap_strftime(self, fmt, self.timetuple())


class datetime(date):

    __slots__ = date.__slots__ + ("_hour", "_minute", "_second", "_microsecond", "_tzinfo")

    def __new__(
        cls, year, month=None, day=None, hour=0, minute=0, second=0, microsecond=0, tzinfo=None
    ):
        if isinstance(year, bytes) and len(year) == 10:
            # Pickle support
            self = date.__new__(cls, year[:4])
            self.__setstate(year, month)
            return self
        #_check_tzinfo_arg(tzinfo)
        _check_time_fields(hour, minute, second, microsecond)
        self = date.__new__(cls, year, month, day)
        self._hour = hour
        self._minute = minute
        self._second = second
        self._microsecond = microsecond
        self._tzinfo = tzinfo
        return self


    @classmethod
    def now(cls, tz=None):
        t = _time.time()
        return cls.fromtimestamp(t, tz)

    @classmethod
    def fromtimestamp(cls, t, tz=None):

        _check_tzinfo_arg(tz)

        converter = _time.localtime if tz is None else _time.gmtime

        t, frac = divmod(t, 1.0)
        us = int(frac * 1e6)

        if us == 1000000:
            t += 1
            us = 0
        dst = 0
        y, m, d, hh, mm, ss, weekday, jday = converter(int(t))[:8]
        ss = min(ss, 59)  # clamp out leap seconds if the platform has them
        result = cls(y, m, d, hh, mm, ss, us, tz)
        if tz is not None:
            result = tz.fromutc(result)
        return result

    def timetuple(self):
        "Return local time tuple compatible with time.localtime()."
        dst = self.dst()
        if dst is None:
            dst = -1
        elif dst:
            dst = 1
        else:
            dst = 0
        return _build_struct_time(
            self.year, self.month, self.day, self.hour, self.minute, self.second, dst
        )

    def timestamp(self):
        "Return POSIX timestamp as float"
        if True:# self._tzinfo is None:
            return (
                _time.mktime(
                    (
                        self.year,
                        self.month,
                        self.day,
                        self.hour,
                        self.minute,
                        self.second,
                        -1,
                        -1,
                        -1,
                    )
                )
            )
        else:
            return (self - _EPOCH).total_seconds()

    def dst(self):
        if self._tzinfo is None:
            return None
        return 0
        offset = self._tzinfo.dst(self)
        _check_utc_offset("dst", offset)
        return offset

    @property
    def hour(self):
        return self._hour
    @property
    def minute(self):
        return self._minute
    @property
    def second(self):
        return self._second

    def replace(
        self,
        year=None,
        month=None,
        day=None,
        hour=None,
        minute=None,
        second=None,
        microsecond=None,
        tzinfo=True,
    ):
        if year is None:
            year = self.year
        if month is None:
            month = self.month
        if day is None:
            day = self.day
        if hour is None:
            hour = self.hour
        if minute is None:
            minute = self.minute
        if second is None:
            second = self.second
        _check_date_fields(year, month, day)
        _check_time_fields(hour, minute, second, microsecond)
        return datetime(year, month, day, hour, minute, second, microsecond, tzinfo)

    def __add__(self, other):
        "Add a datetime and a timedelta."
        if not isinstance(other, timedelta):
            return NotImplemented
        ts = self.timestamp()
        ts += other.seconds
        return datetime.fromtimestamp(ts)
    __radd__ = __add__

    def strftime(self, fmt):
        timetuple = (1900, 1, 1, self._hour, self._minute, self._second, 0, 1, -1)
        return _wrap_strftime(self, fmt, timetuple)
    
    def __repr__(self):
      return '%s-%s-%s %s:%s:%s' % (self.year, self.month, self.day, self.hour, self.minute, self.second)


def _check_date_fields(year, month, day):
    if not isinstance(year, int):
        raise TypeError("int expected")
    if not MINYEAR <= year <= MAXYEAR:
        raise ValueError("year must be in %d..%d" % (MINYEAR, MAXYEAR), year)
    if not 1 <= month <= 12:
        raise ValueError("month must be in 1..12", month)
    dim = _days_in_month(year, month)
    if not 1 <= day <= dim:
        raise ValueError("day must be in 1..%d" % dim, day)

def _check_tzinfo_arg(tz):
    if tz is not None and not isinstance(tz, tzinfo):
        raise TypeError("tzinfo argument must be None or of a tzinfo subclass")

def _check_time_fields(hour, minute, second, microsecond):
    if not isinstance(hour, int):
        raise TypeError("int expected")
    if not 0 <= hour <= 23:
        raise ValueError("hour must be in 0..23", hour)
    if not 0 <= minute <= 59:
        raise ValueError("minute must be in 0..59", minute)
    if not 0 <= second <= 59:
        raise ValueError("second must be in 0..59", second)

def _build_struct_time(y, m, d, hh, mm, ss, dstflag):
    wday = (_ymd2ord(y, m, d) + 6) % 7
    dnum = _days_before_month(y, m) + d
    if hasattr(_time, 'struct_time'):
      return _time.struct_time((y, m, d, hh, mm, ss, wday, dnum, dstflag))
    else:
      return (y, m, d, hh, mm, ss, wday, dnum)

def _wrap_strftime(object, format, timetuple):
    freplace = None  # the string to use for %f
    zreplace = None  # the string to use for %z
    Zreplace = None  # the string to use for %Z
    newformat = []
    push = newformat.append
    i, n = 0, len(format)
    while i < n:
        ch = format[i]
        i += 1
        if ch == "%":
            if i < n:
                ch = format[i]
                i += 1
                if ch == "f":
                    if freplace is None:
                        freplace = "%06d" % getattr(object, "microsecond", 0)
                    newformat.append(freplace)
                elif ch == "z":
                    if zreplace is None:
                        zreplace = ""
                        if hasattr(object, "utcoffset"):
                            offset = object.utcoffset()
                            if offset is not None:
                                sign = "+"
                                if offset.days < 0:
                                    offset = -offset
                                    sign = "-"
                                h, m = divmod(offset, timedelta(hours=1))
                                assert not m % timedelta(minutes=1), "whole minute"
                                m //= timedelta(minutes=1)
                                zreplace = "%c%02d%02d" % (sign, h, m)
                    assert "%" not in zreplace
                    newformat.append(zreplace)
                elif ch == "Z":
                    if Zreplace is None:
                        Zreplace = ""
                        if hasattr(object, "tzname"):
                            s = object.tzname()
                            if s is not None:
                                Zreplace = s.replace("%", "%%")
                    newformat.append(Zreplace)
                else:
                    push("%")
                    push(ch)
            else:
                push("%")
        else:
            push(ch)
    newformat = "".join(newformat)
    return _time.strftime(newformat, timetuple)


