import argparse
from pathlib import Path

from utils.utils import delete_directory

def clean_up(subject, session, project, surface_recon_method):
    # get the subject id, session id, and project name
    session_subdir = "six_month" if session == "sixmonth" and project == "BABIES" else session

    bids_path = Path(f"./{project}/MRI/{session_subdir}/bids/sub-{subject}")
    assert bids_path.exists()
    derivatives_path = Path(f"./{project}/MRI/{session_subdir}/derivatives")
    assert derivatives_path.exists()
    nibabies_path = derivatives_path / "Nibabies" / f"sub-{subject}"
    assert nibabies_path.exists()

    sourcedata_path = nibabies_path.parent / "sourcedata"
    assert sourcedata_path.exists()
    
    freesurfer_path = sourcedata_path / "freesurfer" / f"sub-{subject}"
    if not freesurfer_path.exists():
        msg = f"{freesurfer_path} does not exist"
        if surface_recon_method == "mcribs":
            msg += "MCRIBS may have failed. Please check the logs."
    if surface_recon_method == "mcribs":
        mcribs_path = sourcedata_path / "mcribs" / f"sub-{subject}"
        assert mcribs_path.exists()

    precomputed_path = derivatives_path / "precomputed" / f"sub-{subject}"
    assert precomputed_path.exists()
    reconall_path = derivatives_path / "recon-all" / f"sub-{subject}"
    assert reconall_path.exists()
    work_path = derivatives_path / "work" / "nibabies_work"
    work_paths = list(work_path.glob("*/"))
    assert work_path.exists()
    assert len(work_paths)

    # Delete directories
    paths = [bids_path, nibabies_path, freesurfer_path, precomputed_path, reconall_path] + work_paths
    if surface_recon_method == "mcribs":
        paths += [mcribs_path]
    for path in paths:   
        if path.exists() and path.is_dir():
            print(f"Removing {path}")
            delete_directory(path)
        else:
            print(f"{path} does not exist or is not a directory. Skipping.")

def parse_args():
    # use argparse to get the subject id, session id, and project name
    parser = argparse.ArgumentParser(description='Clean up Nibabies directories.')
    parser.add_argument('project', choices=["BABIES", "ABC"], help='project name, such as BABIES')
    parser.add_argument('subject', type=str, help='subject label. such as 1103')
    parser.add_argument('session', choices=["newborn", "sixmonth"], type=str, help='session label, such as newborn')
    parser.add_argument("surface_recon_method", choices=["mcribs", "freesurfer"], help="surface reconstruction method, such as mcribs.")
    args = parser.parse_args()
    return vars(args)

def run_main():
    kwargs = parse_args()
    clean_up(**kwargs)

if __name__ == "__main__":
    run_main()
