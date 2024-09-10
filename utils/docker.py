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
        project,
        *,
        subject,
        session,
        surface_recon_method,
        use_precomputed=True,
        anat_only=False,
        surface_outputs=True,
        container_type="docker",
        version='latest',
        use_dev=False,
        nibabies_path=None,
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
    surface_outputs : bool, optional
        If true, output CIFTI files. Default is False.
    verbose : bool, optional
        If true, run Nibabies in Verbose mode, to print more information. Default is True.
    """
    command = build_args(
        container_type=container_type,
        project=project,
        subject=subject,
        session=session,
        surface_recon_method=surface_recon_method,
        anat_only=anat_only,
        surface_outputs=True,
        use_precomputed=use_precomputed,
        version=version,
        use_dev=use_dev,
        verbose=verbose,
        )
    run_docker_command(" ".join(command))


def build_args(
    container_type="docker",
    *,
    project,
    subject,
    session,
    surface_recon_method,
    anat_only=False,
    use_precomputed=True,
    use_dev=False,
    version="latest",
    surface_outputs=True,
    verbose=False,
    ):
    """Build the command for Docker or Singularity to run Nibabies.
    
    Parameters
    ----------
    container_type : str, optional
        The container type. Default is "docker", which uses Docker. Can also be
        "singularity" to use Singularity.
    project : str
        The project name. For example, "ABC" or "BABIES"
    subject : str
        The subject label. For example, "1027"
    session : str
        The session label. For example, "newborn" or "sixmonth"
    anat_only : bool, optional
        If true, only run the anatomical processing. Default is False.
    use_precomputed : bool, optional
        Whether to use precomputed derivatives. Default is True.
    use_dev : bool, optional
        If true, this will bind a local Nibabies repository to the Docker container. Default is False.
    version : str, optional
        The version of Nibabies to use. Default is "latest", which uses the current stable
        version of Nibabies. Can also be "unstable" to use the current development version, or
        a specific version number, such as "24.0.0rc".
    surface_recon_method : str, optional
        The surface reconstruction method. For example, "mcribs", or "freesurfer".
    surface_outputs : bool, optional
        If true, output CIFTI files. Default is False.
    verbose : bool, optional
        If true, run Nibabies in Verbose mode, to print more information. Default is False.
    """
    from .utils import get_age_in_months

    # Define paths
    root = Path(__file__).absolute().parent.parent
    bids_dir = Path(f"{root}/{project}/MRI/{session}/bids").resolve()
    derivatives_dir = Path(f"{root}/{project}/MRI/{session}/derivatives/Nibabies").resolve()
    precomputed_dir = Path(f"{root}/{project}/MRI/{session}/derivatives/precomputed").resolve()
    freesurfer_license = Path(f"{root}/utils/assets/license.txt").resolve()
    if container_type == "singularity":
        work_dir = Path("/gpfs51/dors2/l3_humphreys_lab/nibabies_work").resolve()
        image_path = Path("/gpfs51/dors2/l3_humphreys_lab/dev/images/nibabies_latest.sif").resolve()
    else:
        work_dir = Path(f"{root}/{project}/MRI/{session}/derivatives/work/nibabies_work").resolve()

    # Check if directories exist
    if not bids_dir.exists():
        raise FileNotFoundError(f"BIDS directory not found: {bids_dir}")
    if not derivatives_dir.exists():
        raise FileNotFoundError(f"Derivatives directory not found: {derivatives_dir}")
    if not work_dir.exists():
        raise FileNotFoundError(f"Work directory not found: {work_dir}")
    if not freesurfer_license.exists():
        raise FileNotFoundError(f"FreeSurfer license file not found: {freesurfer_license}")
    if container_type == "singularity" and not image_path.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")

    age_months = get_age_in_months(session)

    # define container specific arguments
    bind = "--bind" if container_type == "singularity" else "--volume"
    container = "singularity" if container_type == "singularity" else "docker"
    singularity_args = ["--cleanenv", "--no-home","--nv"]
    docker_args = ["-it"]
    # Build command
    command = [
        container,
        "run",
        # Docker/Singularity arguments
        *(singularity_args if container == "singularity" else docker_args),
        # Bind directories
        bind, f"{bids_dir}:/data:ro",
        bind, f"{derivatives_dir}:/out",
        bind, f"{work_dir}:/scratch",
        bind, f"{freesurfer_license}:/opt/freesurfer/license.txt:ro",
        ]
    if use_precomputed:
        command.extend([
            bind, f"{precomputed_dir}:/opt/derivatives/precomputed",
            ])
    if use_dev:
        raise NotImplementedError("use_dev is not yet implemented.")
    # Nibabies arguments
    if container_type == "singularity":
        command.extend([
            str(image_path),
            ])
    elif container_type == "docker":
        command.extend([
            f"nipreps/nibabies:{version}",
            ]),
    command.extend([
        "/data",
        "/out",
        "participant",
        "--age-months", str(age_months),
        "--participant-label", subject,
        "--derivatives", "/opt/derivatives/precomputed",
        "-w", "/scratch",
        "--surface-recon-method", surface_recon_method,
        ])
    if anat_only:
        command.extend([
            "--anat-only",
            ])
    elif surface_outputs:
        command.extend([
            "--cifti-output", "91k",
            ])
    if verbose:
        command.extend([
            "--verbose",
            ])
    return command

