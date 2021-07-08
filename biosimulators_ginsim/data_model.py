""" Data model

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-07-07
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

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
        'method': 'trace',
        'method_args': lambda simulation: collections.OrderedDict([
            ('m', int(simulation.output_end_time)),
            ('u', UpdatePolicy.synchronous.value),
        ]),
        'parameters': {},
    }),
    # ('KISAO_0000XXX', {
    #     'kisao_id': 'KISAO_0000XXX',
    #     'name': 'sequential logical simulation',
    #     'method': 'trace',
    #     'method_args': lambda simulation: collections.OrderedDict([
    #         ('m', int(simulation.output_end_time)),
    #         ('u', UpdatePolicy.sequential.value),
    #     ]),
    #     'parameters': {},
    # }),
    ('KISAO_0000450', {
        'kisao_id': 'KISAO_0000450',
        'name': 'asynchronous logical simulation',
        'method': 'random',
        'method_args': lambda simulation: collections.OrderedDict([
            ('m', int(simulation.output_end_time)),
            ('u', UpdatePolicy.asynchronous.value),
        ]),
        'parameters': {},
    }),
    ('KISAO_0000573', {
        'kisao_id': 'KISAO_0000573',
        'name': 'complete logical simulation',
        'method': 'random',
        'method_args': lambda simulation: collections.OrderedDict([
            ('m', int(simulation.output_end_time)),
            ('u', UpdatePolicy.complete.value),
        ]),
        'parameters': {},
    }),
])
