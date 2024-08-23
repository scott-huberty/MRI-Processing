import argparse

from utils.run import prepare_subject_files


def main(
    subject,
    session,
    project,
    *,
    anat_only=False,
    bids_only=False,
    ip_address=None,
    username=None,
    dry_run=False,
    spatial_file=None,
    verbose=None,
    ):
    # get the subject id, session id, and project name
    prepare_subject_files(
        project,
        subject,
        session,
        anat_only=anat_only,
        bids_only=bids_only,
        ip_address=ip_address,
        username=username,
    )


def parse_args():
    # use argparse to get the subject id, session id, and project name
    parser = argparse.ArgumentParser(
        description="Pull down MRI BIDS Files for a subject."
    )
    parser.add_argument(
        "--project",
        choices=["BABIES", "ABC"],
        required=True,
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
        dest="session",
        help="session label, such as newborn",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        dest="dry_run",
        help="If included, the function will not copy any files, but will print the rsync command.",
    )
    parser.add_argument(
        "--verbose",
        default="INFO",
        choices=["QUIET", "INFO", "DEBUG"],
        help="The verbosity level. Default is 'INFO'.",
    )
    parser.add_argument(
        "--spatial-file",
        type=str,
        default=None,
        dest="spatial_file",
        help="Path to the spatial file",
    )
    parser.add_argument(
        "--anat-only",
        action="store_true",
        dest="anat_only",
        help="If included, only pull the anatomical data.",
    )
    parser.add_argument(
        "--ip-address",
        dest="ip_address",
        help="The IP address of the server, for example the format can be 'XX.X.XXX.XXX'.",
    )
    parser.add_argument(
        "--username",
        dest="username",
        help="The username to use when connecting to the Whale computer, for example 'Lab Username'.",
    )
    args = parser.parse_args()
    return vars(args)


def run_main():
    args = parse_args()
    main(**args)


if __name__ == "__main__":
    run_main()
