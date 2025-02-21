import shutil
import subprocess
from glob import glob
from pathlib import Path
from warnings import warn

from .config import Config

BABIES_SERVER = Path("/Volumes") / "HumphreysLab" / "Daily_2" / "BABIES" / "MRI"


def rsync_to_server(project, subject, session, dry_run=False, verbose="INFO"):
    """Use rsync to send files in Documents/MRI to the HumphreysLab server.

    Parameters
    ----------
    project : str
        The project name. Must be either "BABIES" or "ABC".
    subject : str
        The subject id, for example "12001". Don't include the "sub-" prefix.
    session : str
        The session. Must be either "newborn" or "six_month", or "sixmonth", which is
        an alias for "six_month".
    dry_run : bool
        If True, the function will not copy any files, but will print the rsync command.
        Use this if you want to validate the behaviour of this function before
        committing to the result. Default is False.
    verbose : str
        The verbosity level. Must be either "QUIET", "INFO", or "DEBUG". Default is "INFO".
    """
    if project not in ["BABIES", "ABC"]:
        raise ValueError("project must be either 'BABIES' or 'ABC', but got: {project}")
    if not subject.isnumeric():
        raise ValueError("subject must be a number, but got: {subject}")
    if session not in ["newborn", "six_month", "sixmonth"]:
        raise ValueError(
            "session must be either 'newborn' or 'six_month', but got: {session}"
        )
    if project == "ABC" and session == "six_month":
        session = "sixmonth"
    elif project == "BABIES" and session == "sixmonth":
        session = "six_month"

    input_dir = Path(".") / project / session
    BABIES_SERVER = Path("/Volumes") / "HumphreysLab" / "Daily_2" / "BABIES" / "MRI"
    ABC_SERVER = Path("/Volumes") / "HumphreysLab" / "Daily_2" / "ABC" / "MRI"

    if project == "BABIES":
        output_dir = BABIES_SERVER
    elif project == "ABC":
        output_dir = ABC_SERVER

    # rsync the bids directory
    bids_path = f"{str(input_dir)}/./bids/sub-{subject}"
    assert bids_path.exists(), f"{bids_path} does not exist"
    do_rsync(bids_path, output_dir, dry_run, verbose)

    # rsync the derivatives/Nibabies/sourcedata/freesurfer directory
    freesurfer_path = (
        f"{str(input_dir)}/./derivatives/NiBabies/sourcedata/freesurfer/sub-{subject}"
    )
    assert freesurfer_path.exists(), f"{freesurfer_path} does not exist"
    do_rsync(freesurfer_path, output_dir, dry_run, verbose)

    # rsync the derivatives/Nibabies/sourcedata/subject directory
    sourcedata_path = (
        f"{str(input_dir)}/./derivatives/NiBabies/sourcedata/sub-{subject}"
    )
    assert sourcedata_path.exists(), f"{sourcedata_path} does not exist"
    do_rsync(sourcedata_path, output_dir, dry_run, verbose)

    # rsync the derivatives/sourcedata directory
    sourcedata_path = f"{str(input_dir)}/./sourcedata/sub-{subject}"
    assert sourcedata_path.exists(), f"{sourcedata_path} does not exist"
    do_rsync(sourcedata_path, output_dir, dry_run, verbose)

    # rsync the dicom2bids directory
    dicom2bids_path = f"{str(input_dir)}/./tmp_dcm2bids/sub-{subject}_ses-{session}"
    assert dicom2bids_path.exists(), f"{dicom2bids_path} does not exist"
    do_rsync(dicom2bids_path, output_dir, dry_run, verbose)


