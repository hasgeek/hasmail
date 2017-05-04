#!/usr/bin/env python
import sys
from hasmail import app

try:
    port = int(sys.argv[1])
except (IndexError, ValueError):
    port = 7890
app.run('0.0.0.0', port=port)
