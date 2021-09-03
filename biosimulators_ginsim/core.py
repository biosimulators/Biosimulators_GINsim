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
from biosimulators_utils.log.data_model import CombineArchiveLog, TaskLog, StandardOutputErrorCapturerLevel  # noqa: F401
from biosimulators_utils.viz.data_model import VizFormat  # noqa: F401
from biosimulators_utils.report.data_model import ReportFormat, VariableResults, SedDocumentResults  # noqa: F401
from biosimulators_utils.sedml import validation
from biosimulators_utils.sedml.data_model import (Task, ModelLanguage, ModelAttributeChange,  # noqa: F401
                                                  SteadyStateSimulation, UniformTimeCourseSimulation,
                                                  Variable, Symbol)
from biosimulators_utils.sedml.exec import exec_sed_doc as base_exec_sed_doc
from biosimulators_utils.utils.core import raise_errors_warnings
import lxml.etree
import os

__all__ = ['exec_sedml_docs_in_combine_archive', 'exec_sed_doc', 'exec_sed_task', 'preprocess_sed_task']


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
    return exec_sedml_docs_in_archive(exec_sed_doc, archive_filename, out_dir,
                                      apply_xml_model_changes=True,
                                      config=config)


def exec_sed_doc(doc, working_dir, base_out_path, rel_out_path=None,
                 apply_xml_model_changes=True,
                 log=None, indent=0, pretty_print_modified_xml_models=False,
                 log_level=StandardOutputErrorCapturerLevel.c, config=None):
    """ Execute the tasks specified in a SED document and generate the specified outputs

    Args:
        doc (:obj:`SedDocument` or :obj:`str`): SED document or a path to SED-ML file which defines a SED document
        working_dir (:obj:`str`): working directory of the SED document (path relative to which models are located)

        base_out_path (:obj:`str`): path to store the outputs

            * CSV: directory in which to save outputs to files
              ``{base_out_path}/{rel_out_path}/{report.id}.csv``
            * HDF5: directory in which to save a single HDF5 file (``{base_out_path}/reports.h5``),
              with reports at keys ``{rel_out_path}/{report.id}`` within the HDF5 file

        rel_out_path (:obj:`str`, optional): path relative to :obj:`base_out_path` to store the outputs
        apply_xml_model_changes (:obj:`bool`, optional): if :obj:`True`, apply any model changes specified in the SED-ML file before
            calling :obj:`task_executer`.
        log (:obj:`SedDocumentLog`, optional): log of the document
        indent (:obj:`int`, optional): degree to indent status messages
        pretty_print_modified_xml_models (:obj:`bool`, optional): if :obj:`True`, pretty print modified XML models
        log_level (:obj:`StandardOutputErrorCapturerLevel`, optional): level at which to log output
        config (:obj:`Config`, optional): BioSimulators common configuration
        simulator_config (:obj:`SimulatorConfig`, optional): tellurium configuration

    Returns:
        :obj:`tuple`:

            * :obj:`ReportResults`: results of each report
            * :obj:`SedDocumentLog`: log of the document
    """
    return base_exec_sed_doc(exec_sed_task, doc, working_dir, base_out_path,
                             rel_out_path=rel_out_path,
                             apply_xml_model_changes=apply_xml_model_changes,
                             log=log,
                             indent=indent,
                             pretty_print_modified_xml_models=pretty_print_modified_xml_models,
                             log_level=log_level,
                             config=config)


def exec_sed_task(task, variables, preprocessed_task=None, log=None, config=None):
    """ Execute a task and save its results

    Args:
        task (:obj:`Task`): task
        variables (:obj:`list` of :obj:`Variable`): variables that should be recorded
        preprocessed_task (:obj:`object`, optional): preprocessed information about the task, including possible
            model changes and variables. This can be used to avoid repeatedly executing the same initialization
            for repeated calls to this method.
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

    if preprocessed_task is None:
        preprocessed_task = preprocess_sed_task(task, variables, config=config)

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

    if not os.path.isfile(task.model.source):
        raise FileNotFoundError('`{}` is not a file.'.format(task.model.source))

    if model.language == ModelLanguage.SBML.value:
        model_etree = lxml.etree.parse(task.model.source)
        target_xpath_ids = get_variable_target_xpath_ids(variables, model_etree)
    else:
        model_etree = None
        target_xpath_ids = None

    # validate model
    if config.VALIDATE_SEDML_MODELS:
        raise_errors_warnings(*validation.validate_model(task.model, [], working_dir='.'),
                              error_summary='Model `{}` is invalid.'.format(model.id),
                              warning_summary='Model `{}` may be invalid.'.format(model.id))

    # read model
    biolqm_model = read_model(model.source, model.language)

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


def preprocess_sed_task(task, variables, config=None):
    """ Preprocess a SED task, including its possible model changes and variables. This is useful for avoiding
    repeatedly initializing tasks on repeated calls of :obj:`exec_sed_task`.

    Args:
        task (:obj:`Task`): task
        variables (:obj:`list` of :obj:`Variable`): variables that should be recorded
        preprocessed_task (:obj:`PreprocessedTask`, optional): preprocessed information about the task, including possible
            model changes and variables. This can be used to avoid repeatedly executing the same initialization for repeated
            calls to this method.
        config (:obj:`Config`, optional): BioSimulators common configuration

    Returns:
        :obj:`object`: preprocessed information about the task
    """
    pass