def download_bids_directory(
    project,
    subject_id,
    session,
    *,
    output_dir,
    anat=True,
    func=True,
    dwi=False,
    dry_run=False,
    login_name=None,
    host_name=None,
):
    """use rsync to download the bids directory from 1 subject for a project like BABIES.

    Parameters
    ----------
    project : str
        Must be ``"BABIES"`` or ``"ABC"``, which will be converted to the
        path for the project on the HumphreysLab server.
    subject_id : str
        The subject to copy. For example "12001".
    session : str
        The session to copy. Must be either "newborn" or "six_month".
    output_dir : path-like
        The output directory to copy to. Can either be a relative or absolute path.
        Usually this will be the path to the local MRI-Processing BIDS directory,
        e.g. ``"/Users/sealab/MRI_Processing/BABIES/newborn/bids"``.
        If ``None``, the current working directory will be used.
    dry_run : bool
        If True, the function will not copy any files, but will print the rsync command.
        Use this if you want to validate the behaviour of this function before
        committing to the result. Default is False.
    anat : bool
        If True, the anat subdirectory will be copied. Default is True.
    func : bool
        If True, the func and fmap subdirectories will be copied. Default is True.
    dwi : bool
        If True, the dwi subdirectory will be copied. Default is False.
    login_name : str
        The login name to use when connecting to the server. For example,
        ``"Lab Username"``. Default is None, which assumes that you have
        locally mounted the server. This must be provided if host_name is provided.
    host_name : str
        The host name to use when connecting to the server. For example,
        ``"XX.X.XXX.XXX"``. Default is None, which assumes that you have
        locally mounted the server. This must be provided if login_name is provided.
    
    Returns
    -------
    output_dir : path-like
        The path to the local BIDS/subject directory that was copied from the server.
    
    Notes
    -----
    .. important::
        
        - If you are not on the Whale computer, you must provide the login_name and host_name
            parameters to connect to the server.
        - Unlike the bids/subject directories on the server, this function will add a session
            directory, e.g. ``"bids/sub-12001/ses-newborn"``. This is to be compliant with BIDS
            and with Nibabies.
    
    Examples
    --------
    >>> from utils.utils import download_bids_directory
    >>> download_bids_directory(
    ...     project="BABIES",
    ...     subject_id=1375,
    ...     session="newborn",
    ...     output_dir="/Users/sealab/MRI_Processing/BABIES/newborn/bids",
    ...     anat=True,
    ...     func=True,
    ...     dwi=False,
    ...     )

    If you are not on the Whale computer, you can use the login_name and host_name
    parameters to connect to the server. For example:

    >>> download_bids_directory(
    ...     project="BABIES",
    ...     subject_id=1375,
    ...     session="newborn",
    ...     output_dir="/Users/sealab/MRI_Processing/BABIES/newborn/bids",
    ...     login_name="Lab Username",
    ...     host_name="XX.X.XXX.XXX",
    ...     )
    """
    BABIES = Path("/Volumes") / "HumphreysLab" / "Daily_2" / "BABIES" / "MRI"
    ABC = Path("/Volumes") / "HumphreysLab" / "Daily_2" / "ABC" / "MRI"
    server_is_mounted = login_name is None or host_name is None

    if project == "BABIES":
        project_dir = BABIES
        session_dirname = "six_month" if session == "sixmonth" else session
    elif project == "ABC":
        project_dir = ABC
        session_dirname = session
    
    sub_entity = f"sub-{subject_id}"
    ses_entity = f"ses-{session}"
    session_dir = project_dir / session_dirname
    bids_dir = session_dir / "bids"
    sub_dir = bids_dir / sub_entity / ses_entity
    if not server_is_mounted:
        sub_dir = Path(f"{login_name}@{host_name}:{sub_dir}")

    if output_dir is None:
        output_dir = Path.cwd()
    output_dir = Path(output_dir).expanduser().resolve()

    ##########################################################################
    # CHECKS
    ##########################################################################

    if not server_is_mounted:
        if login_name is None:
            raise ValueError(f"To download from a remote server, login_name must be provided. but got {login_name}")
        if host_name is None:
            raise ValueError(f"To download from a remote server, host_name must be provided. But got {host_name}")
    if not output_dir.exists():
        raise FileNotFoundError(f"{output_dir} does not exist")
    if not isinstance(subject_id, (str, int)):
        raise ValueError(
            f"subject_id must be a string or number, but got: {subject_id}\n"
            "Example: 12001 for sub-12001"
        )
    if session not in ["newborn", "sixmonth"]:
        raise ValueError(
            "session must be either 'newborn' or 'sixmonth',"
            f" but got: {session}"
        )
    if not isinstance(anat, bool):
        raise ValueError(f"anat_only must be a True or False, but got: {anat}")
    if not isinstance(func, bool):
        raise ValueError(f"func_only must be a True or False, but got: {func}")
    if not isinstance(dwi, bool):
        raise ValueError(f"dwi_only must be a True or False, but got: {dwi}")
    if not isinstance(dry_run, bool):
        raise ValueError(f"dry_run must be a True or False, but got: {dry_run}")
    
    ##########################################################################
    # COPY
    ##########################################################################
    # Make the output parent directory if it doesn't exist
    if not (output_dir / sub_entity).exists():
        (output_dir / sub_entity / ses_entity).mkdir(parents=True)
    if anat:
        do_rsync(
            input_dir=f"{sub_dir}/anat/*_T?w.*",
            output_dir=f"{output_dir}/{sub_entity}/{ses_entity}/anat",
            dry_run=dry_run,
            flags="-rltv",
        )
    if func:
        do_rsync(
            f"{sub_dir}/func",
            output_dir=f"{output_dir}/{sub_entity}/{ses_entity}",
            dry_run=dry_run,
            flags="-rltv",
        )
        do_rsync(
            f"{sub_dir}/fmap",
            output_dir=f"{output_dir}/{sub_entity}/{ses_entity}",
            dry_run=dry_run,
            flags="-rltv",
        )
    if dwi:
        do_rsync(
            f"{sub_dir}/dwi",
            output_dir=f"{output_dir}/{sub_entity}/{ses_entity}",
            dry_run=dry_run,
            flags="-rltv",
        )
    return output_dir / sub_entity

