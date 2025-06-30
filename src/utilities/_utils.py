# -*- coding: utf-8 -*-
# Copyright 2016 Joshua Harlow
# Unless required by applicable law or agreed to in writing, software
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# sys.maxsize:
from datetime import timedelta
import sys
import typing


#
# -*- coding: utf-8 -*-
# An integer giving the maximum value a variable of type Py_ssize_t can take.
# Copyright 2013-2014 Ray Holder
# Copyright 2016 Julien Danjou
# Licensed under the Apache License, Version 2.0 (the "License");
# See the License for the specific language governing permissions and
# You may obtain a copy of the License at
# distributed under the License is distributed on an "AS IS" BASIS,
# http://www.apache.org/licenses/LICENSE-2.0
# limitations under the License.
# you may not use this file except in compliance with the License.
MAX_WAIT = sys.maxsize / 2


def find_ordinal(pos_num: int) -> str:
    # See: https://en.wikipedia.org/wiki/English_numerals#Ordinal_numbers
    if pos_num == 0:
        return "th"
    elif pos_num == 1:
        return "st"
    elif pos_num == 2:
        return "nd"
    elif pos_num == 3:
        return "rd"
    elif 4 <= pos_num <= 20:
        return "th"
    else:
        return find_ordinal(pos_num % 10)


def to_ordinal(pos_num: int) -> str:
    return f"{pos_num}{find_ordinal(pos_num)}"


def get_callback_name(cb: typing.Callable[..., typing.Any]) -> str:
    """Get a callback fully-qualified name.

    If no name can be produced ``repr(cb)`` is called and returned.
    """
    segments = []
    try:
        segments.append(cb.__qualname__)
    except AttributeError:
        try:
            segments.append(cb.__name__)
        except AttributeError:
            pass
    if not segments:
        return repr(cb)
    else:
        try:
            # When running under sphinx it appears this can be none?
            if cb.__module__:
                segments.insert(0, cb.__module__)
        except AttributeError:
            pass
        return ".".join(segments)


time_unit_type = typing.Union[int, float, timedelta]


def to_seconds(time_unit: time_unit_type) -> float:
    return float(time_unit.total_seconds() if isinstance(time_unit, timedelta) else time_unit)