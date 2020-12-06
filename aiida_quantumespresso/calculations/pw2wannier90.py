# -*- coding: utf-8 -*-
"""`CalcJob` implementation for the pw2wannier.x code of Quantum ESPRESSO."""
from aiida.orm import RemoteData, FolderData, SinglefileData, Dict

from aiida_quantumespresso.calculations.namelists import NamelistsCalculation


class Pw2wannier90Calculation(NamelistsCalculation):
    """`CalcJob` implementation for the pw2wannier.x code of Quantum ESPRESSO.

    For more information, refer to http://www.quantum-espresso.org/ and http://www.wannier.org/
    """

    _default_namelists = ['INPUTPP']
    _SEEDNAME = 'aiida'
    _blocked_keywords = [('INPUTPP', 'outdir', NamelistsCalculation._OUTPUT_SUBFOLDER),
                         ('INPUTPP', 'prefix', NamelistsCalculation._PREFIX), ('INPUTPP', 'seedname', _SEEDNAME)]
    # By default we do not download anything else than aiida.out. One can add the files
    # _SEEDNAME.amn/.nnm/.eig to inputs.settings['ADDITIONAL_RETRIEVE_LIST'] to retrieve them.
    _internal_retrieve_list = []
    _default_parser = 'quantumespresso.pw2wannier90'

    @classmethod
    def define(cls, spec):
        """Define the process specification."""
        # yapf: disable
        super().define(spec)
        spec.input('nnkp_file', valid_type=SinglefileData,
                   help='A SinglefileData containing the .nnkp file generated by wannier90.x -pp')
        spec.input('parent_folder', valid_type=(RemoteData, FolderData),
                   help='The output folder of a pw.x calculation')
        spec.output('output_parameters', valid_type=Dict)
        spec.default_output_node = 'output_parameters'
        spec.exit_code(300, 'ERROR_NO_RETRIEVED_FOLDER',
            message='The retrieved folder data node could not be accessed.')
        spec.exit_code(310, 'ERROR_OUTPUT_STDOUT_READ',
            message='The stdout output file could not be read.')
        spec.exit_code(312, 'ERROR_OUTPUT_STDOUT_INCOMPLETE',
            message='The stdout output file was incomplete probably because the calculation got interrupted.')
        spec.exit_code(340, 'ERROR_GENERIC_QE_ERROR',
            message='Encountered a generic error message')
        spec.exit_code(350, 'ERROR_UNEXPECTED_PARSER_EXCEPTION',
            message='An error happened while parsing the output file')

    def prepare_for_submission(self, folder):
        """Prepare the calculation job for submission by transforming input nodes into input files.

        In addition to the input files being written to the sandbox folder, a `CalcInfo` instance will be returned that
        contains lists of files that need to be copied to the remote machine before job submission, as well as file
        lists that are to be retrieved after job completion.

        :param folder: a sandbox folder to temporarily write files on disk.
        :return: :py:`~aiida.common.datastructures.CalcInfo` instance.
        """
        if 'settings' in self.inputs:
            settings_dict = self.inputs.settings.get_dict()
            if "additional_remote_symlink_list" in settings_dict:
                additional_remote_symlink_list = settings_dict.pop("additional_remote_symlink_list")
                # remove additional_remote_symlink_list, otherwise error in super().prepare_for_submission()
                self.inputs.settings = Dict(dict=settings_dict)
            else:
                additional_remote_symlink_list = []
        else:
            additional_remote_symlink_list = []

        calcinfo = super().prepare_for_submission(folder)

        # Put the nnkp in the folder, with the correct filename
        nnkp_file = self.inputs.nnkp_file
        calcinfo.local_copy_list.append(
            (nnkp_file.uuid, nnkp_file.filename, '{}.nnkp'.format(self._SEEDNAME))
        )

        calcinfo.remote_symlink_list.extend(additional_remote_symlink_list)

        return calcinfo
