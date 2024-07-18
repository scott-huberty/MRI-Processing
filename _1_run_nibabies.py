import argparse
from pathlib import Path

import seababies as sea

def main(**kwargs):
    # get the subject id, session id, and project name
    subject = kwargs["subject"]
    session = kwargs["session"]
    project = kwargs["project"]
    surface_recon_method = kwargs["surface_recon_method"]
    session_dir = "six_month" if session == "sixmonth" and project == "BABIES" else session
    surface_recon_method = "infantfs" if surface_recon_method == "freesurfer" else surface_recon_method
    anat_only = kwargs.get("anat_only", False)
    sea.docker.run_nibabies(subject, session_dir, project, surface_recon_method, use_dev=True, anat_only=anat_only)

def parse_args():
    # use argparse to get the subject id, session id, and project name
    parser = argparse.ArgumentParser(description='Run Nibabies.')
    parser.add_argument('project', choices=["BABIES", "ABC"], help='project name, such as BABIES')
    parser.add_argument('subject', type=str, help='subject label. such as 1103')
    parser.add_argument('session', choices=["newborn", "sixmonth"], type=str, help='session label, such as newborn')
    parser.add_argument("surface_recon_method", choices=["mcribs", "freesurfer"], help="surface reconstruction method, such as mcribs.")
    parser.add_argument("--anat_only", action="store_true", help="only process anatomical data")
    args = parser.parse_args()
    return vars(args)

def run_main():
    args = parse_args()
    main(**args)

if __name__ == "__main__":
    run_main()
