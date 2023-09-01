from __future__ import absolute_import, division, print_function
  
import sys

# helps with printing error messages to STDERR
def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)
