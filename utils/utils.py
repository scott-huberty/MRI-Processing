import shutil
import subprocess
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


def pull_subject_files(
    project,
    subject_id,
    session,
    output_dir,
    *,
    dry_run=False,
    anat_only=False,
    pull_dwi=False,
    ip_address=None,
    username=None,
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
        output_dir, subject_id, session, anat_only=anat_only, filter_dwi=filter_dwi
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
    server_is_mounted=True,
    verbose="INFO",
):
    """Use rsync to copy files from one directory to another."""
    if server_is_mounted:
        assert Path(input_dir).exists(), f"{input_dir} does not exist"
    assert output_dir.exists(), f"{output_dir} does not exist"
    flags = flags
    if verbose == "INFO":
        flags += "v"
    elif verbose == "DEBUG":
        flags += "vv"
    if dry_run:
        flags += "n"

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
    subprocess.run(command)


def delete_directory(path):
    """Remove a path and all its contents."""
    if not path.exists():
        raise FileNotFoundError(f"{path} does not exist")
    shutil.rmtree(path)


def create_precomputed_jsons(
    precomputed_dir, spatial_reference_fname, subject, session, space="T2w"
):
    """Create json files for aseg and brain_mask.

    Parameters
    ----------
    precomputed_dir : path-like
        The path to the precomputed directory. Do not include the subject or session.
        For example, ``"/Users/sealab/MRI_Processing/BABIES/derivatives/precomputed"``.
    spatial_reference_fname : path-like
        The path to the spatial reference file, in the ``anat`` folder in the ``bids`` directory.
        For example:
        ``"/Users/sealab/MRI_Processing/BABIES/bids/subject/session/anat/sub-1401_ses-newborn_T1_coregistered2T2_ants_T1w.nii.gz"``.
    """
    aseg_json_fname = f"sub-{subject}_ses-{session}_space-{space}_desc-aseg_dseg.json"
    mask_json_fname = f"sub-{subject}_ses-{session}_space-{space}_desc-brain_mask.json"
    precomputed_dir = precomputed_dir / f"sub-{subject}"
    aseg_json_fpath = precomputed_dir / "anat" / aseg_json_fname
    mask_json_fpath = precomputed_dir / "anat" / mask_json_fname
    bids_index = Path(spatial_reference_fname).parts.index("bids")
    bpath = Path(*spatial_reference_fname.parts[: bids_index + 1])
    spatial_reference_fname = spatial_reference_fname.relative_to(bpath)
    # add the Spatial key to the jsons
    aseg_json = Config()
    aseg_json["SpatialReference"] = spatial_reference_fname
    aseg_json.save(aseg_json_fpath)
    mask_json = Config()
    mask_json["SpatialReference"] = spatial_reference_fname
    mask_json.save(mask_json_fpath)