def download_derivative_directory(
    project,
    subject_id,
    session,
    *,
    derivative: str,
    output_dir=None,
    dry_run=False,
    login_name=None,
    host_name=None,
):
    """use rsync to download the precomputed directory from 1 subject for a project like BABIES.

        The "precomputed" files are the segmented anatomical files. They are usually pulled
        from derivatives/bibsnet, derivatives/recon-all, derivatives/recon-all_final, or
        derivatives/precomputed.

        Parameters
        ----------
        project : str
            Must be ``"BABIES"`` or ``"ABC"``, which will be converted to the
            path for the project on the HumphreysLab server.
        subject_id : str
            The subject to copy. For example "12001".
        session : str
            The session to copy. Must be either "newborn" or "six_month".
        derivative : str
            The derivative to copy. For example ``"precomputed"``, ``"recon-all"``,
            ``"bibsnet"``, or ``"recon-all_final"``.
        output_dir : path-like
            The local output directory to copy to. For example:

            - ``"/Users/sealab/MRI_Processing/BABIES/newborn/derivatives/precomputed"``, or
            - ``"~/MRI_Processing/BABIES/newborn/derivatives/bibsnet"``, or
            - ``"~/MRI_Processing/BABIES/newborn/derivatives/recon-all"``.
            
            Can either be a relative or absolute path. Default is ``None``, which will
            use the current directory of the python interpreter.
            This path must exist before running this function. If it doesnt, pleas
            create it first.
        dry_run : bool
            If True, the function will not copy any files, but will print the rsync command.
            Use this if you want to validate the behaviour of this function before
            committing to the result. Default is False.
        login_name : str
            The login name to use when connecting to the server. For example,
            ``"Lab Username"``. Default is None, which assumes that you have
            locally mounted the server. This must be provided if host_name is provided.
        host_name : str
            The host name to use when connecting to the server. For example,
            ``"XX.X.XXX.XXX"``. Default is None, which assumes that you have
            locally mounted the server. This must be provided if login_name is provided.
    
        Returns
        -------
        output_dir : path-like
            The path to the local derivative/subject directory that was copied from the server.

        Examples
        --------
        >>> from utils.utils import download_derivative_directory
        >>> download_derivative_directory(
        ...     project="BABIES",
        ...     subject_id=1375,
        ...     session="newborn",
        ...     derivative="recon-all_final",
        ...     output_dir="/Users/sealab/MRI_Processing/BABIES/newborn/derivatives/recon-all_final",
        ...     )

        If you are not on the Whale computer, you can use the login_name and host_name
        parameters to connect to the server. For example:
        >>> download_derivative_directory(
        ...     project="BABIES",
        ...     subject_id=1375,
        ...     session="newborn",
        ...     derivative="recon-all_final",
        ...     output_dir="/Users/sealab/MRI_Processing/BABIES/newborn/derivatives/recon-all_final",
        ...     login_name="Lab Username",
        ...     host_name="XX.X.XXX.XXX",
        ...     )
    """
    BABIES = Path("/Volumes") / "HumphreysLab" / "Daily_2" / "BABIES" / "MRI"
    ABC = Path("/Volumes") / "HumphreysLab" / "Daily_2" / "ABC" / "MRI"
    server_is_mounted = login_name is None or host_name is None

    if project == "BABIES":
        project_dir = BABIES
        session_dirname = "six_month" if session == "sixmonth" else session
    elif project == "ABC":
        project_dir = ABC
        session_dirname = session

    sub_entity = f"sub-{subject_id}"
    ses_entity = f"ses-{session}"
    session_dir = project_dir / session_dirname
    deriv_dir = session_dir / "derivatives" / derivative
    sub_dir = deriv_dir / sub_entity
    if not server_is_mounted:
        sub_dir = Path(f"{login_name}@{host_name}:{sub_dir}")

    if output_dir is None:
        output_dir = Path.cwd()
    output_dir = Path(output_dir).expanduser().resolve()

    ##########################################################################
    # CHECKS
    ##########################################################################

    if not server_is_mounted:
        if login_name is None:
            raise ValueError(f"To download from a remote server, login_name must be provided. but got {login_name}")
        if host_name is None:
            raise ValueError(f"To download from a remote server, host_name must be provided. But got {host_name}")
    if not output_dir.exists():
        raise FileNotFoundError(
            f"{output_dir} does not exist. If this path is correct but does not exist, please create it first."
            )
    if not isinstance(subject_id, (str, int)):
        raise ValueError(
            f"subject_id must be a string or number, but got: {subject_id}\n"
            "Example: 12001 for sub-12001"
        )

    if session not in ["newborn", "sixmonth"]:
        raise ValueError(
            "session must be either 'newborn' or 'sixmonth',"
            f" but got: {session}"
        )
    if not isinstance(dry_run, bool):
        raise ValueError(f"dry_run must be a True or False, but got: {dry_run}")

    if login_name is not None or host_name is not None:
        if login_name is None:
            raise ValueError("login_name must be provided if host_name is provided")
        if host_name is None:
            raise ValueError("host_name must be provided if login_name is provided")

    do_rsync(
        sub_dir,
        output_dir,
        flags="-rltv",
        dry_run=dry_run,
    )
    return output_dir / sub_entity

    

