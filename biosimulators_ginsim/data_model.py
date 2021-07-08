""" Data model

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-07-07
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from biosimulators_utils.sedml.data_model import SteadyStateSimulation, UniformTimeCourseSimulation
import collections
import enum

__all__ = [
    'UpdatePolicy',
    'KISAO_ALGORITHM_MAP',
]


class UpdatePolicy(str, enum.Enum):
    """ Update policy """
    synchronous = 'synchronous'
    sequential = 'sequential'
    asynchronous = 'asynchronous'
    complete = 'complete'


KISAO_ALGORITHM_MAP = collections.OrderedDict([
    ('KISAO_0000449', {
        'kisao_id': 'KISAO_0000449',
        'name': 'synchronous logical simulation',
        'simulation_type': UniformTimeCourseSimulation,
        'method': 'trace',
        'method_args': lambda simulation:
            '-m {:d} -u {}'.format(int(simulation.output_end_time), UpdatePolicy.synchronous.value),
        'parameters': {},
    }),
    ('KISAO_0000657', {
        'kisao_id': 'KISAO_0000657',
        'name': 'sequential logical simulation',
        'simulation_type': UniformTimeCourseSimulation,
        'method': 'trace',
        'method_args': lambda simulation:
            '-m {:d} -u {}'.format(int(simulation.output_end_time), UpdatePolicy.sequential.value),
        'parameters': {},
    }),
    ('KISAO_0000450', {
        'kisao_id': 'KISAO_0000450',
        'name': 'asynchronous logical simulation',
        'simulation_type': UniformTimeCourseSimulation,
        'method': 'random',
        'method_args': lambda simulation:
            '-m {:d} -u {}'.format(int(simulation.output_end_time), UpdatePolicy.asynchronous.value),
        'parameters': {},
    }),
    ('KISAO_0000573', {
        'kisao_id': 'KISAO_0000573',
        'name': 'complete logical simulation',
        'simulation_type': UniformTimeCourseSimulation,
        'method': 'random',
        'method_args': lambda simulation:
            '-m {:d} -u {}'.format(int(simulation.output_end_time), UpdatePolicy.complete.value),
        'parameters': {},
    }),
    ('KISAO_0000659', {
        'kisao_id': 'KISAO_0000659',
        'name': 'Naldi MDD stable state search method',
        'simulation_type': SteadyStateSimulation,
        'method': 'fixpoints',
        'method_args': lambda simulation: collections.OrderedDict([]),
        'parameters': {},
    }),
    ('KISAO_0000662', {
        'kisao_id': 'KISAO_0000662',
        'name': 'Klarner ASP trap space identification method',
        'simulation_type': SteadyStateSimulation,
        'method': 'trapspaces',
        'method_args': lambda simulation: None,
        'parameters': {},  # TODO: options: all, reduce, terminal, tree
    }),
    ('KISAO_0000663', {
        'kisao_id': 'KISAO_0000663',
        'name': 'BDD trap space identification method',
        'simulation_type': SteadyStateSimulation,
        'method': 'trapspaces',
        'method_args': lambda simulation: 'BDD',
        'parameters': {},  # TODO: options: all, reduce, terminal, tree
    }),
])
