from .config import SubjectConfig
from .utils import (
    create_filter_file,
    create_precomputed_files,
    create_precomputed_jsons,
    pull_subject_files,
    rename_t1w_files,
)


def prepare_subject_files(
    project,
    subject_id,
    session,
    *,
    anat_only=False,
    bids_only=False,
    ip_address=None,
    username=None,
    dry_run=False,
    check_args=None,
    mri_processing_dir=None,
    verbose="INFO",
):
    """Prepare the files for a single subject to be run through Nibabies.

    Parameters
    ----------
    project : str
        The project label. For example, "ABC" or "BABIES".
    subject_id : str
        The subject label. For example, "1027".
    session : str
        The session label. For example, "newborn" or "sixmonth".
    mri_processing_dir : str, optional
        The path to the MRI-Processing directory that contains these scripts. Default
        is None, which assumes that the current directory is the MRI-Processing
        directory. If not None, this should be the path to the MRI-Processing directory.
    anat_only : bool, optional
        If true, only pull files for the anatomical data. Default is False.
    bids_only : bool, optional
        If true, only pull files for the BIDS data. Default is False.
    dry_run : bool, optional
        If true, do not actually run the rsync commands, i.e. do not actually pull the
        data files, just print them. Default is False.
    check_args : dict, optional
        The arguments to use when checking the paths. Default is None, which uses
        {"local": True, "server": False, "mode": "error"}, which will check the local
        paths and raise an error if they do not exist.
    ip_address : str, optional
        The IP address of the server, for example the format can be "XX.X.XXX.XXX".
        Default is None, which does not use an IP address and assumes that you are on
        the Whale computer. If not None, you must also provide a username.
    username : str, optional
        The username to use when connecting to the Whale computer, for example "Lab Username".
        The username must be an actual account on the Whale computer. Default is None,
        does nothing if the IP address is None, but raises an error if the IP address
        is not None.
    """
    server_is_mounted = ip_address is None

    if check_args is None:
        check_args = {"local": True, "server": False, "mode": "error"}
    config = SubjectConfig(
        project,
        subject_id,
        session,
        get_spatial_file=False,
        anat_only=anat_only,
        bids_only=bids_only,
        server_is_mounted=server_is_mounted,
    )
    project = config["project"]
    subject_id = config["subject_id"]
    session = config["session"]
    p_root = "." if mri_processing_dir is None else mri_processing_dir

    pull_subject_files(
        project,
        subject_id,
        session,
        output_dir=p_root,
        anat_only=anat_only,
        bids_only=bids_only,
        dry_run=dry_run,
        ip_address=ip_address,
        username=username,
        verbose=verbose,
    )

    config.get_spatial_file()
    config.check_paths(local=True, server=False, mode="error")
    rename_t1w_files(config["local_paths"]["sub_anatpath"])

    if bids_only:
        return

    create_precomputed_files(
        reconall_dir=config["local_paths"]["reconall"],
        output_dir=config["local_paths"]["precomputed"],
        subject=config["subject_id"],
        session=config["session"],
        space=config["space"],
        overwrite=True,
    )

    create_precomputed_jsons(
        precomputed_dir=config["local_paths"]["precomputed"],
        spatial_reference_fname=config["spatial_file"],
        subject=config["subject_id"],
        session=config["session"],
        space=config["space"],
    )
