#!/usr/bin/env python3
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.init_system import init_vector_store
asyncio.run(init_vector_store())