def create_precomputed_files(
    reconall_dir, output_dir, subject, session, space="T2w", overwrite=False
):
    """copy recon-all files to precomputed directory and rename them.

    Parameters
    ----------
    reconall_dir : path-like
        The path to the local recon-all directory. Do not include the subject. For example,
        ``"/users/selab/MRI_Processing/BABIES/derivatives/recon-all"``.
        This can be a relative or absolute path.
    output_dir : path-like
        The path to the precomputed directory. Do not include the subject or session.
        For example, ``"/Users/sealab/MRI_Processing/BABIES/derivatives/precomputed"``.
    subject : str
        The subject id, for example "12001".
    session : str
        The session. Must be either ``"newborn"`` or ``"six_month"``. Default is ``"newborn"``.
    space : str
        The space of the aseg and brain_mask files. Must be ``"T1w"`` or ``"T2w"``.
        Default is "T1w".
    overwrite : bool
        If True, the function will overwrite the files in the precomputed directory (if a file
        with the same name already exists). If False, the function will raise an error if a file
        with the same name already exists. Default is False.

    Notes
    -----
    This function will look for a file named ``aseg.nii.gz`` and ``brain_mask.nii.gz`` in the
    recon-all directory. It will copy these files to the precomputed directory and rename them
    to the following format: ``{subject}_ses-{session}_space-{space}_desc-aseg_dseg.nii.gz``
    and ``{subject}_ses-{session}_space-{space}_desc-brain_mask.nii.gz``.
    """

    # Checks
    if not Path(reconall_dir).exists():
        raise FileNotFoundError(f"{reconall_dir} does not exist")
    if not Path(output_dir).exists():
        raise FileNotFoundError(f"{output_dir} does not exist")
    if space not in ["T1w", "T2w"]:
        raise ValueError(f"space must be either 'T1w' or 'T2w', but got: {space}")
    if not subject.isnumeric():
        raise ValueError(f"subject must be a number, but got: {subject}")
    if session not in ["newborn", "sixmonth"]:
        raise ValueError(
            f"session must be either 'newborn' or 'six_month', but got: {session}"
        )

    output_dir = Path(output_dir).resolve()
    recon_sub_dir = reconall_dir / f"sub-{subject}"
    aseg_fpath = recon_sub_dir / "aseg.nii.gz"
    assert aseg_fpath.exists(), f"{aseg_fpath} does not exist"
    brain_mask_fpath = recon_sub_dir / "brain_mask.nii.gz"
    assert brain_mask_fpath.exists(), f"{brain_mask_fpath} does not exist"
    precomputed_aseg_fname = (
        f"sub-{subject}_ses-{session}_space-{space}_desc-aseg_dseg.nii.gz"
    )
    precomputed_mask_fname = (
        f"sub-{subject}_ses-{session}_space-{space}_desc-brain_mask.nii.gz"
    )
    if not (output_dir / f"sub-{subject}").exists():
        (output_dir / f"sub-{subject}").mkdir()
        (output_dir / f"sub-{subject}" / "anat").mkdir()
    precomputed_aseg_fpath = (
        output_dir / f"sub-{subject}" / "anat" / precomputed_aseg_fname
    )
    precomputed_mask_fpath = (
        output_dir / f"sub-{subject}" / "anat" / precomputed_mask_fname
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

    if precomputed_mask_fpath.exists():
        if not overwrite:
            raise FileExistsError(
                f"{precomputed_mask_fpath} already exists. Set overwrite=True "
                " to overwrite."
            )
        else:
            warn(f"{precomputed_mask_fpath} already exists. Overwriting.")
            precomputed_mask_fpath.unlink()
    print(f"Copying {aseg_fpath} to {precomputed_aseg_fpath}\n")
    shutil.copy(aseg_fpath, precomputed_aseg_fpath)
    print(f"Copying {brain_mask_fpath} to {precomputed_mask_fpath}\n")
    shutil.copy(brain_mask_fpath, precomputed_mask_fpath)


def create_filter_file(
    fpath, subject_id, session_dir, anat_only=False, filter_dwi=True
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
    """
    filter_file = Path(fpath)
    filter_file = filter_file / f"{subject_id}_filter.txt"
    session_bids = "sixmonth" if session_dir == "six_month" else session_dir
    filter_func = "-" if anat_only else "+"
    filter_dwi = "-" if filter_dwi else "+"
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
        f"+ {session_dir}/derivatives/recon-all/",
        f"+ {session_dir}/derivatives/recon-all/sub-{subject_id}/***",
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
    ]

    with filter_file.open("w") as file:
        for line in file_contents:
            file.write(line.strip() + "\n")

    print(f"Filter file saved to: {filter_file.resolve()}")
    return filter_file


def rename_t1w_files(anat_path):
    """Rename T1w files to match the bids standard.

    Notes
    -----
    For example, ``sub-1011_ses-sixmonth_T1_coregistered2T2_ants_T1w.nii.gz`` will be renamed to
    ``sub-1011_ses-sixmonth_T1w.nii.gz``.
    """
    anat_path = Path(anat_path)
    if not anat_path.exists():
        raise FileNotFoundError(f"{anat_path} does not exist")
    t1w_files = list(anat_path.glob("sub-*_T1w.nii.gz"))
    t1w_jsons = list(anat_path.glob("sub-*_T1w.json"))
    new_names = []
    for t1w in t1w_files + t1w_jsons:
        new_name = t1w.name.replace("_T1_coregistered2T2_ants", "")
        new_name = anat_path / new_name
        t1w.rename(new_name)
        print(f"Renamed {t1w} to {new_name}")
        new_names.append(new_name)
    return new_names
