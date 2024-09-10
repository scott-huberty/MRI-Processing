import argparse
import subprocess
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description='Run BiBS-Net')
    parser.add_argument(
        "--project",
        type=str,
        dest="project",
        choices=["BABIES", "ABC"],
        help="Project name. Must be one 'BABIES', or 'ABC'",
        required=True,
    )
    parser.add_argument(
        "--subject",
        type=str,
        dest="subject",
        help="The label of the participant that should be analyzed, for example 1011 for sub-1011. The label corresponds to sub-<participant_label> from the BIDS spec (so it does not include 'sub-')",
        required=True,
    )
    parser.add_argument(
        "--session",
        type=str,
        dest="session",
        required=True,
        choices=["newborn", "sixmonth", "twelvemonth"],
        help="Must be 'newborn', 'sixmonth', or 'twelvemonth'."
    )
    parser.add_argument(
        "--image_path",
        type=str,
        dest="image_path",
        default=None,
        help="Absolute path to the BIBSnet image. If ``None`` is provided (default), Then function will use the image stored on The Humphreys Lab DORS server: ``/gpfs51/dors2/l3_humphreys_lab/dev/images/bibsnet_fork.sil``.",
    )
    args = parser.parse_args()
    return vars(args)


def main(
    project: str,
    *,
    subject: str,
    session: str,
    image_path: str = None,
    ):
    """Run BIBSnet on a single subject.
    
    Parameters
    ----------
    project : str
        Project name. Must be one 'BABIES', or 'ABC'.
    subject : str
        The label of the participant that should be analyzed, for example 1011 for sub-1011.
    session : str
        The session of the participant that should be analyzed, for example 'newborn', 'sixmonth', or 'twelvemonth'.
    image_path : str, optional
        Absolute path to the BIBSnet image. If ``None`` is provided (default), Then function will use the image stored on The Humphreys Lab DORS server: ``/gpfs51/dors2/l3_humphreys_lab/dev/images/bibsnet_fork.sil``.
    """
    dors_image_path = Path("/gpfs51/dors2/l3_humphreys_lab/dev/images/bibsnet_fork.sil")
    image_path = Path(image_path) if image_path is not None else dors_image_path
    if not isinstance(image_path, Path):
        raise TypeError(f"image_path must be a string or a Path object, got {type(image_path)} instead.")
    if not image_path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")

    # Define paths
    session_dir = "six_month" if (session == "sixmonth" and project == "BABIES") else session
    pwd = Path(__file__).parent
    bids_path = pwd.parent / project / session_dir / "bids"
    derivatives_path = pwd.parent / project / session_dir / "derivatives"
    if not bids_path.exists():
        raise FileNotFoundError(f"BIDS directory not found: {bids_path}")
    if not derivatives_path.exists():
        raise FileNotFoundError(f"Derivatives directory not found: {derivatives_path}")
    # Run BIBSnet
    subprocess.call(
        [
        "singularity",
        "run",
        "--cleanenv",
        "--no-home",
        "--nv",
        "--bind",
        f"{bids_path}:/input",
        "--bind",
        f"{derivatives_path}:/output",
        image_path,
        "/input",
        "/output",
        participant_label,
        ]
    )

if __name__ == "__main__":
    args = parse_args()
    main(**args)
