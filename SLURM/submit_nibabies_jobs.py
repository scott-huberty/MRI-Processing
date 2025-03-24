import argparse

from pathlib import Path

import subprocess


def main(
    *,
    project,
    session,
    surface_recon_method="mcribs",
    anat_only=False,
    ):
    """"Batch submit Nibabies for all subjects from a project and visit."""
    session_dir = "six_month" if (session == "sixmonth" and project == "BABIES") else session
    bids_path = Path(__file__).resolve().parent.parent / project / "MRI" / f"{session_dir}" / "bids"
    assert bids_path.exists()
    fpaths = list(bids_path.glob("sub-*"))
    assert len(fpaths)
    for fpath in fpaths:
        subject = fpath.name[4:]
        if anat_only == False:
            if not has_func(fpath, session):
                    anat_only_mode = True
            else:
                anat_only_mode = False
        else:
            anat_only_mode = anat_only
        print(f"Submitting Nibabies job for {fpath.name}. anat-only: {anat_only_mode}")
        assert Path("./submit_nibabies_job.sbatch").exists()
        command = [
			"sbatch",
			"./submit_nibabies_job.sbatch",
			project,
			subject,
			session,
            surface_recon_method,
			]
        if anat_only_mode:
            command.append("--anat-only")
        subprocess.run(command, check=True)


def has_func(sub_dir, session):
    if not (sub_dir / f"ses-{session}" / "func").exists():
        return False
    return True


def parse_args():
    parser = argparse.ArgumentParser(description="Submit Nibabies for multiple subjects at once.")
    parser.add_argument(
		"--project",
		required=True,
		dest="project",
		choices=["BABIES", "ABC", "BABIES-Stanford"],
		help="Which project the subject you want to run is from. Must be 'BABIES', 'ABC', or 'BABIES-stanford'"
	)
    parser.add_argument(
		"--session",
		required=True,
		dest="session",
		choices=["newborn", "sixmonth", "twelvemonth"],
		help="Whether to run Nibabies for newborn, sixmonth or twelvemonth timepoint. Must be 'newborn', 'sixmonth', or 'twelvemonth'."
	)
    parser.add_argument(
        "--surface_recon_method",
        dest="surface_recon_method",
        default="mcribs",
        type=str,
        choices=["infantfs", "mcribs"],
        help="Which method Nibabies should use for cortical surface reconstructins. must be: 'infantfs' or 'mcribs'",
    )
    parser.add_argument(
        "--anat_only",
        dest="anat_only",
        action="store_true",
        help="Only Process Anatomical data for this subject."
    )
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = parse_args()
    project = args.project
    session = args.session
    surface_recon_method = args.surface_recon_method
    anat_only = args.anat_only
    main(
		project=project,
		session=session,
        surface_recon_method=surface_recon_method,
        anat_only=anat_only
		)