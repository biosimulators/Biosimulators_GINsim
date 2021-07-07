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


KISAO_ALGORITHM_MAP = collections.OrderedDict([
    ('KISAO_0000449', {
        'kisao_id': 'KISAO_0000449',
        'id': 'synchronous',
        'update_policy': UpdatePolicy.synchronous,
        'parameters': {},
    }),
    ('KISAO_0000450', {
        'kisao_id': 'KISAO_0000450',
        'id': 'sequential',
        'update_policy': UpdatePolicy.sequential,
        'parameters': {},
    }),
])
