import argparse
from pathlib import Path

from utils.config import SubjectConfig
from utils.utils import do_rsync


def rsync_to_server(**kwargs):
    # get the subject id, session id, and project name
    subject = kwargs["subject"]
    session = kwargs["session"]
    project = kwargs["project"]
    anat_only = kwargs.get("anat_only", False)
    surface_recon_method = kwargs["surface_recon_method"]
    ip_address = kwargs.get("ip_address", None)
    username = kwargs.get("username", None)

    session_subdir = ("six_month" if session == "sixmonth" and project == "BABIES" else session)  # fmt:skip
    server_is_mounted = ip_address is None

    # create a subject config object with the paths to their files populated
    config = SubjectConfig(
        project,
        subject,
        session,
        anat_only=anat_only,
        server_is_mounted=server_is_mounted,
    )
    config.check_paths(local=True, server=False, mode="error")

    derivatives_path = config.local_paths["derivatives"]
    assert derivatives_path.exists()
    assert (derivatives_path == Path(f"./{project}/MRI/{session_subdir}/derivatives").resolve())  # fmt:skip

    nibabies_path = config.local_paths["nibabies"] / f"sub-{subject}"
    assert nibabies_path.exists()
    assert nibabies_path == (derivatives_path / "Nibabies" / f"sub-{subject}").resolve()
    server_nibabies = config.server_paths["nibabies"]

    sourcedata_path = (config.local_paths["nibabies"] / "sourcedata" / f"{surface_recon_method}" / f"sub-{subject}")  # fmt:skip
    assert sourcedata_path.exists()
    assert (sourcedata_path == derivatives_path / "Nibabies" / "sourcedata" / f"{surface_recon_method}" / f"sub-{subject}")  # fmt:skip
    server_sourcedata = server_nibabies / "sourcedata"  # / f"{surface_recon_method}"

    html_path = derivatives_path / "Nibabies" / f"sub-{subject}_ses-{session}.html"
    server_html = server_nibabies

    precomputed_path = config.local_paths["precomputed"] / f"sub-{subject}"
    assert precomputed_path.exists()
    assert (precomputed_path == (derivatives_path / "precomputed" / f"sub-{subject}").resolve())  # fmt:skip
    server_precomputed = config.server_paths["precomputed"]

    freesurfer_path = (nibabies_path.parent / "sourcedata" / "freesurfer" / f"sub-{subject}")  # fmt:skip
    server_freesurfer = server_nibabies / "sourcedata" / "freesurfer"
    if not freesurfer_path.exists():
        msg = f"{freesurfer_path} does not exist."
        if surface_recon_method == "mcribs":
            msg += "MCRIBS may have failed. Please check the logs."
        raise FileNotFoundError(msg)
    if surface_recon_method == "mcribs":
        mcribs_path = nibabies_path.parent / "sourcedata" / "mcribs" / f"sub-{subject}"
        server_mcribs = server_sourcedata / "mcribs"
        assert mcribs_path.exists()
        assert server_mcribs.exists(), f"{server_mcribs} directory does not exist."

    server_reconall = config.server_paths["reconall"]
    if server_is_mounted:
        assert server_reconall.exists()

    paths = [
        nibabies_path,
        freesurfer_path,
        html_path,
        precomputed_path,
        freesurfer_path,
    ]
    server_paths = [
        server_nibabies,
        server_freesurfer,
        server_html,
        server_precomputed,
        server_reconall,
    ]
    if surface_recon_method == "mcribs":
        paths.append(mcribs_path)
        server_paths.append(server_mcribs)
    for path, server_path in zip(paths, server_paths):
        if path.exists():
            print(f"Pushing {path} to {server_path}")
            do_rsync(path, server_path, flags="-rltv")
        else:
            print(f"{path} does not exist. Skipping.")


def parse_args():
    # use argparse to get the subject id, session id, and project name
    parser = argparse.ArgumentParser(description="Push Nibabies output to server.")
    parser.add_argument(
        "--project",
        type=str,
        required=True,
        choices=["BABIES", "ABC"],
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
        choices=["newborn", "sixmonth"],
        dest="session",
        help="session label, such as newborn",
    )
    parser.add_argument(
        "--surface-recon-method",
        type=str,
        required=True,
        choices=["mcribs", "freesurfer"],
        dest="surface_recon_method",
        help="surface reconstruction method, such as mcribs.",
    )
    parser.add_argument(
        "--anat_only",
        action="store_true",
        dest="anat_only",
        help="Only push the anatomical data.",
    )
    parser.add_argument(
        "--ip-address",
        default=None,
        dest="ip_address",
        help="The IP address of the Whale computer, if you are running this command from a remote computer.",
    )
    parser.add_argument(
        "--username",
        default=None,
        dest="username",
        help="The username to use when connecting to the Whale computer, such as 'Lab Username'.",
    )
    args = parser.parse_args()
    return vars(args)


def run_main():
    kwargs = parse_args()
    rsync_to_server(**kwargs)


if __name__ == "__main__":
    run_main()
