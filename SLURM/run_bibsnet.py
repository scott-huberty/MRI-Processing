import argparse
import subprocess


def parse_args():
    parser = argparse.ArgumentParser(description='Run BiBS-Net')
    parser.add_argument(
        "--bids_path",
        type=str,
        dest="bids_path",
        help="Absolute path to the BIDS directory",
        required=True,
    )
    parser.add_argument(
        "--derivatives-fpath",
        type=str,
        dest="derivatives_path",
        help="Absolute path to the derivatives/BIBsnet directory. This is where the output of BIBSnet will be stored.",
        required=True,
    )
    parser.add_argument(
        "--participant-label",
        type=str,
        dest="participant_label",
        help="The label of the participant that should be analyzed, for example 1011 for sub-1011. The label corresponds to sub-<participant_label> from the BIDS spec (so it does not include 'sub-')",
        required=True,
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
    bids_path: str,
    *,
    derivatives_path: str,
    participant_label: str,
    image_path: str = None,
    ):
    """Run BIBSnet on a single subject.
    
    Parameters
    ----------
    bids_path : str
        Absolute path to the BIDS directory
    derivatives_path : str
        Absolute path to the derivatives/BIBsnet directory. This is where the output of BIBSnet will be stored.
    participant_label : str
        The label of the participant that should be analyzed, for example 1011 for sub-1011.
    image_path : str, optional
        Absolute path to the BIBSnet image. If ``None`` is provided (default), Then function will use the image stored on The Humphreys Lab DORS server: ``/gpfs51/dors2/l3_humphreys_lab/dev/images/bibsnet_fork.sil``.
    """
    dors_image_path = Path("/gpfs51/dors2/l3_humphreys_lab/dev/images/bibsnet_fork.sil")
    image_path = Path(image_path) if image_path is not None else dors_image_path
    if not isinstance(image_path, Path):
        raise TypeError(f"image_path must be a string or a Path object, got {type(image_path)} instead.")
    if not image_path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")
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
