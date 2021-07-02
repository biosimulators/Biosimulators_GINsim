from biosimulators_boolnet.utils import (install_boolnet, get_boolnet, get_boolnet_version,
                                         validate_time_course, validate_data_generator_variables,
                                         get_variable_target_x_path_keys,
                                         set_simulation_method_arg, get_variable_results)
from biosimulators_utils.sedml.data_model import (UniformTimeCourseSimulation, Variable,
                                                  Symbol, AlgorithmParameterChange)
from unittest import mock
import numpy
import numpy.testing
import os
import pandas
import unittest


class UtilsTestCase(unittest.TestCase):
    def test_install_boolnet(self):
        install_boolnet()

        with mock.patch.dict(os.environ, {'BOOLNET_VERSION': get_boolnet_version()}):
            install_boolnet()

    def test_get_boolnet(self):
        pkg = get_boolnet()
        self.assertRegex(pkg.__version__, r'^\d+\.\d+\.\d+$')

    def test_get_bionetgen_version(self):
        self.assertRegex(get_boolnet_version(), r'^\d+\.\d+\.\d+$')

    def test_validate_time_course(self):
        sim = UniformTimeCourseSimulation(initial_time=0, output_start_time=0, output_end_time=100, number_of_points=100)
        self.assertEqual(validate_time_course(sim), [])

        sim = UniformTimeCourseSimulation(initial_time=1, output_start_time=1, output_end_time=100, number_of_points=99)
        self.assertNotEqual(validate_time_course(sim), [])

        sim = UniformTimeCourseSimulation(initial_time=0, output_start_time=0.1, output_end_time=100, number_of_points=100)
        self.assertNotEqual(validate_time_course(sim), [])

        sim = UniformTimeCourseSimulation(initial_time=0, output_start_time=0, output_end_time=100.1, number_of_points=100)
        self.assertNotEqual(validate_time_course(sim), [])

        sim = UniformTimeCourseSimulation(initial_time=0, output_start_time=0, output_end_time=100, number_of_points=101)
        self.assertNotEqual(validate_time_course(sim), [])

    def test_validate_data_generator_variables(self):
        alg_kisao_id = 'KISAO_0000573'
        variables = [
            Variable(
                symbol=Symbol.time),
            Variable(
                target="/sbml:sbml/sbml:model/qual:listOfQualitativeSpecies/qual:qualitativeSpecies[@id='x']/@level"),
            Variable(
                target="/sbml:sbml/sbml:model/qual:listOfQualitativeSpecies/qual:qualitativeSpecies[@id='y']"),
            Variable(
                target="/sbml:sbml/sbml:model/qual:listOfQualitativeSpecies/qual:qualitativeSpecies[@name='Y']"),
            Variable(
                target="/sbml:sbml/sbml:model/qual:listOfQualitativeSpecies/qual:qualitativeSpecies/@level"),
            Variable(
                target="/sbml:sbml/sbml:model/qual:listOfQualitativeSpecies/qual:qualitativeSpecies")
        ]
        validate_data_generator_variables(variables, alg_kisao_id)

        variables = [Variable(symbol='x')]
        with self.assertRaises(NotImplementedError):
            validate_data_generator_variables(variables, alg_kisao_id)

        variables = [Variable(target='x')]
        with self.assertRaises(ValueError):
            validate_data_generator_variables(variables, alg_kisao_id)

    def test_get_variable_target_x_path_keys(self):
        with mock.patch('lxml.etree.parse', return_value=None):
            with mock.patch('biosimulators_utils.xml.utils.get_namespaces_for_xml_doc', return_value={'qual': None}):
                with mock.patch('biosimulators_utils.sedml.validation.validate_variable_xpaths', side_effect=[{'x': 'X'}, {'x': 'eX'}]):
                    self.assertEqual(get_variable_target_x_path_keys([Variable(target='x')], None), {'x': 'eX'})

                with mock.patch('biosimulators_utils.sedml.validation.validate_variable_xpaths', side_effect=[{'x': 'X'}, {'x': None}]):
                    self.assertEqual(get_variable_target_x_path_keys([Variable(target='x')], None), {'x': 'X'})

                with mock.patch('biosimulators_utils.sedml.validation.validate_variable_xpaths', side_effect=[{'x': 'X'}, {'x': 'e/X'}]):
                    self.assertEqual(get_variable_target_x_path_keys([Variable(target='x')], None), {'x': 'e_X'})

                with mock.patch('biosimulators_utils.sedml.validation.validate_variable_xpaths', side_effect=[
                    {'x': 'X', 'y': 'Y'},
                    {'x': 'name-X', 'y': 'name-Y'},
                ]):
                    get_variable_target_x_path_keys([Variable(target='x'), Variable(target='y')], None)

                with mock.patch('biosimulators_utils.sedml.validation.validate_variable_xpaths', side_effect=[
                    {'x': 'X', 'y': 'Y'},
                    {'x': 'name', 'y': 'name'},
                ]):
                    with self.assertRaisesRegex(ValueError, 'must generate a unique key'):
                        get_variable_target_x_path_keys([Variable(target='x'), Variable(target='y')], None)

    def test_set_simulation_method_arg(self):
        class Model(list):
            def __init__(self):
                super(Model, self).__init__()
                self.append(['A', 'B'])

            @property
            def names(self):
                return ['genes']

        model = Model()

        algorithm_kisao_id = 'KISAO_0000450'
        parameter_change = AlgorithmParameterChange(kisao_id='KISAO_0000572', new_value='0.9')
        simulation_method_args = {}
        set_simulation_method_arg(model, algorithm_kisao_id, parameter_change, simulation_method_args)
        self.assertEqual(simulation_method_args, {'noiseLevel': 0.9})

        parameter_change.kisao_id = 'KISAO_0000574'
        parameter_change.new_value = '{"A": 0.3, "B": 0.7}'
        set_simulation_method_arg(model, algorithm_kisao_id, parameter_change, simulation_method_args)
        self.assertEqual(list(simulation_method_args['geneProbabilities']), [0.3, 0.7])

        parameter_change.kisao_id = 'KISAO_0000574'
        parameter_change.new_value = '{"A": 0.3}'
        with self.assertRaises(ValueError):
            set_simulation_method_arg(model, algorithm_kisao_id, parameter_change, simulation_method_args)

        parameter_change.kisao_id = 'KISAO_0000574'
        parameter_change.new_value = '{"A": 0.3, "B": 0.6, "C": 0.1}'
        with self.assertRaises(ValueError):
            set_simulation_method_arg(model, algorithm_kisao_id, parameter_change, simulation_method_args)

        parameter_change.kisao_id = 'KISAO_0000574'
        parameter_change.new_value = '{"A": 0.3, "B": -0.6}'
        with self.assertRaises(ValueError):
            set_simulation_method_arg(model, algorithm_kisao_id, parameter_change, simulation_method_args)

        parameter_change.kisao_id = 'KISAO_0000574'
        parameter_change.new_value = '{"A": 0.3, "B": 0.8}'
        with self.assertRaises(ValueError):
            set_simulation_method_arg(model, algorithm_kisao_id, parameter_change, simulation_method_args)

        parameter_change.kisao_id = 'KISAO_0000001'
        parameter_change.new_value = '0.9'
        with self.assertRaises(NotImplementedError):
            set_simulation_method_arg(model, algorithm_kisao_id, parameter_change, simulation_method_args)

        parameter_change.kisao_id = 'KISAO_0000572'
        parameter_change.new_value = 'one point nine'
        with self.assertRaises(ValueError):
            set_simulation_method_arg(model, algorithm_kisao_id, parameter_change, simulation_method_args)

        parameter_change.kisao_id = 'KISAO_0000572'
        parameter_change.new_value = '-0.9'
        with self.assertRaises(ValueError):
            set_simulation_method_arg(model, algorithm_kisao_id, parameter_change, simulation_method_args)

    def test_get_variable_results(self):
        sim = UniformTimeCourseSimulation(initial_time=0, output_start_time=0, output_end_time=2, number_of_points=2)
        data = numpy.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        species_results = pandas.DataFrame(data, index=['A', 'B', 'C']).transpose()
        variables = [
            Variable(
                id='var_time',
                symbol=Symbol.time.value),
            Variable(
                id='var_A',
                target="/sbml:sbml/sbml:model/qual:listOfQualitativeSpecies/qual:qualitativeSpecies[@qual:id='A']"),
            Variable(
                id='var_B',
                target="/sbml:sbml/sbml:model/qual:listOfQualitativeSpecies/qual:qualitativeSpecies[@qual:id='B']"),
        ]

        target_x_paths_keys = {
            variables[1].target: 'A',
            variables[2].target: 'B',
        }

        variable_results = get_variable_results(sim, variables, target_x_paths_keys, species_results)
        numpy.testing.assert_allclose(variable_results['var_time'], numpy.array([0, 1, 2]))
        numpy.testing.assert_allclose(variable_results['var_A'], numpy.array([1, 2, 3]))
        numpy.testing.assert_allclose(variable_results['var_B'], numpy.array([4, 5, 6]))
