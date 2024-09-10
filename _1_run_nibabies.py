import argparse
from pathlib import Path

from utils.docker import run_nibabies


def main(
    project,
    subject,
    session,
    surface_recon_method,
    anat_only=False,
    surface_outputs=True,
    container_type="docker",
    version="latest",
    use_dev=False,
    nibabies_path=None,
):
    # get the subject id, session id, and project name

    session_dir = "six_month" if session == "sixmonth" and project == "BABIES" else session
    surface_recon_method = "infantfs" if surface_recon_method == "freesurfer" else surface_recon_method
    
    run_nibabies(
        project=project,
        subject=subject,
        session=session_dir,
        surface_recon_method=surface_recon_method,
        anat_only=anat_only,
        surface_outputs=surface_outputs,
        version=version,
        use_dev=use_dev,
        nibabies_path=nibabies_path,
        )

def parse_args():
    # use argparse to get the subject id, session id, and project name
    parser = argparse.ArgumentParser(description='Run Nibabies.')
    parser.add_argument(
        '--project',
        type=str,
        choices=["BABIES", "ABC"],
        dest='project',
        required=True,
        help='project name, such as BABIES'
        )
    parser.add_argument(
        '--subject',
        type=str,
        required=True,
        dest='subject',
        help='subject label. such as 1103'
        )
    parser.add_argument(
        '--session',
        choices=["newborn", "sixmonth"],
        required=True,
        dest='session',
        type=str,
        help='session label, such as newborn'
        )
    parser.add_argument(
        "--surface-recon-method",
        choices=["mcribs", "freesurfer"],
        required=True,
        dest="surface_recon_method",
        type=str,
        help="surface reconstruction method, such as mcribs or freesurfer."
        )
    parser.add_argument(
        "--anat-only",
        dest="anat_only",
        action="store_true",
        help="only process anatomical data"
        )
    parser.add_argument(
        "--surface-outputs",
        dest="surface_outputs",
        choices=[True, False],
        default=True,
        help="output CIFTI files"
        )
    parser.add_argument(
        "--container-type",
        dest="container_type",
        default="docker",
        help="container type, must be 'docker' or 'singularity'. Default is docker."
    )
    parser.add_argument(
        "--nibabies-version",
        type=str,
        dest="version",
        default="latest",
        help="version of Nibabies to use. Default is latest. Can also be 'unstable' to use the current development version, or a specific version number, such as '24.0.0rc'.")
    parser.add_argument(
        "--use-dev",
        action="store_true",
        dest="use_dev",
        help="use the development version of Nibabies repository."
        )
    parser.add_argument(
        "--nibabies-path",
        type=str,
        dest="nibabies_path",
        default=None,
        help="path to the local Nibabies repository. Only used if use_dev is used. If no path is provided, the default path is used."
        )
    args = parser.parse_args()
    return vars(args)

def run_main():
    args = parse_args()
    main(**args)

if __name__ == "__main__":
    run_main()
