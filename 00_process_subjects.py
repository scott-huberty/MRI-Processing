"""Sequentially process multiple subjects with Nibabies."""

import argparse
import subprocess
import sys
from pathlib import Path

import seababies as sea

import _0_pull_subject_files
import _1_run_nibabies
import _2_push_derivatives
import _3_delete_local_directories


def parse_args():
    """Parse the command line arguments."""
    parser = argparse.ArgumentParser(description='Process multiple subjects with Nibabies.')
    parser.add_argument(
        "-p",
        "--project",
        choices=["BABIES", "ABC"],
        required=True,
        dest='project',
        help='project name, such as BABIES'
        )
    parser.add_argument(
        "-s",
        "--subjects",
        nargs="+",
        required=True,
        dest='subjects',
        help="Space separated subject labels. such as '1103' '1027'"
        )
    parser.add_argument(
        "-S",
        "--session",
        required=True,
        choices=["newborn", "sixmonth"],
        dest='session',
        type=str,
        help="session label. such as 'newborn' or 'sixmonth'")
    parser.add_argument(
        "-m",
        "--surface-recon-method",
        choices=["mcribs", "freesurfer"],
        required=True,
        dest='surface_recon_method',
        help="surface reconstruction method, such as mcribs.")
    parser.add_argument(
        "--anat_only",
        action="store_true",
        dest="anat_only",
        help="only process anatomical data")
    parser.add_argument(
        "--nibabies-version",
        type=str,
        dest="version",
        default='latest',
        help="version of Nibabies to use. Default is 'latest'."
        )
    parser.add_argument(
        "--use_dev",
        action="store_true",
        dest="use_dev",
        help="use the development version of Nibabies"
    )
    parser.add_argument(
        "--nibabies_path",
        type=str,
        dest="nibabies_path",
        default=None,
        help="path to the local Nibabies repository. Only used if use_dev is used. If no path is provided, the default path is used."
    )
    args = parser.parse_args()
    return vars(args)

def process_one_subject(project, subject, session, surface_recon_method, anat_only=False, version="latest", use_dev=False, nibabies_path=None):
    """Process one subject. Use subprocess to run individual scripts."""
    print(f" 👇 Processing started for subject {subject} {session}👇 \n")
    # Pull down the subject files from the server
    _0_pull_subject_files.main(project=project, subject=subject, session=session, anat_only=anat_only)
    # run nibabies
    _1_run_nibabies.main(
        project=project,
        subject=subject,
        session=session,
        surface_recon_method=surface_recon_method,
        anat_only=anat_only,
        version=version,
        use_dev=use_dev,
        nibabies_path=nibabies_path,
        )
    # Push the subject Nibabies derivatives back to the server
    _2_push_derivatives.rsync_to_server(project=project, subject=subject, session=session, surface_recon_method=surface_recon_method)
    # Clean up local files
    _3_delete_local_directories.clean_up(project=project, subject=subject, session=session, surface_recon_method=surface_recon_method)
    print(f"✅ Processing completed for subject {subject}\n")


def main(**kwargs):
    """Process multiple subjects with Nibabies."""
    project = kwargs["project"]
    subjects = kwargs["subjects"]
    session = kwargs["session"]
    surface_recon_method = kwargs["surface_recon_method"]
    anat_only = kwargs.get('anat_only', False)
    version = kwargs["version"]
    use_dev = kwargs.get("use_dev", False)
    nibabies_path = kwargs.get("nibabies_path", None)
    
    assert isinstance(anat_only, bool), "anat_only must be a boolean."
    for subject in subjects:
        # sys.stdout = open(f'./sub-{subject}_ses-{session}_processing.log', 'w')
        print(f"\nProcessing")
        process_one_subject(
            project=project,
            subject=subject,
            session=session,
            surface_recon_method=surface_recon_method,
            anat_only=anat_only,
            version=version,
            use_dev=use_dev,
            nibabies_path=nibabies_path,
            )

def run_main():
    args = parse_args()
    main(**args)

if __name__ == "__main__":
    run_main()