def pull_subject_files(
    project,
    subject_id,
    session,
    *,
    output_dir,
    anat_only=False,
    bids_only=False,
    pull_dwi=False,
    ip_address=None,
    username=None,
    dry_run=False,
    verbose="INFO",
):
    """use rsync to pull the bids directory from 1 subject for a project like BABIES.

    Parameters
    ----------
    project : str
        Must be ``"BABIES"`` or ``"ABC"``, which will be converted to the
        path for the project on the HumphreysLab server.
    subject_id : str
        The subject to copy. For example "12001".
    session : str
        The session to copy. Must be either "newborn" or "six_month".
    output_dir : path-like
        The output directory to copy to. Can either be a relative or absolute path.
    dry_run : bool
        If True, the function will not copy any files, but will print the rsync command.
        Use this if you want to validate the behaviour of this function before
        committing to the result. Default is False.
    pull_dwi : bool
        If True, the function will pull the bids dwi directory. Default is False.
    anat_only : bool
        If True, the function will only pull the anatomical data. Default is False.
    bids_only : bool
        If True, the function will only pull the bids data. Default is False.
    ip_address : str
        The IP address of the whale computer, for example format "XX.X.XXX.XXX".
        Default is None, which assumes that the HumphreysLab server is mounted on
        the local computer. This option is useful if you are running this function
        on a remote computer such as the ACCRE cluster.
    username : str
        If ip_address is not None, The username to use when connecting to the whale
        computer, for example "Lab Username". Default is None, which does not do
        anything if ip_address is None as well, but will raise an error if ip_address
        is not None and username is None.
    """
    BABIES = Path("/Volumes") / "HumphreysLab" / "Daily_2" / "BABIES" / "MRI"
    ABC = Path("/Volumes") / "HumphreysLab" / "Daily_2" / "ABC" / "MRI"
    if project == "BABIES":
        input_dir = BABIES
        session = "six_month" if session == "sixmonth" else session
    elif project == "ABC":
        input_dir = ABC

    output_dir = Path(output_dir)

    ##########################################################################
    # CHECKS
    ##########################################################################

    # if one of ip_address or username is not None, then both must be provided
    need_username = ip_address is not None and username is None
    need_ip_address = ip_address is None and username is not None
    if need_username or need_ip_address:
        raise ValueError(
            "If either ip_address or username is not None, the other must be provided."
            f" Got ip_address={ip_address} and username={username}"
        )

    server_is_mounted = ip_address is None

    if not input_dir.exists() and server_is_mounted:
        raise FileNotFoundError(f"{input_dir} does not exist")
    else:
        warn(
            "You are pulling files from a remote server. We cannot assure that the directories"
            f" you are trying to pull actually exist. Trying to pull: {input_dir}\n"
        )
    if not output_dir.exists() and server_is_mounted:
        raise FileNotFoundError(f"{output_dir.resolve()} does not exist")
    if not subject_id.isnumeric():
        raise ValueError(
            f"subject_id must be a number, but got: {subject_id}\n"
            "Example: 12001 for sub-12001"
        )
    subject = f"sub-{subject_id}"

    if session not in ["newborn", "six_month"]:
        raise ValueError(
            f"session must be either 'newborn' 'sixmonth', or 'six_month',"
            " but got: {session}"
        )
    if not isinstance(anat_only, bool):
        raise ValueError(f"anat_only must be a True or False, but got: {anat_only}")
    if verbose not in ["QUIET", "INFO", "DEBUG"]:
        raise ValueError(
            f"verbose must be either 'QUIET', 'INFO', or 'DEBUG', but got: {verbose}"
        )

    session_dir = input_dir / f"{session}"
    bids_dir = session_dir / "bids" / subject
    recon_dir = session_dir / "derivatives" / "recon-all" / subject

    if server_is_mounted:
        assert session_dir.exists(), f"{session_dir} does not exist"
        assert bids_dir.exists(), f"{bids_dir} does not exist"
        assert recon_dir.exists(), f"{recon_dir} does not exist"
    else:
        warn(
            "You are pulling files from a remote server. We cannot assure that the directories\n"
            " you are trying to pull actually exist. Here are the directories we are trying to pull:\n"
            f"    {bids_dir}\n"
            f"    {recon_dir}\n"
            f"    {session_dir}\n"
        )

    ##########################################################################
    # COPY
    ##########################################################################

    # we should use a logger instead of print
    print(
        f"Copying {subject} directories from:\n {input_dir.resolve()} to:\n {output_dir.resolve()}"
    )

    # copy the entire subject directory
    filter_dwi = not pull_dwi
    filter_fpath = create_filter_file(
        output_dir,
        subject_id=subject_id,
        session_dir=session,
        anat_only=anat_only,
        bids_only=bids_only,
        filter_dwi=filter_dwi
    )
    rsync_input = f"{str(input_dir.parent.parent)}/./{project}/MRI/{session}"
    if ip_address is not None:
        rsync_input = f"{username}@{ip_address}:" + rsync_input
    do_rsync(
        rsync_input,
        output_dir,
        filter_file=filter_fpath,
        dry_run=dry_run,
        server_is_mounted=server_is_mounted,
        verbose=verbose,
    )


