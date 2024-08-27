"""Sequentially process multiple subjects with Nibabies."""

import argparse
import subprocess
import sys
from pathlib import Path

import _0_pull_subject_files
import _1_run_nibabies
import _2_push_derivatives
import _3_delete_local_directories


def parse_args():
    """Parse the command line arguments."""
    parser = argparse.ArgumentParser(
        description="Process multiple subjects with Nibabies."
    )
    parser.add_argument(
        "-p",
        "--project",
        choices=["BABIES", "ABC"],
        required=True,
        dest="project",
        help="project name, such as BABIES",
    )
    parser.add_argument(
        "-s",
        "--subjects",
        nargs="+",
        required=True,
        dest="subjects",
        help="Space separated subject labels. such as '1103' '1027'",
    )
    parser.add_argument(
        "-S",
        "--session",
        required=True,
        choices=["newborn", "sixmonth"],
        dest="session",
        type=str,
        help="session label. such as 'newborn' or 'sixmonth'",
    )
    parser.add_argument(
        "-m",
        "--surface-recon-method",
        choices=["mcribs", "freesurfer"],
        default="freesurfer",
        dest="surface_recon_method",
        help="surface reconstruction method. Must be 'mcribs' or 'freesurfer'.",
    )
    parser.add_argument(
        "--anat_only",
        action="store_true",
        dest="anat_only",
        help="only process anatomical data",
    )
    parser.add_argument(
        "--nibabies-version",
        type=str,
        dest="version",
        default="latest",
        help="version of Nibabies to use. Default is 'latest'.",
    )
    parser.add_argument(
        "--use_dev",
        action="store_true",
        dest="use_dev",
        help="use the development version of Nibabies",
    )
    parser.add_argument(
        "--nibabies_path",
        type=str,
        dest="nibabies_path",
        default=None,
        help="path to the local Nibabies repository. Only used if use_dev is used. If no path is provided, the default path is used.",
    )
    parser.add_argument(
        "--ip-address",
        dest="ip_address",
        help="The IP address of the Whale computer, if you running these scripts from a remote computer or server. For example, the format can be 'XX.X.XXX.XXX'.",
        default=None,
    )
    parser.add_argument(
        "--username",
        dest="username",
        help="The username to use when connecting to the Whale computer. For example, 'Lab Username'.",
        default=None,
    )
    args = parser.parse_args()
    return vars(args)


def process_one_subject(
    project,
    subject,
    session,
    surface_recon_method,
    anat_only=False,
    version="latest",
    use_dev=False,
    nibabies_path=None,
    ip_address=None,
    username=None,
):
    """Process one subject. Use subprocess to run individual scripts."""
    print(f" 👇 Processing started for subject {subject} {session}👇 \n")
    # Pull down the subject files from the server
    _0_pull_subject_files.main(
        project=project,
        subject=subject,
        session=session,
        anat_only=anat_only,
        ip_address=ip_address,
        username=username,
    )
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
    _2_push_derivatives.rsync_to_server(
        project=project,
        subject=subject,
        session=session,
        surface_recon_method=surface_recon_method,
        ip_address=ip_address,
        username=username,
    )
    # Clean up local files
    _3_delete_local_directories.clean_up(
        project=project,
        subject=subject,
        session=session,
        surface_recon_method=surface_recon_method,
    )
    print(f"✅ Processing completed for subject {subject}\n")


def main(**kwargs):
    """Process multiple subjects with Nibabies."""
    project = kwargs["project"]
    subjects = kwargs["subjects"]
    session = kwargs["session"]
    surface_recon_method = kwargs["surface_recon_method"]
    anat_only = kwargs.get("anat_only", False)
    version = kwargs["version"]
    use_dev = kwargs.get("use_dev", False)
    nibabies_path = kwargs.get("nibabies_path", None)
    ip_address = kwargs.get("ip_address", None)
    username = kwargs.get("username", None)

    assert isinstance(anat_only, bool), "anat_only must be a boolean."
    subject_success_file = Path(f"./logs/{project}_subject_success.txt")
    for subject in subjects:
        # sys.stdout = open(f'./sub-{subject}_ses-{session}_processing.log', 'w')
        print(f"\nProcessing {subject}")
        with subject_success_file.open("a") as f:
            f.write(f"\n ####{subject} #### \n")
        try:
            process_one_subject(
                project=project,
                subject=subject,
                session=session,
                surface_recon_method=surface_recon_method,
                anat_only=anat_only,
                version=version,
                use_dev=use_dev,
                nibabies_path=nibabies_path,
                ip_address=ip_address,
                username=username,
            )
        except Exception as e:
            mgs = f"❌ Error processing subject {subject}: {e}"
            print(mgs)
            with subject_success_file.open("a") as f:
                f.write(mgs)
            continue
        with subject_success_file.open("a") as f:
            f.write(f"✅ {subject} Completed \n")


def run_main():
    args = parse_args()
    main(**args)


if __name__ == "__main__":
    run_main()
