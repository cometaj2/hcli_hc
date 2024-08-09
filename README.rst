|pypi| |build status| |pyver|

HCLI hc
=======

HCLI hc is a python package wrapper that contains an HCLI sample application (hc); hc can can act both as a gcode streamer (e.g. for OpenBuilds Blackbox controller v1.1g) and CNC interface. In other words, this HCLI acts in the same capacity as the OpenBuilds CONTROL software or OpenBuilds Interface CNC Touch hardware to help control a GRBL v1.1g controlled CNC.

----

HCLI hc wraps hc (an HCLI) and is intended to be used with an HCLI Client [1] as presented via an HCLI Connector [2].

You can find out more about HCLI on hcli.io [3]

[1] https://github.com/cometaj2/huckle

[2] https://github.com/cometaj2/hcli_core

[3] http://hcli.io

Installation
------------

HCLI hc requires a supported version of Python and pip.

You'll need an HCLI Connector to run hc. For example, you can use HCLI Core (https://github.com/cometaj2/hcli_core), a WSGI server such as Green Unicorn (https://gunicorn.org/), and an HCLI Client like Huckle (https://github.com/cometaj2/huckle).


.. code-block:: console

    pip install hcli-hc
    pip install hcli-core
    pip install huckle
    pip install gunicorn
    gunicorn --workers=1 --threads=1 -b 127.0.0.1:8000 "hcli_core:connector(\"`hcli_hc path`\")"

Usage
-----

Open a different shell window.

Setup the huckle env eval in your .bash_profile (or other bash configuration) to avoid having to execute eval everytime you want to invoke HCLIs by name (e.g. hc).

Note that no CLI is actually installed by Huckle. Huckle reads the HCLI semantics exposed by the API via HCLI Connector and ends up behaving *like* the CLI it targets.


.. code-block:: console

    huckle cli install http://127.0.0.1:8000
    eval $(huckle env)
    hc help

Versioning
----------
    
This project makes use of semantic versioning (http://semver.org) and may make use of the "devx",
"prealphax", "alphax" "betax", and "rcx" extensions where x is a number (e.g. 0.3.0-prealpha1)
on github.

Supports
--------

- Gcode streaming
- Immediate/realtime GRBL command execution (including during gcode streaming)
- Gcode job sequences
- CNC jogging (continuous, incremental, imperial, and metric)
- Automated serial port scanning and connectivity (hc connect)

To Do
-----

- Update GRBL controller to include support for additional commands and/or echo of hexadecimal values.
- Update hc to include job removal, insertion and resequencing.
- Update hc to function in a multi-process environment (e.g. multiple workers in gunicorn).
- Implement GRBL emulation tests for hc.

Bugs
----

.. |build status| image:: https://circleci.com/gh/cometaj2/hcli_hc.svg?style=shield
   :target: https://circleci.com/gh/cometaj2/hcli_hc
.. |pypi| image:: https://img.shields.io/pypi/v/hcli-hc?label=hcli-hc
   :target: https://pypi.org/project/hcli-hc
.. |pyver| image:: https://img.shields.io/pypi/pyversions/hcli-hc.svg
   :target: https://pypi.org/project/hcli-hc
