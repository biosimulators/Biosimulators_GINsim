from biosimulators_boolnet.data_model import KISAO_METHOD_ARGUMENTS_MAP
import json
import os
import re
import unittest


class DataModelTestCase(unittest.TestCase):
    def test_data_model_matches_specifications(self):
        with open(os.path.join(os.path.dirname(__file__), '..', 'biosimulators.json'), 'r') as file:
            specs = json.load(file)

        self.assertEqual(
            set(KISAO_METHOD_ARGUMENTS_MAP.keys()),
            set(alg_specs['kisaoId']['id'] for alg_specs in specs['algorithms']))

        for alg_specs in specs['algorithms']:
            alg_props = KISAO_METHOD_ARGUMENTS_MAP[alg_specs['kisaoId']['id']]

            self.assertEqual(set(alg_props['parameters'].keys()), set(param_specs['kisaoId']['id']
                                                                      for param_specs in alg_specs['parameters']))

            for param_specs in alg_specs['parameters']:
                param_props = alg_props['parameters'][param_specs['kisaoId']['id']]

                self.assertEqual(param_props['type'], param_specs['type'])

            for var_target_specs in alg_specs['dependentVariableTargetPatterns']:
                matches = False
                for var_target_props in alg_props['variable_targets']:
                    if re.match(var_target_props['targets'], var_target_specs['targetPattern']):
                        matches = True
                        break
                self.assertTrue(matches)
