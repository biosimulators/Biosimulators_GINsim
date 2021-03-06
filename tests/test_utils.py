from biosimulators_ginsim.data_model import UpdatePolicy
from biosimulators_ginsim.utils import (validate_time_course, validate_simulation, get_variable_target_xpath_ids,
                                        validate_variables, read_model, set_up_simulation,
                                        exec_simulation, get_variable_results)
from biosimulators_utils.sedml.data_model import (ModelLanguage, SteadyStateSimulation,
                                                  UniformTimeCourseSimulation,
                                                  Algorithm, AlgorithmParameterChange,
                                                  Variable, Symbol)
from biosimulators_utils.warnings import BioSimulatorsWarning
from kisao.exceptions import AlgorithmCannotBeSubstitutedException
from kisao.warnings import AlgorithmSubstitutedWarning
from unittest import mock
import collections
import lxml.etree
import numpy.testing
import os
import unittest


class UtilsTestCase(unittest.TestCase):
    def test_validate_time_course(self):
        sim = UniformTimeCourseSimulation(initial_time=0, output_start_time=0, output_end_time=100, number_of_points=100)
        self.assertEqual(validate_time_course(sim), ([], []))

        sim = UniformTimeCourseSimulation(initial_time=0, output_start_time=0, output_end_time=100, number_of_points=50)
        self.assertEqual(validate_time_course(sim), ([], []))

        sim = UniformTimeCourseSimulation(initial_time=1, output_start_time=1, output_end_time=100, number_of_points=99)
        self.assertNotEqual(validate_time_course(sim), ([], []))

        sim = UniformTimeCourseSimulation(initial_time=0, output_start_time=0.1, output_end_time=100, number_of_points=100)
        self.assertNotEqual(validate_time_course(sim), ([], []))

        sim = UniformTimeCourseSimulation(initial_time=0, output_start_time=0, output_end_time=100.1, number_of_points=100)
        self.assertNotEqual(validate_time_course(sim), ([], []))

        sim = UniformTimeCourseSimulation(initial_time=0, output_start_time=0, output_end_time=100, number_of_points=101)
        self.assertNotEqual(validate_time_course(sim), ([], []))

    def test_validate_simulation(self):
        sim = UniformTimeCourseSimulation(initial_time=0, output_start_time=0, output_end_time=100, number_of_points=100)
        self.assertEqual(validate_simulation(sim), ([], []))

        sim = UniformTimeCourseSimulation(initial_time=0, output_start_time=0, output_end_time=100, number_of_points=101)
        self.assertNotEqual(validate_simulation(sim), ([], []))

    def test_get_variable_target_xpath_ids(self):
        with mock.patch('lxml.etree.parse', return_value=None):
            with mock.patch('biosimulators_utils.xml.utils.get_namespaces_for_xml_doc', return_value={'qual': None}):
                with mock.patch('biosimulators_utils.model_lang.sbml.utils.get_package_namespace', return_value=('qual', None)):
                    with mock.patch('biosimulators_utils.sedml.validation.validate_target_xpaths', return_value={'x': 'X'}):
                        self.assertEqual(get_variable_target_xpath_ids([Variable(target='x')], None), {'x': 'X'})

    def test_read_model(self):
        filename = os.path.join(os.path.dirname(__file__), 'fixtures', 'SuppMat_Model_Master_Model.zginml')
        read_model(filename, ModelLanguage.ZGINML)

        filename = os.path.join(os.path.dirname(__file__), 'fixtures', 'example-model.sbml')
        read_model(filename, ModelLanguage.SBML)

        filename = os.path.join(os.path.dirname(__file__), 'fixtures', 'example-model.xml')
        read_model(filename, ModelLanguage.SBML)

        with self.assertRaises(FileNotFoundError):
            read_model('not a file', ModelLanguage.SBML)

        filename = os.path.join(os.path.dirname(__file__), 'fixtures', 'invalid.zginml')
        with self.assertRaises(ValueError):
            read_model(filename, ModelLanguage.ZGINML)

        filename = os.path.join(os.path.dirname(__file__), 'fixtures', 'regulatoryGraph.ginml')
        with self.assertRaises(ValueError):
            read_model(filename, ModelLanguage.GINML)

    def test_set_up_simulation(self):
        simulation = UniformTimeCourseSimulation(
            output_end_time=100,
            algorithm=Algorithm(kisao_id='KISAO_0000449'))
        kisao_id, method, method_args = set_up_simulation(simulation)
        self.assertEqual(kisao_id, 'KISAO_0000449')
        self.assertEqual(method, 'trace')
        self.assertEqual(method_args(simulation), ['-m 100', '-u {}'.format(UpdatePolicy.synchronous.value)])

        simulation.algorithm.kisao_id = 'KISAO_0000448'
        with mock.patch.dict('os.environ', {'ALGORITHM_SUBSTITUTION_POLICY': 'NONE'}):
            with self.assertRaises(AlgorithmCannotBeSubstitutedException):
                set_up_simulation(simulation)

        simulation.algorithm.kisao_id = 'KISAO_0000448'
        with mock.patch.dict('os.environ', {'ALGORITHM_SUBSTITUTION_POLICY': 'SIMILAR_VARIABLES'}):
            with self.assertWarns(AlgorithmSubstitutedWarning):
                kisao_id, method, method_args = set_up_simulation(simulation)
        self.assertEqual(kisao_id, 'KISAO_0000449')
        self.assertEqual(method, 'trace')
        self.assertEqual(method_args(simulation), ['-m 100', '-u {}'.format(UpdatePolicy.synchronous.value)])

        simulation.algorithm.kisao_id = 'KISAO_0000449'
        simulation.algorithm.changes = [AlgorithmParameterChange()]
        with mock.patch.dict('os.environ', {'ALGORITHM_SUBSTITUTION_POLICY': 'NONE'}):
            with self.assertRaises(NotImplementedError):
                set_up_simulation(simulation)

        with mock.patch.dict('os.environ', {'ALGORITHM_SUBSTITUTION_POLICY': 'SIMILAR_VARIABLES'}):
            with self.assertWarns(BioSimulatorsWarning):
                set_up_simulation(simulation)

        simulation.algorithm.kisao_id = 'KISAO_0000448'
        simulation.algorithm.changes = [AlgorithmParameterChange()]
        with mock.patch.dict('os.environ', {'ALGORITHM_SUBSTITUTION_POLICY': 'SIMILAR_VARIABLES'}):
            with self.assertWarns(BioSimulatorsWarning):
                set_up_simulation(simulation)

        simulation.algorithm.kisao_id = 'KISAO_0000663'
        simulation.algorithm.changes = []
        with mock.patch.dict('os.environ', {'ALGORITHM_SUBSTITUTION_POLICY': 'NONE'}):
            with self.assertRaises(NotImplementedError):
                set_up_simulation(simulation)

        simulation = SteadyStateSimulation(algorithm=Algorithm())
        simulation.algorithm.kisao_id = 'KISAO_0000662'
        with mock.patch.dict('os.environ', {'ALGORITHM_SUBSTITUTION_POLICY': 'NONE'}):
            kisao_id, method, method_args = set_up_simulation(simulation)
        self.assertEqual(kisao_id, 'KISAO_0000662')
        self.assertEqual(method, 'trapspaces')
        self.assertEqual(method_args(simulation), [])

        simulation.algorithm.kisao_id = 'KISAO_0000663'
        with mock.patch.dict('os.environ', {'ALGORITHM_SUBSTITUTION_POLICY': 'NONE'}):
            kisao_id, method, method_args = set_up_simulation(simulation)
        self.assertEqual(kisao_id, 'KISAO_0000663')
        self.assertEqual(method, 'trapspaces')
        self.assertEqual(method_args(simulation), ['BDD'])

        simulation.algorithm.changes.append(AlgorithmParameterChange(
            kisao_id='KISAO_0000216',
            new_value='false',
        ))
        with mock.patch.dict('os.environ', {'ALGORITHM_SUBSTITUTION_POLICY': 'NONE'}):
            kisao_id, method, method_args = set_up_simulation(simulation)
        self.assertEqual(kisao_id, 'KISAO_0000663')
        self.assertEqual(method, 'trapspaces')
        self.assertEqual(method_args(simulation), ['BDD'])

        simulation.algorithm.changes[0].new_value = 'true'
        with mock.patch.dict('os.environ', {'ALGORITHM_SUBSTITUTION_POLICY': 'NONE'}):
            kisao_id, method, method_args = set_up_simulation(simulation)
        self.assertEqual(kisao_id, 'KISAO_0000663')
        self.assertEqual(method, 'trapspaces')
        self.assertEqual(method_args(simulation), ['BDD', 'reduced'])

        simulation.algorithm.changes[0].new_value = 'unsupported'
        with mock.patch.dict('os.environ', {'ALGORITHM_SUBSTITUTION_POLICY': 'NONE'}):
            with self.assertRaises(ValueError):
                set_up_simulation(simulation)

        simulation.algorithm.changes[0].new_value = 'unsupported'
        with mock.patch.dict('os.environ', {'ALGORITHM_SUBSTITUTION_POLICY': 'SIMILAR_VARIABLES'}):
            with self.assertWarns(BioSimulatorsWarning):
                set_up_simulation(simulation)

    def test_exec_simulation(self):
        filename = os.path.join(os.path.dirname(__file__), 'fixtures', 'SuppMat_Model_Master_Model.zginml')
        model = read_model(filename, ModelLanguage.ZGINML)
        raw_results = exec_simulation('trace', model, ['-m 10', '-u {}'.format(UpdatePolicy.synchronous.value)])
        self.assertLessEqual(len(raw_results), 10 + 1)

        raw_results = exec_simulation('fixpoints', model)
        self.assertEqual(len(raw_results), 9)

    def test_get_variable_results_sbml(self):
        filename = os.path.join(os.path.dirname(__file__), 'fixtures', 'example-model.xml')
        model = read_model(filename, ModelLanguage.SBML)
        raw_results = exec_simulation('trace', model, ['-m 10', '-u {}'.format(UpdatePolicy.synchronous.value)])

        namespaces = {
            'sbml': 'http://www.sbml.org/sbml/level3/version1/core',
            'qual': 'http://www.sbml.org/sbml/level3/version1/qual/version1',
        }
        variables = [
            Variable(
                id='time',
                symbol=Symbol.time.value,
            ),
            Variable(
                id='G0',
                target="/sbml:sbml/sbml:model/qual:listOfQualitativeSpecies/qual:qualitativeSpecies[@qual:id='G0']",
                target_namespaces=namespaces,
            ),
            Variable(
                id='G1',
                target="/sbml:sbml/sbml:model/qual:listOfQualitativeSpecies/qual:qualitativeSpecies[@qual:id='G1']",
                target_namespaces=namespaces,
            ),
        ]
        model_language = ModelLanguage.SBML
        target_xpath_ids = get_variable_target_xpath_ids(variables, lxml.etree.parse(filename))
        simulation = UniformTimeCourseSimulation(
            initial_time=0,
            output_start_time=0,
            output_end_time=10,
            number_of_points=10,
        )
        results = get_variable_results(variables, model_language, target_xpath_ids, simulation, raw_results)
        self.assertEqual(set(results.keys()), set(['time', 'G0', 'G1']))
        numpy.testing.assert_allclose(results['time'], numpy.linspace(0, 10, 10 + 1))
        self.assertEqual(len(results['G0']), 10 + 1)

        simulation.output_start_time = 5
        simulation.number_of_points = 5
        results = get_variable_results(variables, model_language, target_xpath_ids, simulation, raw_results)
        self.assertEqual(set(results.keys()), set(['time', 'G0', 'G1']))
        numpy.testing.assert_allclose(results['time'], numpy.linspace(5, 10, 5 + 1))
        self.assertEqual(len(results['G0']), 5 + 1)

        simulation.output_start_time = 2
        simulation.number_of_points = 4
        results = get_variable_results(variables, model_language, target_xpath_ids, simulation, raw_results)
        self.assertEqual(set(results.keys()), set(['time', 'G0', 'G1']))
        numpy.testing.assert_allclose(results['time'], numpy.linspace(2, 10, 4 + 1))
        self.assertEqual(len(results['G0']), 4 + 1)

        variables[0].symbol = 'undefined'
        target_xpath_ids[variables[1].target] = 'undefined'
        with self.assertRaises(ValueError):
            validate_variables(variables, model, model_language, target_xpath_ids, simulation)

    def test_get_variable_results_zginml(self):
        filename = os.path.join(os.path.dirname(__file__), 'fixtures', 'SuppMat_Model_Master_Model.zginml')
        model = read_model(filename, ModelLanguage.ZGINML)
        raw_results = exec_simulation('trace', model, ['-m 10', '-u {}'.format(UpdatePolicy.synchronous.value)])

        variables = [
            Variable(
                id='time',
                symbol=Symbol.time.value,
            ),
            Variable(
                id='AKT1',
                target="AKT1",
            ),
            Variable(
                id='DKK1',
                target="DKK1",
            ),
        ]
        model_language = ModelLanguage.ZGINML
        target_xpath_ids = None
        simulation = UniformTimeCourseSimulation(
            initial_time=0,
            output_start_time=0,
            output_end_time=10,
            number_of_points=10,
        )
        results = get_variable_results(variables, model_language, target_xpath_ids, simulation, raw_results)
        self.assertEqual(set(results.keys()), set(['time', 'AKT1', 'DKK1']))
        numpy.testing.assert_allclose(results['time'], numpy.linspace(0, 10, 10 + 1))
        self.assertEqual(len(results['AKT1']), 10 + 1)

        variables[0].symbol = 'undefined'
        with self.assertRaises(ValueError):
            validate_variables(variables, model, model_language, target_xpath_ids, simulation)
