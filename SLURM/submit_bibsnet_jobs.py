import argparse

from pathlib import Path

import subprocess


def main(*, project, session):
	""""Batch submit BIBSNET for all subjects from a project and visit."""
	session_dir = "six_month" if (session == "sixmonth" and project == "BABIES") else session

	bids_path = Path(__file__).resolve().parent.parent / project / "MRI" / f"{session_dir}" / "bids"
	assert bids_path.exists()
	fpaths = list(bids_path.glob("sub-*"))
	assert len(fpaths)
	for fpath in fpaths:
		subject = fpath.name[4:]
		print(fpath.name)
		assert Path("./submit_bibsnet_job.sbatch").exists()
		command = [
			"sbatch",
			"./submit_bibsnet_job.sbatch",
			project,
			subject,
			session
			]
		subprocess.run(command, check=True)

def parse_args():
	parser = argparse.ArgumentParser(description="Submit BIBSnet for multiple subjects at once.")
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
		choices=["newborn", "sixmonth"],
		help="Whether to run BIBSNet for newborn or sixmonth timepoint. Must be 'newborn' or 'sixmonth'."
	)
	args = parser.parse_args()
	return args


if __name__ == "__main__":
	args = parse_args()
	project = args.project
	session = args.session
	main(
		project=project,
		session=session,
		)