""" Utility methods

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-07-07
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from .data_model import KISAO_ALGORITHM_MAP, UpdatePolicy  # noqa: F401
from biosimulators_utils.report.data_model import VariableResults
from biosimulators_utils.sedml.data_model import ModelLanguage, UniformTimeCourseSimulation, Symbol  # noqa: F401
from biosimulators_utils.simulator.utils import get_algorithm_substitution_policy
from biosimulators_utils.warnings import warn, BioSimulatorsWarning
from kisao.data_model import AlgorithmSubstitutionPolicy, ALGORITHM_SUBSTITUTION_POLICY_LEVELS
from kisao.utils import get_preferred_substitute_algorithm_by_ids
from ginsim.gateway import japi as ginsim_japi
import biolqm  # noqa: F401
import biosimulators_utils.sedml.validation
import biosimulators_utils.xml.utils
import collections
import lxml.etree
import numpy
import os
import py4j.java_gateway  # noqa: F401

__all__ = [
    'validate_time_course',
    'get_variable_target_xpath_ids',
    'read_model',
    'set_up_simulation',
    'get_trace_arg',
    'exec_simulation',
    'get_variable_results',
]


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


def get_variable_target_xpath_ids(variables, model_source):
    """ Get the SBML-qual id for each XML XPath target of a SED-ML variable

    Args:
        variables (:obj:`list` of :obj:`Variable`): variables of data generators
        model_source (:obj:`str`): path to model

    Returns:
        :obj:`dict`: dictionary that maps each variable target to the id of the
            corresponding qualitative species
    """
    namespaces = biosimulators_utils.xml.utils.get_namespaces_for_xml_doc(lxml.etree.parse(model_source))

    return biosimulators_utils.sedml.validation.validate_variable_xpaths(
        variables,
        model_source,
        attr={
            'namespace': {
                'prefix': 'qual',
                'uri': namespaces['qual'],
            },
            'name': 'id',
        }
    )


def read_model(filename):
    """ Read a model

    Args:
        filename (:obj:`str`): path to model

    Returns:
        :obj:`py4j.java_gateway.JavaObject`: model
    """
    if not os.path.isfile(filename):
        raise FileNotFoundError('`{}` is not a file.'.format(filename))

    format = None
    try:
        root = lxml.etree.parse(filename).getroot()
        if root.tag.startswith('{http://www.sbml.org/sbml/'):
            format = 'sbml'
    except lxml.etree.XMLSyntaxError:
        pass  # pragma: no cover

    model = ginsim_japi.lqm.load(filename, format)

    if model is None:
        raise ValueError('Model `{}` could not be loaded.'.format(filename))

    return model


def set_up_simulation(simulation):
    """ Set up a simulation

    Args:
        simulation (:obj:`UniformTimeCourseSimulation`): simulation

    Returns:
        :obj:`tuple`:

            * :obj:`str`: KiSAO of algorithm to execute
            * :obj:`int`: maximum number of steps to simulate
            * :obj:`UpdatePolicy`: update policy
    """
    # time course
    max_steps = simulation.output_end_time

    # simulation algorithm
    alg_kisao_id = simulation.algorithm.kisao_id
    alg_substitution_policy = get_algorithm_substitution_policy()
    exec_kisao_id = get_preferred_substitute_algorithm_by_ids(
        alg_kisao_id, KISAO_ALGORITHM_MAP.keys(),
        substitution_policy=alg_substitution_policy)
    update_policy = KISAO_ALGORITHM_MAP[exec_kisao_id]['update_policy']

    # Apply the algorithm parameter changes specified by `simulation.algorithm.parameter_changes`
    if exec_kisao_id == alg_kisao_id:
        for change in simulation.algorithm.changes:
            if (
                ALGORITHM_SUBSTITUTION_POLICY_LEVELS[alg_substitution_policy]
                > ALGORITHM_SUBSTITUTION_POLICY_LEVELS[AlgorithmSubstitutionPolicy.NONE]
            ):
                warn('Unsuported algorithm parameter `{}` was ignored.'.format(change.kisao_id), BioSimulatorsWarning)
            else:
                raise NotImplementedError('Algorithm parameter `{}` is not supported.'.format(change.kisao_id))
    else:
        for change in simulation.algorithm.changes:
            warn('Unsuported algorithm parameter `{}` was ignored.'.format(change.kisao_id), BioSimulatorsWarning)

    # return
    return (exec_kisao_id, max_steps, update_policy)


def get_trace_arg(max_steps, update_policy):
    """ Set up the argument to :obj:`biolqm.trace`

    Args:
        max_steps (:obj:`int`): maximum number of steps to simulation
        update_policy (:obj:`UpdatePolicy`): update policy

    Returns:
        :obj:`str`: argument to :obj:`biolqm.trace`
    """
    args = collections.OrderedDict([
        ('m', int(max_steps)),
        ('u', update_policy.value),
    ])
    args_str = ' '.join('-{} {}'.format(arg, val) for arg, val in args.items())
    return args_str


def exec_simulation(model, max_steps, update_policy):
    """ Execute a simulation

    Args:
        model (:obj:`py4j.java_gateway.JavaObject`): model
        max_steps (:obj:`int`): maximum number of steps to simulation
        update_policy (:obj:`UpdatePolicy`): update policy

    Returns:
        :obj:`list` of :obj:`dict`: predicted states
    """
    return list(biolqm.trace(model, get_trace_arg(max_steps, update_policy)))


def get_variable_results(variables, model_language, target_xpath_ids, simulation, raw_results):
    """ Get the result of each SED-ML variable

    Args:
        variables (:obj:`list` of :obj:`Variable`): variables
        model_language (:obj:`str`): model language
        target_xpath_ids (:obj:`dict`): dictionary that maps XPaths to the SBML qualitative ids
            of the corresponding objects
        simulation (:obj:`UniformTimeCourseSimulation`): simulation
        raw_results (:obj:`list` of :obj:`dict`): predicted simulatioin states

    Returns:
        :obj:`VariableResults`: result of each SED-ML variable
    """
    n_sim_steps = len(raw_results)
    variable_results = VariableResults()
    for variable in variables:
        variable_results[variable.id] = numpy.full((n_sim_steps,), numpy.nan)

    invalid_variables = []
    for i_state, state in enumerate(raw_results):
        for variable in variables:
            if variable.symbol:
                variable_results[variable.id][i_state] = i_state
                if variable.symbol != Symbol.time.value:
                    invalid_variables.append('{}: symbol: {}'.format(variable.id, variable.symbol))

            else:
                if model_language == ModelLanguage.SBML.value:
                    id = target_xpath_ids[variable.target]
                else:
                    id = variable.target

                variable_results[variable.id][i_state] = state.get(id, numpy.nan)
                if i_state == 0 and numpy.isnan(variable_results[variable.id][i_state]):
                    invalid_variables.append('{}: target: {}'.format(variable.id, variable.target))

    if invalid_variables:
        raise ValueError('The following variables could not recorded:\n  {}'.format(
            '\n  '.join(sorted(invalid_variables))))

    for key in variable_results.keys():
        variable_results[key] = numpy.concatenate((
            variable_results[key],
            numpy.full((int(simulation.output_end_time) + 1 - n_sim_steps,), variable_results[key][-1]),
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