def do_rsync(
    input_dir,
    output_dir,
    filter_file=None,
    dry_run=False,
    flags="-ahR",
    verbose="INFO",
):
    """Use rsync to copy files from one directory to another."""

    flags = flags
    if verbose == "INFO":
        flags += "v"
    elif verbose == "DEBUG":
        flags += "vv"
    if dry_run:
        flags += "n"

    input_dir = str(input_dir)
    # if the user is on the whale computer, shell expansion does not work under the hood..
    if "@" not in input_dir:
        if "*" in input_dir or "?" in input_dir:
            files = glob(input_dir)
            if len(files) == 0:
                raise FileNotFoundError(f"No files found with pattern: {input_dir}")
            input_dir = " ".join(files)        
    command = [
        "rsync",
        f"{flags}",
        f"{input_dir}",
        f"{output_dir}",
        "--prune-empty-dirs",
        "--progress",
    ]
    if filter_file is not None:
        command += [f"--filter=merge {filter_file}"]
    print("\n")
    print(" ".join(command))
    print("\n")
    subprocess.run(command, check=True)


def delete_directory(path):
    """Remove a path and all its contents."""
    if not path.exists():
        raise FileNotFoundError(f"{path} does not exist")
    shutil.rmtree(path)


def create_precomputed_jsons(
    precomputed_nifti_fpath,
    precomputed_brain_mask_fpath,
    spatial_reference_fpath,
):
    """Create json files for the aseg and brain_mask nifties in the precomputed directory.

    Parameters
    ----------
    precomputed_nifti_fpath : path-like
        The path to the aseg nifti file. For example,
        ``"/Users/sealab/MRI_Processing/BABIES/derivatives/precomputed/sub-1401/anat/sub-1401_ses-newborn_space-T2w_desc-aseg_dseg.nii.gz"``.
    precopmuted_brain_mask_fpath : path-like
        The path to the brain mask nifti file. For example,
        ``"/Users/sealab/MRI_Processing/BABIES/derivatives/precomputed/sub-1401/anat/sub-1401_ses-newborn_space-T2w_desc-brain_mask.nii.gz"``.
    spatial_reference_fpath : path-like
        The path to the nifti file (within the bids/anat directory) that you want to use
        as the spatial reference for the precomputed aseg and brain mask files.
        For example:
        ``"/Users/sealab/MRI_Processing/BABIES/bids/subject/session/anat/sub-1401_ses-newborn_T2w.nii.gz"``.
    
    Returns
    -------
    aseg_json_fpath : path-like
        The path to the aseg json file.
    brain_mask_json_fpath : path-like
        The path to the brain mask json file.

    Examples
    --------
    >>> from utils.utils import create_precomputed_jsons
    >>> create_precomputed_jsons(
    ...     precomputed_nifti_fpath="/Users/sealab/MRI_Processing/BABIES/derivatives/precomputed/sub-1401/anat/sub-1401_ses-newborn_space-T2w_desc-aseg_dseg.nii.gz",
    ...     precopmuted_brain_mask_fpath="/Users/sealab/MRI_Processing/BABIES/derivatives/precomputed/sub-1401/anat/sub-1401_ses-newborn_space-T2w_desc-brain_mask.nii.gz",
    ...     spatial_reference_fpath="/Users/sealab/MRI_Processing/BABIES/bids/subject/session/anat/sub-1401_ses-newborn_T2w.nii.gz",
    ...     )
    """
    spatial_reference_fpath = Path(spatial_reference_fpath).expanduser().resolve()
    aseg_nifti_fpath = Path(precomputed_nifti_fpath).expanduser().resolve()
    brain_mask_fpath = Path(precomputed_brain_mask_fpath).expanduser().resolve()

    aseg_json_fpath = aseg_nifti_fpath.with_suffix(".json")
    brain_mask_json_fpath = brain_mask_fpath.with_suffix(".json")
    bids_index = Path(spatial_reference_fpath).parts.index("bids")
    bpath = Path(*spatial_reference_fpath.parts[: bids_index + 1])
    spatial_reference_fname = spatial_reference_fpath.relative_to(bpath)
    # Create a JSON file and add the Spatial key to the jsons
    aseg_json = Config()
    aseg_json["SpatialReference"] = spatial_reference_fname
    aseg_json.save(aseg_json_fpath)
    brain_mask_json = Config()
    brain_mask_json["SpatialReference"] = spatial_reference_fname
    brain_mask_json.save(brain_mask_json_fpath)
    return aseg_json_fpath, brain_mask_json_fpath


