"""Sequentilly process multiple subjects with Nibabies."""

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
    parser.add_argument("-p", "--project", choices=["BABIES", "ABC"], help='project name, such as BABIES')
    parser.add_argument("-s", "--subjects", nargs="+", help="Space separated subject labels. such as '1103' '1027'")
    parser.add_argument("-S", "--sessions", help="session label. such as 'newborn' 'sixmonth'")
    parser.add_argument("-m", "--surface_recon_method", choices=["mcribs", "freesurfer"], help="surface reconstruction method, such as mcribs.")
    parser.add_argument("--anat_only", action="store_true", help="only process anatomical data")
    return parser.parse_args()

def process_one_subject(project, subject, session, surface_recon_method, anat_only=False):
    """Process one subject. Use subprocess to run individual scripts."""
    print(f" 👇 Processing started for subject {subject}👇 \n")
    # Pull down the subject files from the server
    _0_pull_subject_files.main(project=project, subject=subject, session=session, anat_only=anat_only)
    # run nibabies
    _1_run_nibabies.main(project=project, subject=subject, session=session, surface_recon_method=surface_recon_method, anat_only=anat_only)
    # Push the subject Nibabies derivatives back to the server
    _2_push_derivatives.rsync_to_server(project=project, subject=subject, session=session, surface_recon_method=surface_recon_method)
    # Clean up local files
    _3_delete_local_directories.clean_up(project=project, subject=subject, session=session, surface_recon_method=surface_recon_method)
    print(f"✅ Processing completed for subject {subject}\n")


def main():
    """Process multiple subjects with Nibabies."""
    args = parse_args()
    project = args.project
    subjects = args.subjects
    session = args.sessions
    surface_recon_method = args.surface_recon_method
    anat_only = args.anat_only
    for subject in subjects:
       #sys.stdout = open(f'./sub-{subject}_ses-{session}_processing.log', 'w')
        process_one_subject(project, subject, session, surface_recon_method, anat_only=anat_only)
    
if __name__ == "__main__":
    main()
