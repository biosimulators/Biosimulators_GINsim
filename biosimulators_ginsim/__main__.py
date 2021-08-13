""" BioSimulators-compliant command-line interface to the
`GINsim <http://ginsim.org>`_ simulation program.

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-07-07
:Copyright: 2021, BioSimulators Team
:License: MIT
"""

from . import get_simulator_version
from ._version import __version__
from .core import exec_sedml_docs_in_combine_archive
from biosimulators_utils.simulator.cli import build_cli

App = build_cli('biosimulators-ginsim', __version__,
                'GINsim', get_simulator_version(), 'http://ginsim.org',
                exec_sedml_docs_in_combine_archive)


def main():
    with App() as app:
        app.run()
