from __future__ import absolute_import, division, print_function

import subprocess
import os

def test_function():
    setup = """
    #!/bin/bash
    set -x

    gunicorn --workers=1 --threads=1 --chdir `hcli_core path` "hcli_core:connector(\\"`hcli_hc path`\\")" --daemon
    huckle cli install http://127.0.0.1:8000
    """

    p1 = subprocess.Popen(['bash', '-c', setup], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    out, err = p1.communicate()

    hello = """
    #!/bin/bash
    set -x

    export PATH=$PATH:~/.huckle/bin
    echo '$H' | hc -j '$H'
    hc jobs
    kill $(ps aux | grep '[g]unicorn' | awk '{print $2}')
    """

    p2 = subprocess.Popen(['bash', '-c', hello], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    out, err = p2.communicate()
    result = out.decode('utf-8')

    assert('1    $H' in result)
