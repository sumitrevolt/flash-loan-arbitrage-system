# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
import asyncio
import os
import sys

from scripts.init_system import init_db
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
asyncio.run(init_db())