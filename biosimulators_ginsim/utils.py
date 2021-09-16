""" Utility methods

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-07-07
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from .data_model import KISAO_ALGORITHM_MAP, UpdatePolicy  # noqa: F401
from biosimulators_utils.config import Config  # noqa: F401
from biosimulators_utils.report.data_model import VariableResults
from biosimulators_utils.sedml.data_model import (  # noqa: F401
    ModelLanguage, Simulation, UniformTimeCourseSimulation, Symbol)
from biosimulators_utils.simulator.utils import get_algorithm_substitution_policy
from biosimulators_utils.utils.core import validate_str_value, parse_value
from biosimulators_utils.warnings import warn, BioSimulatorsWarning
from kisao.data_model import AlgorithmSubstitutionPolicy, ALGORITHM_SUBSTITUTION_POLICY_LEVELS
from kisao.utils import get_preferred_substitute_algorithm_by_ids
from ginsim.gateway import japi as ginsim_japi
import biolqm  # noqa: F401
import biosimulators_utils.sedml.validation
import biosimulators_utils.xml.utils
import lxml.etree  # noqa: F401
import numpy
import os
import py4j.java_gateway  # noqa: F401
import types  # noqa: F401

__all__ = [
    'validate_simulation',
    'validate_time_course',
    'get_variable_target_xpath_ids',
    'validate_variables',
    'read_model',
    'set_up_simulation',
    'exec_simulation',
    'get_variable_results',
]


def validate_simulation(simulation):
    """ Validate a simulation

    Args:
        simulation (:obj:`Simulation`): simulation

    Returns:
        :obj:`tuple`:

            * nested :obj:`list` of :obj:`str`: nested list of errors (e.g., required ids missing or ids not unique)
            * nested :obj:`list` of :obj:`str`: nested list of errors (e.g., required ids missing or ids not unique)
    """
    errors = []
    warnings = []

    if isinstance(simulation, UniformTimeCourseSimulation):
        temp_errors, temp_warnings = validate_time_course(simulation)
        errors.extend(temp_errors)
        warnings.extend(temp_warnings)

    return (errors, warnings)


def validate_time_course(simulation):
    """ Validate a time course

    Args:
        simulation (:obj:`UniformTimeCourseSimulation`): simulation

    Returns:
        :obj:`tuple`:

            * nested :obj:`list` of :obj:`str`: nested list of errors (e.g., required ids missing or ids not unique)
            * nested :obj:`list` of :obj:`str`: nested list of errors (e.g., required ids missing or ids not unique)
    """
    errors = []
    warnings = []

    if simulation.initial_time != 0:
        errors.append(['Initial time must be 0, not `{}`.'.format(simulation.initial_time)])

    if simulation.output_start_time != int(simulation.output_start_time):
        errors.append(['Output start time must be an integer, not `{}`.'.format(simulation.output_start_time)])

    if simulation.output_end_time != int(simulation.output_end_time):
        errors.append(['Output end time must be an integer, not `{}`.'.format(simulation.output_end_time)])

    step_size = (simulation.output_end_time - simulation.output_start_time) / simulation.number_of_steps
    if abs(step_size - round(step_size)) > 1e-8:
        msg = (
            'The interval between the output start and time time '
            'must be an integer multiple of the number of steps, not `{}`:'
            '\n  Output start time: {}'
            '\n  Output end time: {}'
            '\n  Number of steps: {}'
        ).format(step_size, simulation.output_start_time, simulation.output_end_time, simulation.number_of_steps)
        errors.append([msg])

    return (errors, warnings)


def get_variable_target_xpath_ids(variables, model_etree):
    """ Get the SBML-qual id for each XML XPath target of a SED-ML variable

    Args:
        variables (:obj:`list` of :obj:`Variable`): variables of data generators
        model_etree (:obj:`lxml.etree._ElementTree`): element tree for model

    Returns:
        :obj:`dict`: dictionary that maps each variable target to the id of the
            corresponding qualitative species
    """
    namespaces = biosimulators_utils.xml.utils.get_namespaces_for_xml_doc(model_etree)

    return biosimulators_utils.sedml.validation.validate_target_xpaths(
        variables,
        model_etree,
        attr={
            'namespace': {
                'prefix': 'qual',
                'uri': namespaces['qual'],
            },
            'name': 'id',
        }
    )


def validate_variables(variables, model, model_language, target_xpath_ids, simulation):
    """ Get the result of each SED-ML variable

    Args:
        variables (:obj:`list` of :obj:`Variable`): variables
        model (:obj:`py4j.java_gateway.JavaObject`): bioLQM model
        model_language (:obj:`str`): model language
        target_xpath_ids (:obj:`dict`): dictionary that maps XPaths to the SBML qualitative ids
            of the corresponding objects
        simulation (:obj:`Simulation`): analysis
    """
    component_ids = set(component.getNodeID() for component in model.getComponents())
    invalid_variables = []

    for variable in variables:
        if variable.symbol:
            if not (isinstance(simulation, UniformTimeCourseSimulation) and variable.symbol == Symbol.time.value):
                invalid_variables.append('{}: symbol: {}'.format(variable.id, variable.symbol))
        else:
            if model_language == ModelLanguage.SBML.value:
                id = target_xpath_ids[variable.target]
            else:
                id = variable.target

            if id not in component_ids:
                invalid_variables.append('{}: target: {}'.format(variable.id, variable.target))

    if invalid_variables:
        valid_variables = []

        if isinstance(simulation, UniformTimeCourseSimulation):
            valid_variables.append('symbol: {}'.format(Symbol.time.value))

        for component_id in component_ids:
            if model_language == ModelLanguage.SBML.value:
                valid_variables.append(
                    "target: /sbml:sbml/sbml:model/qual:listOfQualitativeSpecies/qual:qualitativeSpecies[@id='{}']".format(component_id))
            else:
                valid_variables.append(
                    'target: {}'.format(component_id))

        raise ValueError((
            'The following variables cannot be recorded:\n'
            '  {}\n'
            '\n'
            'Variables with the following symbols and targets can be recorded:\n'
            '  {}'
        ).format(
            '\n  '.join(sorted(invalid_variables)),
            '\n  '.join(sorted(valid_variables)),
        ))


def read_model(filename, language):
    """ Read a model

    Args:
        language (:obj:`ModelLanguage`): language

    Returns:
        :obj:`py4j.java_gateway.JavaObject`: model
    """
    if language == ModelLanguage.SBML:
        format = 'sbml'
    else:
        format = None

    if not os.path.isfile(filename):
        raise FileNotFoundError('`{}` is not a file.'.format(filename))

    model = ginsim_japi.lqm.load(filename, format)

    if model is None:
        raise ValueError('Model `{}` could not be loaded.'.format(filename))

    return model


def set_up_simulation(simulation, config=None):
    """ Set up an analysis

    Args:
        simulation (:obj:`Simulation`): analysis
        config (:obj:`Config`, optional): configuration

    Returns:
        :obj:`tuple`:

            * :obj:`str`: KiSAO of algorithm to execute
            * :obj:`str`: name of the :obj:`biolqm` simulation/analysis method
            * :obj:`types.LambdaType` of :obj:`Simulation` -> :obj:`list` of :obj:`str`: arguments for simulation method
    """
    # simulation algorithm
    alg_kisao_id = simulation.algorithm.kisao_id
    alg_substitution_policy = get_algorithm_substitution_policy(config=config)
    exec_kisao_id = get_preferred_substitute_algorithm_by_ids(
        alg_kisao_id, KISAO_ALGORITHM_MAP.keys(),
        substitution_policy=alg_substitution_policy)
    alg_props = KISAO_ALGORITHM_MAP[exec_kisao_id]
    if simulation.__class__ != alg_props['simulation_type']:
        raise NotImplementedError('{} simulations cannot be executed with `{}` ({}).'.format(
            simulation.__class__.__name__, exec_kisao_id, alg_props['name']))

    method = alg_props['method']
    method_args = []

    # Apply the algorithm parameter changes specified by `simulation.algorithm.parameter_changes`
    if exec_kisao_id == alg_kisao_id:
        for change in simulation.algorithm.changes:
            param_props = alg_props['parameters'].get(change.kisao_id, None)

            if param_props is None:
                if (
                    ALGORITHM_SUBSTITUTION_POLICY_LEVELS[alg_substitution_policy]
                    > ALGORITHM_SUBSTITUTION_POLICY_LEVELS[AlgorithmSubstitutionPolicy.NONE]
                ):
                    warn('Unsuported algorithm parameter `{}` was ignored.'.format(change.kisao_id), BioSimulatorsWarning)
                else:
                    raise NotImplementedError('Algorithm parameter `{}` is not supported.'.format(change.kisao_id))
            else:
                if validate_str_value(change.new_value, param_props['type']):
                    parsed_value = parse_value(change.new_value, param_props['type'])
                    method_args.extend(param_props['method_args'](parsed_value))

                else:
                    if (
                        ALGORITHM_SUBSTITUTION_POLICY_LEVELS[alg_substitution_policy]
                        > ALGORITHM_SUBSTITUTION_POLICY_LEVELS[AlgorithmSubstitutionPolicy.NONE]
                    ):
                        msg = 'Unsuported algorithm parameter value `{}` of `{}` was ignored. The value must be a {}.'.format(
                            change.new_value, change.kisao_id, param_props['type'].value)
                        warn(msg, BioSimulatorsWarning)
                    else:
                        msg = '`{}` is not a valid value of algorithm parameter `{}`. The value must be a {}.'.format(
                            change.new_value, change.kisao_id, param_props['type'].value)
                        raise ValueError(msg)
    else:
        for change in simulation.algorithm.changes:
            warn('Unsuported algorithm parameter `{}` was ignored.'.format(change.kisao_id), BioSimulatorsWarning)

    # return
    return (
        exec_kisao_id,
        method,
        lambda simulation: alg_props['method_args'](simulation) + method_args,
    )


def exec_simulation(method_name, model, args=None):
    """ Execute a task

    Args:
        method_name (:obj:`str`): name of the :obj:`biolqm` simulation/analysis method
        model (:obj:`py4j.java_gateway.JavaObject`): model
        args (:obj:`list` of :obj:`str`, optional): argument to :obj:`method`

    Returns:
        :obj:`list` of :obj:`dict`: result of :obj:`method` for :obj:`model` and :obj:`args`
    """
    method = getattr(biolqm, method_name)
    if args:
        args_list = [' '.join(args)]
    else:
        args_list = []
    result = method(model, *args_list)
    return list(result)


def get_variable_results(variables, model_language, target_xpath_ids, simulation, raw_results):
    """ Get the result of each SED-ML variable

    Args:
        variables (:obj:`list` of :obj:`Variable`): variables
        model_language (:obj:`str`): model language
        target_xpath_ids (:obj:`dict`): dictionary that maps XPaths to the SBML qualitative ids
            of the corresponding objects
        simulation (:obj:`Simulation`): simulation
        raw_results (:obj:`list` of :obj:`dict`): predicted simulatioin states

    Returns:
        :obj:`VariableResults`: result of each SED-ML variable
    """
    n_states = len(raw_results)
    variable_results = VariableResults()
    for variable in variables:
        variable_results[variable.id] = numpy.full((n_states,), numpy.nan)

    for i_state, state in enumerate(raw_results):
        for variable in variables:
            if variable.symbol:
                variable_results[variable.id][i_state] = i_state

            else:
                if model_language == ModelLanguage.SBML.value:
                    id = target_xpath_ids[variable.target]
                else:
                    id = variable.target

                variable_results[variable.id][i_state] = state[id]

    if isinstance(simulation, UniformTimeCourseSimulation):
        for key in variable_results.keys():
            variable_results[key] = numpy.concatenate((
                variable_results[key],
                numpy.full((int(simulation.output_end_time) + 1 - n_states,), variable_results[key][-1]),
            ))
        for variable in variables:
            if variable.symbol and variable.symbol == Symbol.time.value:
                variable_results[variable.id] = numpy.linspace(
                    int(simulation.initial_time),
                    int(simulation.output_end_time),
                    int(simulation.output_end_time) + 1)

        step_size = round((simulation.output_end_time - simulation.output_start_time) / simulation.number_of_steps)
        for key in variable_results.keys():
            variable_results[key] = variable_results[key][int(simulation.output_start_time)::step_size]

    return variable_results
