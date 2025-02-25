from pathlib import Path

from .config import SubjectConfig
from .utils import (
    create_precomputed_jsons,
    create_precomputed_nifties,
    download_bids_directory,
    download_derivative_directory,
    rename_coregistered_t1w_files,
)


def prepare_subject_files(
    project,
    subject_id,
    session,
    *,
    login_name=None,
    host_name=None,
    dry_run=False,
    check_args=None,
    download_bids_dir_kwargs=None,
    download_derivative_dir_kwargs=None,
    rename_coregistered_t1w_files_kwargs=None,
    create_precomputed_nifties_kwargs=None,
    create_precomputed_jsons_kwargs=None,
):
    """Download and BIDSify the bids directory and a precomputed derivative of your choice for a single subject to be run through Nibabies.

    Parameters
    ----------
    project : str
        The project label. For example, "ABC" or "BABIES".
    subject_id : str
        The subject label. For example, "1027".
    session : str
        The session label. For example, "newborn" or "sixmonth".
    dry_run : bool, optional
        If true, do not actually run the rsync commands, i.e. do not actually pull the
        data files, just print them. Default is False.
    check_args : dict, optional
        The arguments to use when checking the paths. Default is None, which uses
        {"local": True, "server": False, "mode": "error"}, which will check the local
        paths and raise an error if they do not exist.
    login_name : str
        The login name to use when connecting to the server. For example,
        ``"Lab Username"``. Default is None, which assumes that you have
        locally mounted the server. This must be provided if host_name is provided.
    host_name : str
        The host name to use when connecting to the server. For example,
        ``"XX.X.XXX.XXX"``. Default is None, which assumes that you have
        locally mounted the server. This must be provided if login_name is provided.
    download_bids_dir_kwargs : dict, optional
        The keyword arguments to pass to the download_bids_directory function.
        For example, ``{"anat": False, "func": False, "dwi": True}.``
        Default is ``None``, which will use ``{"anat": True, "func": True, "dwi": False}``,
        which downloads the anat and func directories from the server.
    download_derivative_dir_kwargs : dict, optional
        The keyword arguments to pass to the download_derivative_directory function,
        which will download a derivative directory from the server and copy it to
        the local derivative/precomputed directory for use in Nibabies.
        For example, ``{"derivative": "recon-all_final"}``, which will download the
        recon-all_final directory from the server and copy it to the local
        derivative/precomputed directory for use in Nibabies.
        Default is ``None``, which will download the ``recon-all`` directory from the
        server.
    rename_coregistered_t1w_files_kwargs : dict, optional
        The keyword arguments to pass to the rename_coregistered_t1w_files function.
        For example, ``{"anat_dir": Path("path/to/anat/dir")}``.
        Default is None, which uses the default values.
    create_precomputed_nifties_kwargs : dict, optional
        The keyword arguments to pass to the create_precomputed_nifties function,
        which will copy the ``aseg`` and ``brain_mask`` files from another derivative
        directory to the local derivative/precomputed directory for use in Nibabies.
        For example, ``{"aseg_nifti_fpath": './BABIES/derivatives/bibsnet/sub-1459/sub-1459_ses-newborn_space-T2w_desc-aseg_dseg.nii.gz'}``.
        Default is None, which will try to copy the ``aseg.nii.gz`` and
        ``brain_mask.nii.gz`` files in ``./project/derivatives/recon-all/sub-XXX/``
        to the local derivative/precomputed directory.
    create_precomputed_jsons_kwargs : dict, optional
        The keyword arguments to pass to the create_precomputed_jsons function,
        which will create the ``aseg.json`` and ``brain_mask.json`` sidecar files
        in the local derivative/precomputed directory, with a ``"SpatialReference"``
        key pointing to the spatial reference file in the ``bids/sub-XXX/anat/``
        directory.
        For example, ``{"aseg_nifti_fpath": '/Users/sealab/MRI_Processing/BABIES/derivatives/precomputed/sub-1401/anat/sub-1401_ses-newborn_space-T2w_desc-aseg_dseg.nii.gz'}``.   
        Default is ``None``, which will try to create the sidecar files for the ``aseg``
        and ``brain_mask`` nifti files in the local derivative/precomputed directory.
    
    Notes
    -----
    This function is a wrapper around the download_bids_directory, download_derivative_directory,
    rename_coregistered_t1w_files, create_precomputed_nifties, and create_precomputed_jsons functions.
    It 1) downloads the BIDS directory for a single subject, 2) downloads a derivative directory
    for the same subject, 3) renames any coregistered T1w files in the local anat directory to be
    compliant with BIDS, 4) copies the aseg and brain mask files from the local derivative directory
    to the local precomputed directory, and 5) creates json sidecar files for the aseg and brain mask
    nifti files in the local precomputed directory, with a "SpatialReference" key pointing to the
    spatial reference file in the local anat directory.
    """
    server_is_mounted = not (login_name or host_name) # True if on Whale computer

    subject_id = str(subject_id)

    if not server_is_mounted:
        if login_name and not host_name:
            raise ValueError("If login_name is provided, host_name must also be provided.")
        if host_name and not login_name:
            raise ValueError("If host_name is provided, login_name must also be provided.")

    if check_args is None:
        check_args = {"local": True, "server": False, "mode": "error"}
    
    if not download_bids_dir_kwargs.get("func", False):
        anat_only = True
    else:
        anat_only = False
    config = SubjectConfig(
        project,
        subject_id,
        session,
        get_spatial_file=False,
        anat_only=anat_only,
        server_is_mounted=server_is_mounted,
    )

    if download_bids_dir_kwargs is None:
        download_bids_dir_kwargs = {}
    
    anat = download_bids_dir_kwargs.get("anat", True)
    func = download_bids_dir_kwargs.get("func", True)
    dwi = download_bids_dir_kwargs.get("dwi", False)
    bids_dir = download_bids_dir_kwargs.get("output_dir", None)

    if not anat and not func and not dwi:
        raise ValueError(
            "You must download at least one of the anat, func, or dwi directories"
            f" from the server. You provided anat={anat}, func={func}, dwi={dwi}."
        )

    if bids_dir is None:
        bids_dir = Path(__file__).resolve().parent.parent / project / "MRI" / session / "bids"
    print(f"Downloading BIDS directory to {bids_dir}.")
    download_bids_directory(
        project=project,
        subject_id=subject_id,
        session=session,
        output_dir=bids_dir,
        dry_run=dry_run,
        login_name=login_name,
        host_name=host_name,
        **download_bids_dir_kwargs,
        )

    if download_derivative_dir_kwargs is None:
        download_derivative_dir_kwargs = {}
    
    derivative = download_derivative_dir_kwargs.get("derivative", "recon-all")
    derivative_dir = download_derivative_dir_kwargs.get("output_dir", None)
    if derivative_dir is None:
        derivative_dir = (
            Path(__file__).resolve().parent.parent /
            project /
            "MRI" /
            session / 
            "derivatives" /
            derivative
        )
    print(f"Downloading {derivative} directory to {derivative_dir}.")
    download_derivative_directory(
        project=project,
        subject_id=subject_id,
        session=session,
        derivative=derivative,
        output_dir=derivative_dir,
        dry_run=dry_run,
        login_name=login_name,
        host_name=host_name,
    )

    if dry_run:
        return # don't check paths or rename/move files

    config.get_spatial_file()
    config.check_paths(local=True, server=False, mode="error")
    
    
    if rename_coregistered_t1w_files_kwargs is None:
        rename_coregistered_t1w_files_kwargs = {}
    
    anat_dir = rename_coregistered_t1w_files_kwargs.get("anat_dir", None)
    if anat_dir is None:
        anat_dir = config["local_paths"]["sub_anatpath"]
    rename_coregistered_t1w_files(anat_dir)

    # If the user only plans to run the anatomical portion of Nibabies
    # they can skip the precomputed files
    if not download_bids_dir_kwargs.get("func", True):
        return

    if create_precomputed_nifties_kwargs is None:
        create_precomputed_nifties_kwargs = {}
    aseg_nifti_fpath = create_precomputed_nifties_kwargs.get("aseg_nifti_fpath", None)
    brain_mask_fpath = create_precomputed_nifties_kwargs.get("brain_mask_fpath", None)
    precomputed_dir = create_precomputed_nifties_kwargs.get("precomputed_dir", None)
    space = create_precomputed_nifties_kwargs.get("space", None)
    overwrite = create_precomputed_nifties_kwargs.get("overwrite", True) # we are overriding the default value of False
    
    if aseg_nifti_fpath is None:
        aseg_nifti_dir = derivative_dir / f"sub-{subject_id}"
        aseg_nifti_fpath = list(aseg_nifti_dir.rglob("aseg.nii.gz"))
        if not aseg_nifti_fpath:
            raise FileNotFoundError(
                f"Could not find aseg.nii.gz in {aseg_nifti_dir}."
                " Please provide the path to the aseg nifti file that you wish to have"
                " copied into the derivatives/precomputed directory, via the"
                " --create_precomputed_nifties_kwargs argument if you are using the"
                " _0_pull_subject_files command line script, or via the"
                " create_precomputed_nifties_kwargs argument if you are using"
                " the prepare_subject_files function. If you are using the"
                " _0_pull_subject_files.main function, you can provide the"
                " create_precomputed_nifties_kwargs argument."
            )
        aseg_nifti_fpath = aseg_nifti_fpath[0]
        print(f"Found precomputed derivative file: {aseg_nifti_fpath}.")
    if brain_mask_fpath is None:
        brain_mask_dir = derivative_dir / f"sub-{subject_id}"
        brain_mask_fpath = list(brain_mask_dir.rglob("brain_mask.nii.gz"))
        if not brain_mask_fpath:
            raise FileNotFoundError(
                f"Could not find brain_mask.nii.gz in {brain_mask_dir}."
                " Please provide the path to the brain mask nifti file that you wish to have"
                " copied into the derivatives/precomputed directory, via the"
                " --create_precomputed_nifties_kwargs argument if you are using the"
                " _0_pull_subject_files command line script, or via the"
                " create_precomputed_nifties_kwargs argument if you are using"
                " the prepare_subject_files function. If you are using the"
                " _0_pull_subject_files.main function, you can provide the"
                " create_precomputed_nifties_kwargs argument."
            )
        brain_mask_fpath = brain_mask_fpath[0]
        print(f"Found precomputed brain_mask file: {brain_mask_fpath}")
    if precomputed_dir is None:
        precomputed_dir = (
            Path(__file__).resolve().parent.parent /
            project /
            "MRI" /
            session /
            "derivatives" /
            "precomputed"
        )
    if space is None:
        space = "T2w" # this only matters if the nifti file does not have the space in the name
    create_precomputed_nifties(
        aseg_nifti_fpath=aseg_nifti_fpath,
        brain_mask_fpath=brain_mask_fpath,
        precomputed_dir=precomputed_dir,
        space=space,
        overwrite=overwrite
    )

    if create_precomputed_jsons_kwargs is None:
        create_precomputed_jsons_kwargs = {}
    precomputed_nifti_fpath = create_precomputed_jsons_kwargs.get("precomputed_nifti_fpath", None)
    precomputed_brain_mask_fpath = create_precomputed_jsons_kwargs.get("precomputed_brain_mask_fpath", None)
    spatial_reference_fpath = create_precomputed_jsons_kwargs.get("spatial_reference_fpath", None)

    if precomputed_nifti_fpath is None:
        precomputed_sub_dir = precomputed_dir / f"sub-{subject_id}"
        precomputed_nifti_fpath = list(precomputed_sub_dir.rglob("*desc-aseg_dseg.nii.gz"))
        if not precomputed_nifti_fpath:
            raise FileNotFoundError(
                "Could not find a precomputed nifti file (a file ending with desc-aseg_dseg.nii.gz"
                f" in {precomputed_sub_dir}."
                " Please provide the path to the aseg nifti file that you wish to have"
                " copied into the derivatives/precomputed directory, via the"
                " --create_precomputed_jsons_kwargs argument if you are using the"
                " _0_pull_subject_files command line script, or via the"
                " create_precomputed_jsons_kwargs argument if you are using"
                " the prepare_subject_files function. If you are using the"
                " _0_pull_subject_files.main function, you can provide the"
                " create_precomputed_jsons_kwargs argument."
            )
        precomputed_nifti_fpath = precomputed_nifti_fpath[0]
        print(f"Found aseg_desg file: {precomputed_nifti_fpath}.")
    if precomputed_brain_mask_fpath is None:
        precomputed_brain_mask_fpath = list(precomputed_sub_dir.rglob("*desc-brain_mask.nii.gz"))
        if not precomputed_brain_mask_fpath:
            raise FileNotFoundError(
                "Could not find a brain mask file ending with desc-brain_mask.nii.gz"
                f" in {precomputed_sub_dir}."
                " Please provide the path to the brain mask nifti file that you wish to have"
                " copied into the derivatives/precomputed directory, via the"
                " --create_precomputed_jsons_kwargs argument if you are using the"
                " _0_pull_subject_files command line script, or via the"
                " create_precomputed_jsons_kwargs argument if you are using"
                " the prepare_subject_files function. If you are using the"
                " _0_pull_subject_files.main function, you can provide the"
                " create_precomputed_jsons_kwargs argument."
            )
        precomputed_brain_mask_fpath = precomputed_brain_mask_fpath[0]
        print(f"Found brain_mask file: {precomputed_brain_mask_fpath}")
    if spatial_reference_fpath is None:
        if "T1w" in precomputed_nifti_fpath.name:
            space = "T1w"
        elif "T2w" in precomputed_nifti_fpath.name:
            space = "T2w"
        else:
            raise ValueError(
                f"Could not determine the space of the precomputed nifti file: {precomputed_nifti_fpath}."
                " So we cannot determine the spatial reference file for it."
                " Please make sure that the precomputed nifti file has the space entity"
                " in the name, e.g. sub-XXX_ses-YYY_space-T1w_desc-aseg_dseg.nii.gz."
            )
        spatial_reference_fpath = list(anat_dir.glob(f"*_{space}.nii.gz"))
        if not spatial_reference_fpath:
            raise FileNotFoundError(
                "Could not find a spatial reference file (a file ending with _T2w.nii.gz"
                f" in {bids_dir / subject_id / 'anat'}."
                " Please provide the path to the spatial reference file that you wish to have"
                " copied into the derivatives/precomputed directory, via the"
                " --create_precomputed_jsons_kwargs argument if you are using the"
                " _0_pull_subject_files command line script, or via the"
                " create_precomputed_jsons_kwargs argument if you are using"
                " the prepare_subject_files function. If you are using the"
                " _0_pull_subject_files.main function, you can provide the"
                " create_precomputed_jsons_kwargs argument."
            )
        spatial_reference_fpath = spatial_reference_fpath[0]
        print(f"Found spatial reference file: {spatial_reference_fpath}")
    create_precomputed_jsons(
        precomputed_nifti_fpath=precomputed_nifti_fpath,
        precomputed_brain_mask_fpath=precomputed_brain_mask_fpath,
        spatial_reference_fpath=spatial_reference_fpath
    )
    return config
