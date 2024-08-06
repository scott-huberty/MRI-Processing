import subprocess
from pathlib import Path

from pprint import pprint as pp


def run_docker_command(command):
    """Run a docker command."""
    print("\nRunning Docker command:\n"
          f"    {command}"
          )
    print("\n")
    subprocess.run(command, shell=True)

def run_nibabies(
        subject,
        session,
        project,
        surface_recon_method,
        root=None,
        use_precomputed=True,
        version='latest',
        use_dev=False,
        nibabies_path=None,
        freesurfer_license=None,
        anat_only=False,
        verbose=True
        ):
    """Run Nibabies on a subject.
    
    Parameters
    ----------
    subject : str
        The subject label. For example, "1027"
    session : str
        The session label. For example, "newborn" or "sixmonth"
    project : str
        The project label. For example, "ABC" or "BABIES"
    surface_recon_method : str
        The surface reconstruction method. For example, "mcribs", or "freesurfer".
    root : str, optional
        The root directory. Default is None, which uses "/Users/sealab/MRI_Processing".
    use_precomputed : bool, optional
        Whether to use precomputed derivatives. Default is True.
    version : str, optional
        The version of Nibabies to use. Default is "latest", which uses the current stable
        version of Nibabies. Can also be "unstable" to use the current development version, or
        a specific version number, such as "24.0.0rc".
    use_dev : bool, optional
        If true, this will bind a local Nibabies repository to the Docker container. Default is False.
    nibabies_path : str, optional
        The path to the local Nibabies repository. Default is None, which uses 
        "/Users/sealab/devel/repos/nibabies/nibabies". Only used if use_dev is True.
    freesurfer_license : str, optional
        The path to the FreeSurfer licence file. Default is None, which uses
        "/Applications/freesurfer/7.1.1/license.txt".
    anat_only : bool, optional
        If true, only run the anatomical processing. Default is False.
    verbose : bool, optional
        If true, run Nibabies in Verbose mode, to print more information. Default is True.
    """
    if root is None:
        root = "/Users/sealab/MRI_Processing"
    if freesurfer_license is None:
        freesurfer_license = Path("./utils/assets/license.txt").resolve()
        assert freesurfer_license.exists()

    command = [
        "docker", "run",
        "-it",
        "-v", f"{root}/{project}/MRI/{session}/bids:/data:ro",
        "-v", f"{root}/{project}/MRI/{session}/derivatives/Nibabies:/out",
        "-v", f"{root}/{project}/MRI/{session}/derivatives/work/nibabies_work:/scratch",
        "-v", f"{freesurfer_license}:/opt/freesurfer/license.txt:ro",
        ]
    if use_precomputed:
        command.extend([
            "-v", f"{root}/{project}/MRI/{session}/derivatives/precomputed:/opt/derivatives/precomputed",
            ])
    if use_dev:
        assert 1 == 0
        if nibabies_path is None:
            nibabies_path = "/Users/sealab/devel/repos/nibabies/nibabies"
        command.extend([
            "-v", f"{nibabies_path}:/opt/conda/envs/nibabies/lib/python3.10/site-packages/nibabies:ro",
            ])
    command.extend([
        f"nipreps/nibabies:{version}",
        "/data",
        "/out",
        "participant",
        "--age-months", "1" if session == "newborn" else "6",
        "--participant-label", subject,
        "--derivatives", "/opt/derivatives/precomputed",
        "-w", "/scratch",
        "--surface-recon-method", surface_recon_method,
        ])
    if not anat_only:
        command.extend([
            "--cifti-output", "91k",
            ])
    else:
        command.extend([
            "--anat-only",
            ])
    if verbose:
        command.extend([
            "--verbose",
            ])
    run_docker_command(" ".join(command))