def create_precomputed_nifties(
    aseg_nifti_fpath,
    brain_mask_fpath,
    precomputed_dir,
    space="T2w",
    overwrite=False,
):
    """Copy a derived aseg and brain mask nifti file to the precomputed directory.

    Parameters
    ----------
    aseg_nifti_fpath : path-like
        The path to the nifti file that you want to copy into the precomputed
        directory. Often times this is the ``aseg.nii.gz`` file in the recon-all
        directory. It can also be the ``sub-XXXX_ses-XX_space-T2w_desc-aseg_dseg.nii.gz``
        file in the bibsnet directory. For example:

        - ``"/users/sealab/MRI_Processing/BABIES/newborn/derivatives/recon-all/sub-1459/aseg.nii.gz"``.
        - ``"/users/sealab/MRI_Processing/BABIES/derivatives/recon-all_final/sub-1459/aseg.nii.gz"``.
        - ``"/users/sealab/MRI_Processing/BABIES/derivatives/bibsnet/sub-1459/sub-1459_ses-newborn_space-T2w_desc-aseg_dseg.nii.gz"``.

        This can be a relative or absolute path.
    brain_mask_fpath : path-like
        The path to the brain mask file that you want to copy into the precomputed
        directory. Often times this is the ``brain_mask.nii.gz`` file in the recon-all
        directory. It can also be the ``sub-XXXX_ses-XX_space-T2w_desc-brain_mask.nii.gz``
        file in the bibsnet directory. For example:

        - ``"/users/sealab/MRI_Processing/BABIES/newborn/derivatives/recon-all/sub-1459/brain_mask.nii.gz"``.
        - ``"/users/sealab/MRI_Processing/BABIES/derivatives/recon-all_final/sub-1459/brain_mask.nii.gz"``.
        - ``"/users/sealab/MRI_Processing/BABIES/derivatives/bibsnet/sub-1459/sub-1459_ses-newborn_space-T2w_desc-brain_mask.nii.gz"``.

    precomputed_dir : path-like
        The path to the precomputed derivatives directory, excluding the subject and modality (e.g. anat).
        For example, ``"/Users/sealab/MRI_Processing/BABIES/derivatives/precomputed"``.
    space : str
        This only applies if ``aseg_nifti_fpath`` and ``brain_mask_fpath`` don't contain the
        space in the filename (e.g. if they are the aseg.nii.gz and brain_mask.nii.gz).
        In that case, specify here the space of the aseg and brain_mask files
        Must be ``"T1w"`` or ``"T2w"``. Default is "T1w".
    overwrite : bool
        If True, the function will overwrite the files in the precomputed directory (if a file
        with the same name already exists). If False, the function will raise an error if a file
        with the same name already exists. Default is False.
    
    Returns
    -------
    precomputed_aseg_fpath : path-like
        The path to the precomputed aseg file.
    precomputed_brain_mask_fpath : path-like
        The path to the precomputed brain mask file.

    Notes
    -----
    This will copy these files to the precomputed directory. If the do not fillow the bids convention,
    then this function will rename them to the following format:

    - ``{subject}_ses-{session}_space-{space}_desc-aseg_dseg.nii.gz``
    - ``{subject}_ses-{session}_space-{space}_desc-brain_mask.nii.gz``.

    Examples
    --------
    >>> from utils.utils import create_precomputed_nifties
    >>> create_precomputed_nifties(
    ...     aseg_nifti_fpath="/Users/sealab/MRI_Processing/BABIES/derivatives/recon-all/sub-1459/aseg.nii.gz",
    ...     brain_mask_fpath="/Users/sealab/MRI_Processing/BABIES/derivatives/recon-all/sub-1459/brain_mask.nii.gz",
    ...     precomputed_dir="/Users/sealab/MRI_Processing/BABIES/derivatives/precomputed",
    """
    # XXX: If the user passes in the BIBSnet output, we shouldn't rename the files and create jsons manually.
    # XXX: We should just copy them over to the precomputed directory.

    # Checks
    aseg_nifti_fpath = Path(aseg_nifti_fpath).expanduser().resolve()
    brain_mask_fpath = Path(brain_mask_fpath).expanduser().resolve()
    precomputed_dir = Path(precomputed_dir).expanduser().resolve()
    if not aseg_nifti_fpath.exists():
        raise FileNotFoundError(
            f"{aseg_nifti_fpath} does not exist. Can't copy it to precomputed directory")
    if not brain_mask_fpath.exists():
        raise FileNotFoundError(
            f"{brain_mask_fpath} does not exist. Can't copy it to precomputed directory"
            )
    if not precomputed_dir.exists():
        raise FileNotFoundError(
            f"{precomputed_dir} does not exist. Please pass a valid precomputed directory to copy files into."
            )
    if "T1w" not in str(aseg_nifti_fpath) and "T2w" not in str(aseg_nifti_fpath):
        if space not in ["T1w", "T2w"]:
            raise ValueError(
                f"{aseg_nifti_fpath.name} does not contain the space in the filename. "
                "Please specify the space in the filename. The "
                f"space must be either 'T1w' or 'T2w', but got: {space}"
                )

    subject = get_subject_from_bids_path(aseg_nifti_fpath)
    subject_id = subject.split("-")[1]
    session = get_session_from_bids_path(aseg_nifti_fpath)
    if "ses-" in session:
        session = session.split("-")[1]
    precomputed_aseg_fname = (
        f"sub-{subject_id}_ses-{session}_space-{space}_desc-aseg_dseg.nii.gz"
    )
    precomputed_brain_mask_fname = (
        f"sub-{subject_id}_ses-{session}_space-{space}_desc-brain_mask.nii.gz"
    )
    if not (precomputed_dir / f"sub-{subject_id}").exists():
        (precomputed_dir / f"sub-{subject_id}").mkdir()
        (precomputed_dir / f"sub-{subject_id}" / "anat").mkdir()
    
    precomputed_aseg_fpath = (
        precomputed_dir / f"sub-{subject_id}" / "anat" / precomputed_aseg_fname
    )
    precomputed_brain_mask_fpath = (
        precomputed_dir / f"sub-{subject_id}" / "anat" / precomputed_brain_mask_fname
    )

    # copy aseg and mask to precomputed directory
    if precomputed_aseg_fpath.exists():
        if not overwrite:
            raise FileExistsError(
                f"{precomputed_aseg_fpath} already exists. Set overwrite=True "
                " to overwrite."
            )
        else:
            warn(f"{precomputed_aseg_fpath} already exists. Overwriting.")
            precomputed_aseg_fpath.unlink()

    if precomputed_brain_mask_fpath.exists():
        if not overwrite:
            raise FileExistsError(
                f"{precomputed_brain_mask_fpath} already exists. Set overwrite=True "
                " to overwrite."
            )
        else:
            warn(f"{precomputed_brain_mask_fpath} already exists. Overwriting.")
            precomputed_brain_mask_fpath.unlink()
    print(f"Copying {aseg_nifti_fpath} to {precomputed_aseg_fpath}\n")
    shutil.copy(aseg_nifti_fpath, precomputed_aseg_fpath)
    print(f"Copying {brain_mask_fpath} to {precomputed_brain_mask_fpath}\n")
    shutil.copy(brain_mask_fpath, precomputed_brain_mask_fpath)
    return precomputed_aseg_fpath, precomputed_brain_mask_fpath


