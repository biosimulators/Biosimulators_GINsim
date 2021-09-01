""" BioSimulators-compliant command-line interface to the `GINsim <http://ginsim.org/>`_ simulation program.

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-07-07
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from .utils import (validate_simulation, get_variable_target_xpath_ids,
                    read_model, set_up_simulation, exec_simulation, get_variable_results)
from biosimulators_utils.combine.exec import exec_sedml_docs_in_archive
from biosimulators_utils.config import get_config, Config  # noqa: F401
from biosimulators_utils.log.data_model import CombineArchiveLog, TaskLog  # noqa: F401
from biosimulators_utils.viz.data_model import VizFormat  # noqa: F401
from biosimulators_utils.report.data_model import ReportFormat, VariableResults, SedDocumentResults  # noqa: F401
from biosimulators_utils.sedml import validation
from biosimulators_utils.sedml.data_model import (Task, ModelLanguage, ModelAttributeChange,  # noqa: F401
                                                  SteadyStateSimulation, UniformTimeCourseSimulation,
                                                  Variable, Symbol)
from biosimulators_utils.sedml.exec import exec_sed_doc
from biosimulators_utils.utils.core import raise_errors_warnings
import functools

__all__ = ['exec_sedml_docs_in_combine_archive', 'exec_sed_task']


def exec_sedml_docs_in_combine_archive(archive_filename, out_dir, config=None):
    """ Execute the SED tasks defined in a COMBINE/OMEX archive and save the outputs

    Args:
        archive_filename (:obj:`str`): path to COMBINE/OMEX archive
        out_dir (:obj:`str`): path to store the outputs of the archive

            * CSV: directory in which to save outputs to files
              ``{ out_dir }/{ relative-path-to-SED-ML-file-within-archive }/{ report.id }.csv``
            * HDF5: directory in which to save a single HDF5 file (``{ out_dir }/reports.h5``),
              with reports at keys ``{ relative-path-to-SED-ML-file-within-archive }/{ report.id }`` within the HDF5 file

        config (:obj:`Config`, optional): BioSimulators common configuration

    Returns:
        :obj:`tuple`:

            * :obj:`SedDocumentResults`: results
            * :obj:`CombineArchiveLog`: log
    """
    sed_doc_executer = functools.partial(exec_sed_doc, exec_sed_task)
    return exec_sedml_docs_in_archive(sed_doc_executer, archive_filename, out_dir,
                                      apply_xml_model_changes=True,
                                      config=config)


def exec_sed_task(task, variables, log=None, config=None):
    """ Execute a task and save its results

    Args:
       task (:obj:`Task`): task
       variables (:obj:`list` of :obj:`Variable`): variables that should be recorded
       log (:obj:`TaskLog`, optional): log for the task
       config (:obj:`Config`, optional): BioSimulators common configuration

    Returns:
        :obj:`tuple`:

            :obj:`VariableResults`: results of variables
            :obj:`TaskLog`: log

    Raises:
        :obj:`NotImplementedError`:

          * Task requires a time course that GINsim doesn't support
          * Task requires an algorithm that GINsim doesn't support
    """
    config = config or get_config()

    if config.LOG and not log:
        log = TaskLog()

    # validate task
    model = task.model
    sim = task.simulation

    if config.VALIDATE_SEDML:
        raise_errors_warnings(
            validation.validate_task(task),
            error_summary='Task `{}` is invalid.'.format(task.id))
        raise_errors_warnings(
            validation.validate_model_language(
                task.model.language,
                (ModelLanguage.SBML, ModelLanguage.ZGINML)),
            error_summary='Language for model `{}` is not supported.'.format(model.id))
        raise_errors_warnings(
            validation.validate_model_change_types(task.model.changes, ()),
            error_summary='Changes for model `{}` are not supported.'.format(model.id))
        raise_errors_warnings(
            *validation.validate_model_changes(task.model),
            error_summary='Changes for model `{}` are invalid.'.format(model.id))
        raise_errors_warnings(
            validation.validate_simulation_type(task.simulation,
                                                (UniformTimeCourseSimulation, SteadyStateSimulation)),
            error_summary='{} `{}` is not supported.'.format(sim.__class__.__name__, sim.id))
        raise_errors_warnings(
            *validation.validate_simulation(task.simulation),
            error_summary='Simulation `{}` is invalid.'.format(sim.id))
        raise_errors_warnings(
            *validate_simulation(task.simulation),
            error_summary='Simulation `{}` is invalid.'.format(sim.id))

    if model.language == ModelLanguage.SBML.value:
        target_xpath_ids = get_variable_target_xpath_ids(variables, task.model.source)
    else:
        target_xpath_ids = None

    # validate model
    if config.VALIDATE_SEDML_MODELS:
        raise_errors_warnings(*validation.validate_model(task.model, [], working_dir='.'),
                              error_summary='Model `{}` is invalid.'.format(model.id),
                              warning_summary='Model `{}` may be invalid.'.format(model.id))

    # read model
    biolqm_model = read_model(model.source)

    # setup simulation
    alg_kisao_id, method_name, method_args = set_up_simulation(sim, config=config)

    # run simulation
    raw_results = exec_simulation(method_name, biolqm_model, method_args)

    # transform results
    variable_results = get_variable_results(variables, model.language, target_xpath_ids, sim, raw_results)

    # log action
    if config.LOG:
        log.algorithm = alg_kisao_id
        log.simulator_details = {
            'method': method_name,
            'arguments': method_args,
        }

    ############################
    # return the result of each variable and log
    return variable_results, log
