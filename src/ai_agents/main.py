# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
from typing import List, Optional

    from pip._internal.utils.entrypoints import _wrapper
# -*- coding: utf-8 -*-
def main(args: Optional[List[str]] = None) -> int:
    """This is preserved for old console scripts that may still be referencing
    it.

    For additional details, see https://github.com/pypa/pip/issues/7498.
    """

    return _wrapper(args)