def get_subject_from_bids_path(path):
    """Get the subject entity from a BIDS compliant path 

    Parameters
    ----------
    path : path-like
        The path to the subject directory. For example,
        ``"/Users/sealab/MRI_Processing/BABIES/newborn/derivatives/recon-all/sub-12001/aseg.nii.gz"``.

    Returns
    -------
    subject : str
        The subject BIDS entity. For example, "sub-12001".
    """
    path = Path(path).expanduser().resolve()
    parts = path.parts
    subject = [part for part in parts if part.startswith("sub-")]
    if not subject:
        raise ValueError(f"Can't infer the subject from {path}")
    subject = subject[0]
    return subject

def get_session_from_bids_path(path):
    """Get the session entity from a BIDS compliant path 

    Parameters
    ----------
    path : path-like
        The path to the subject directory. For example,
        ``"/Users/sealab/MRI_Processing/BABIES/newborn/derivatives/recon-all/sub-12001/aseg.nii.gz"``.

    Returns
    -------
    session : str
        The session BIDS entity. For example, "ses-sixmonth".
    """
    path = Path(path).expanduser().resolve()
    parts = path.parts
    session = [part for part in parts if part.startswith("ses-")]
    if not session:
        session = [
            part for part in parts
            if part == "newborn"
            or part == "sixmonth"
            or part == "six_month"
            or part == "twelvemonth"
            ]
        if len(session) > 1:
            raise ValueError(f"Multiple sessions found in {path}. Can't infer which one to use.")
        if not session:
            raise ValueError(f"Can't infer the session from {path}")
    session = session[0]
    return session

