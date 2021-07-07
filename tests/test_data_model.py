from biosimulators_ginsim.data_model import KISAO_ALGORITHM_MAP
import json
import os
import unittest


class DataModelTestCase(unittest.TestCase):
    def test_data_model_matches_specs(self):
        specs_filename = os.path.join(os.path.dirname(__file__), '..', 'biosimulators.json')
        with open(specs_filename, 'r') as file:
            specs = json.load(file)

        self.assertEqual(set(KISAO_ALGORITHM_MAP.keys()),
                         set(alg_specs['kisaoId']['id'] for alg_specs in specs['algorithms']))

        for alg_specs in specs['algorithms']:
            alg_props = KISAO_ALGORITHM_MAP[alg_specs['kisaoId']['id']]
            self.assertEqual(set(alg_props['parameters'].keys()),
                             set(param_specs['kisaoId']['id'] for param_specs in alg_specs['parameters']))
