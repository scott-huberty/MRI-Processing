import argparse
from pathlib import Path

from utils.utils import delete_directory

def clean_up(subject, session, project):
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
        # newer versions of nibabies append session to the filename
        freesurfer_path = freesurfer_path.parent / f"sub-{subject}_ses-{session}"
    mcribs_path = sourcedata_path / "mcribs" / f"sub-{subject}"
    if not mcribs_path.exists():
        # newer versions of nibabies append session to the filename
        mcribs_path = mcribs_path.parent / f"sub-{subject}_ses-{session}"

    precomputed_path = derivatives_path / "precomputed" / f"sub-{subject}"
    assert precomputed_path.exists()
    reconall_path = derivatives_path / "recon-all" / f"sub-{subject}"
    work_path = derivatives_path / "work" / "nibabies_work"
    work_paths = list(work_path.glob("*/"))
    # We want to keep the .gitkeep file
    work_paths = [fpath for fpath in work_fpaths if not fpath.startswith(".")]
    assert work_path.exists()
    assert len(work_paths)

    # Delete directories
    paths = [bids_path, nibabies_path, freesurfer_path, mcribs_path, precomputed_path, reconall_path] + work_paths
    for path in paths:   
        if path.exists() and path.is_dir():
            print(f"Removing {path}")
            delete_directory(path)
        else:
            print(f"{path} does not exist or is not a directory. Skipping.")

def parse_args():
    # use argparse to get the subject id, session id, and project name
    parser = argparse.ArgumentParser(description='Clean up Nibabies directories.')
    parser.add_argument(
        '--project',
        dest="project",
        type=str,
        choices=["BABIES", "ABC"],
        help='project name, such as BABIES'
        )
    parser.add_argument(
        '--subject',
        dest="subject",
        type=str,
        help='subject label. such as 1103'
        )
    parser.add_argument(
        '--session',
        dest="session",
        type=str,
        choices=["newborn", "sixmonth"],
        help='session label, such as newborn'
        )
    args = parser.parse_args()
    return vars(args)

def run_main():
    kwargs = parse_args()
    clean_up(**kwargs)

if __name__ == "__main__":
    run_main()