def create_filter_file(
    fpath,
    *,
    subject_id,
    session_dir,
    anat_only=False,
    bids_only=False,
    filter_dwi=True
):
    """Create a filter file for a subject.

    Parameters
    ----------
    subject_id : str
        The subject id, for example "12001".
    session_dir : str
        The session directory, for example "newborn" "six_month", or "sixmonth".
    filter_dwi : bool
        If True, the filter file will include the dwi directory. Default is True.
    anat_only : bool
        If True, the filter file will only include the anatomical datatype directories.
        functional and fmap directories will be marked for exclusion. Default is False.
    bids_only : bool
        If True, the filter file will only include the bids data, and will mark any
        derivatives sub directories (recon-all) for exclusion.
        Default is False.
    """
    filter_file = Path(fpath)
    filter_file = filter_file / f"{subject_id}_filter.txt"
    session_bids = "sixmonth" if session_dir == "six_month" else session_dir
    filter_func = "-" if anat_only else "+"
    filter_dwi = "-" if filter_dwi else "+"
    filter_derivatives = "-" if bids_only else "+"

    file_contents = [
        f"+ {session_dir}/bids/",
        f"+ {session_dir}/bids/sub-{subject_id}/",
        f"+ {session_dir}/bids/sub-{subject_id}/ses-{session_bids}/",
        f"- {session_dir}/bids/sub-{subject_id}/ses-{session_bids}/anat/*_raw.nii.gz",
        f"+ {session_dir}/bids/sub-{subject_id}/ses-{session_bids}/anat/***",
        f"{filter_func} {session_dir}/bids/sub-{subject_id}/ses-{session_bids}/func/***",
        f"{filter_dwi} {session_dir}/bids/sub-{subject_id}/ses-{session_bids}/dwi/***",
        f"{filter_dwi} {session_dir}/bids/sub-{subject_id}/ses-{session_bids}/fmap/sub-*_acq-dwi*",
        f"{filter_func} {session_dir}/bids/sub-{subject_id}/ses-{session_bids}/fmap/***",
        f"- {session_dir}/bids/sub-{subject_id}/ses-{session_bids}/**",
        f"+ {session_dir}/derivatives/",
        f"{filter_derivatives} {session_dir}/derivatives/recon-all/",
        f"{filter_derivatives} {session_dir}/derivatives/recon-all/sub-{subject_id}/***",
        f"- {session_dir}/bids/*",
        f"- {session_dir}/derivatives/**",
        f"- {session_dir}/bids_dwi/**",
        f"- {session_dir}/bids_t2only/**",
        f"- {session_dir}/code/**",
        f"- {session_dir}/tmp_dcm2bids/**",
        f"- {session_dir}/trash/**",
        f"- {session_dir}/sourcedata/**",
        f"- {session_dir}/data_share/**",
        f"- {session_dir}/Test Scan/**",
        f"- {session_dir}/.DS_Store",
        f"- {session_dir}/CABINET_Processing_IDs.xlsx",
        f"- {session_dir}/dataset_description.json",
        f"- {session_dir}/newborn_t1_t2_count.csv",
        f"- {session_dir}/subs_only_one_t1_t2_TOTAL.xlsx",
        f"- {session_dir}/vuPhyslog/**"
    ]

    with filter_file.open("w") as file:
        for line in file_contents:
            file.write(line.strip() + "\n")

    print(f"Filter file saved to: {filter_file.resolve()}")
    return filter_file


def rename_coregistered_t1w_files(anat_path):
    """Rename T1w files that were coregistered to T2w using ANTS, to match the bids standard.

    Parameters
    ----------
    anat_path : path-like
        The path to the anat directory for 1 subject. For example,
        ``"/Users/sealab/MRI_Processing/BABIES/newborn/bids/sub-12001/anat"``.

    
    Returns
    -------
    new_names : list of path-like
        A list filenames, corresponding to the newly renamed T1w files.
    
    Notes
    -----
    For example, ``sub-1011_ses-sixmonth_T1_coregistered2T2_ants_T1w.nii.gz`` will be renamed to
    ``sub-1011_ses-sixmonth_T1w.nii.gz``.

    Examples
    --------
    >>> from utils.utils import rename_coregistered_t1w_files
    >>> rename_coregistered_t1w_files(
            "/Users/scotterik/MRI_Processing/BABIES/MRI/newborn/bids/sub-1159/anat"
            )
    """
    anat_path = Path(anat_path)
    if not anat_path.exists():
        raise FileNotFoundError(f"{anat_path} does not exist")
    t1w_files = list(anat_path.glob("sub-*_T1w.nii.gz"))
    t1w_jsons = list(anat_path.glob("sub-*_T1w.json"))
    if not t1w_files:
        print(
            f"No T1w files found in {anat_path}, Thus there are no Coregistered T1w files to rename."
            " If you think this is an error, please check the directory."
            )
    new_names = []
    for t1w in t1w_files + t1w_jsons:
        new_name = t1w.name.replace("_T1_coregistered2T2_ants", "")
        if new_name == t1w.name:
            print(
                f"{t1w} already appears to be BIDS compliant, and was not coregistered to T2w."
                " I will not rename this file. If you think this is an error, please report the issue."
                )
            continue
        new_name = anat_path / new_name
        t1w.rename(new_name)
        print(f"Renamed {t1w} to {new_name}")
        new_names.append(new_name)
    return new_names
