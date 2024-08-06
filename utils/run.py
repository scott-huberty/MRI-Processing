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
        target_directory=None,
        anat_only=False,
        dry_run=False,
        check_args=None,
        verbose="INFO"):
    """Prepare the files for a single subject to be run through Nibabies on a local machine like WHALE."""

    if check_args is None:
        check_args = {"local": True, "server": False, "mode": "error"}
    config = SubjectConfig(project, subject_id, session, get_spatial_file=False, anat_only=anat_only)
    project = config["project"]
    subject_id = config["subject_id"]
    session = config["session"]
    p_root = "." if target_directory is None else target_directory
    
    pull_subject_files(
        project,
        subject_id,
        session,
        output_dir=p_root,
        anat_only=anat_only,
        dry_run=dry_run,
        verbose=verbose,
        )

    config.get_spatial_file()
    config.check_paths(local=True, server=False, mode="error")
    rename_t1w_files(config["local_paths"]["sub_anatpath"])
    
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
        space=config["space"]
    )