import argparse

from utils.run import prepare_subject_files


def main(
    subject,
    session,
    project,
    *,
    login_name=None,
    host_name=None,
    dry_run=False,
    download_bids_dir_kwargs=None,
    download_derivative_dir_kwargs=None,
    rename_coregistered_t1w_files_kwargs=None,
    create_precomputed_nifties_kwargs=None,
    create_precomputed_jsons_kwargs=None,
    ):
    prepare_subject_files(
        project,
        subject,
        session,
        login_name=login_name,
        host_name=host_name,
        dry_run=dry_run,
        download_bids_dir_kwargs=download_bids_dir_kwargs,
        download_derivative_dir_kwargs=download_derivative_dir_kwargs,
        rename_coregistered_t1w_files_kwargs=rename_coregistered_t1w_files_kwargs,
        create_precomputed_nifties_kwargs=create_precomputed_nifties_kwargs,
        create_precomputed_jsons_kwargs=create_precomputed_jsons_kwargs,
        check_args=None,
    )


def parse_args():
    # use argparse to get the subject id, session id, and project name
    parser = argparse.ArgumentParser(
        description=(
            "This script will 1) download the BIDS directory and 2) one of the derivative"
            " directories (e.g. recon-all, recon-all_final, bibsnet, etc.) from the server."
            " for a single subject."
            " Then it will 3) copy the derivative directory to the local derivative/precomputed"
            " directory for use in Nibabies, and 4) create JSON sidecar files"
            " in the local precomputed directory, that have a 'SpatialReference' Key"
            " pointing to the anatomical file in the same space as the precomputed file."
            " Finally, 5) it will rename any coregistered T1w files"
            " in the local anat directory, to be compliant with BIDS."
        )
    )
    parser.add_argument(
        "--project",
        choices=["BABIES", "ABC"],
        required=True,
        dest="project",
        help="project name, such as BABIES",
    )
    parser.add_argument(
        "--subject",
        type=str,
        required=True,
        dest="subject",
        help="subject label. such as 1103",
    )
    parser.add_argument(
        "--session",
        type=str,
        required=True,
        dest="session",
        help="session label, such as newborn",
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        dest="dry_run",
        help="If included, the function will not copy any files, but will print the rsync command.",
    )

    parser.add_argument(
        "--host_name",
        dest="host_name",
        help="The IP address of the server, for example the format can be 'XX.X.XXX.XXX'.",
    )
    parser.add_argument(
        "--login_name",
        dest="login_name",
        help="The username to use when connecting to the Whale computer, for example 'Lab Username'.",
    )
    parser.add_argument(
        "--download_bids_dir_kwargs",
        dest="download_bids_dir_kwargs",
        nargs="*",
        help=(
            "The keyword arguments to pass to the download_bids_directory function."
            " For example, --download_bids_dir_kwargs anat=False func=False dwi=True.",
            "If not provided, the default is {'anat': True, 'func': True, 'dwi': False}," 
            " which will download the anat and func directories from the server."
        ),
    )
    parser.add_argument(
        "--download_derivative_dir_kwargs",
        dest="download_derivative_dir_kwargs",
        nargs="*",
        help=(
            "The keyword arguments to pass to the download_derivative_directory function."
            " Which will download a derivative directory from the server and copy it to"
            " the local derivative/precomputed directory for use in Nibabies."
            " For example, ``--download_derivative_dir_kwargs derivative=recon-all_final``."
            " If not provided, the default is ``{'derivative': 'recon-all'}``, which will"
            " download the 'precomputed files' from the derivatives/recon-all' directory"
            " and copy them to the local derivatives/precomputed directory for use in"
            " Nibabies."
        ),
    )
    parser.add_argument(
        "--rename_coregistered_t1w_files_kwargs",
        dest="rename_coregistered_t1w_files_kwargs",
        nargs="*",
        help=("The keyword arguments to pass to the rename_coregistered_t1w_files function."
              " Which will rename the coregistered T1w files in the anat directory to be"
              " compliant with BIDS."
              " For example, ``--rename_coregistered_files_kwargs anat_dir='path/to/anat_dir'``."
              " If not provided, the default is ``{'anat_dir': 'bids/subject/anat')}``,"
              " which will rename the coregistered T1w files in the anat directory."
              " This is necessary for the BIDS validator to pass."
              ),
    )
    parser.add_argument(
        "--create_precomputed_nifties_kwargs",
        dest="create_precomputed_nifties_kwargs",
        nargs="*",
        help=(
            "The keyword arguments to pass to the create_precomputed_nifties function."
            " Which will copy the ``aseg`` and ``brain_mask`` nifti files from another"
            " derivative directory (e.g. recon-all, recon-all_final, bibsnet, etc.)"
            " into the ``precomputed`` directory, for use by Nibabies."
            " For example, ``--create_precomputed_nifties_kwargs aseg_nifti_fpath='./BABIES/derivatives/bibsnet/sub-1459/sub-1459_ses-newborn_space-T2w_desc-aseg_dseg.nii.gz'``."
            " If not provided, we will try to copy the ``aseg.nii.gz`` and"
            " ``brain_mask.nii.gz`` files in ``./project/derivatives/recon-all/sub-XXX/``"
            " to ``./project/derivatives/precomputed``."
        ),
    )
    parser.add_argument(
        "--create_precomputed_jsons_kwargs",
        dest="create_precomputed_jsons_kwargs",
        nargs="*",
        help=(
            "The keyword arguments to pass to the create_precomputed_jsons function."
            " Which will create json sidecar files for the ``aseg_dseg`` and" 
            " ``brain_mask`` nifti files that were copied into the ``precomputed``"
            " directory by the ``create_precomputed_nifties`` function in the previous step."
            " For example,"
            " ``--create_precomputed_jsons_kwargs aseg_nifti_fpath='/Users/sealab/MRI_Processing/BABIES/derivatives/precomputed/sub-1401/anat/sub-1401_ses-newborn_space-T2w_desc-aseg_dseg.nii.gz'``"
            " If not provided, we will try to create the json files in ``./project/derivatives/precomputed/sub-[subject]/anat``."
        ),
    )
    args = parser.parse_args()
    return vars(args)


def parse_kwargs(pairs):
    """Convert a list of key=value strings from the command line into a dictionary."""
    kwargs = {}
    for pair in pairs:
        if "=" not in pair:
            raise argparse.ArgumentTypeError(f"Expected key=value pair, but got {pair}")
        key, value = pair.split("=", 1)
        kwargs[key] = value
    return kwargs


def run_main():
    args = parse_args()
    # the command line arguments for the kwargs below come in as a list of strings
    # we need to convert them to a dictionary
    for key in [
        "download_bids_dir_kwargs",
        "download_derivative_dir_kwargs",
        "rename_coregistered_t1w_files_kwargs",
        "create_precomputed_nifties_kwargs",
        "create_precomputed_jsons_kwargs",
    ]:
        if args[key]:
            args[key] = parse_kwargs(args[key])
    main(**args)


if __name__ == "__main__":
    run_main()
