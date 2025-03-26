import argparse

from pathlib import Path
import re
import shutil

def main(log_directory, derivative_directory):
    log_directory = Path(log_directory).resolve()
    derivative_directory = Path(derivative_directory).resolve()
    assert log_directory.exists()
    assert derivative_directory.exists()
    session_map = {"sixmonth": "sixmonth", "newborn": "newborn"}
    parts = derivative_directory.parts
    session = next((session_map[p] for p in parts if p in session_map), None)

    log_files = list(Path(log_directory).glob("*.out"))
    assert log_files
    for log_file in log_files:
        text = log_file.read_text().splitlines()[0]        
        if "submit_nibabies_job.sbatch" in text:
            if "BABIES-Stanford" in text:
                if "newborn" in text:
                    subject = re.findall(r"\d{4}", text)
                    assert subject
                    subject = subject[0]
        elif "BibsNet" in text:
            if ("BABIES-Stanford" in parts and "sixmonth" in parts):
                subject = re.findall(r"\b\w{4}\b", text)
                assert len(subject) == 1
                subject = subject[0]
            else: # Newborn
                subject = re.findall(r"1\d{3}", text)[0]
            assert subject
        else:
            raise ValueError(f"Neither BIBSNet nor Nibabies was run via {text}.\n So I don't know where to copy the log file")
        assert subject
        sub_dir = derivative_directory / f"sub-{subject}" / f"ses-{session}"
        assert sub_dir.exists()
        fname = log_file.name
        shutil.copy2(log_file, sub_dir / fname)

def parse_args():
    parser = argparse.ArgumentParser(description="Move a subjects SLURM Log file to the output directory of the process that was run.")
    parser.add_argument(
        "--log_directory",
        dest="log_directory",
        required=True,
        type=str,
        help=(
            "Path to the directory containing the log files you wish to move. "
            "For example 'SLURM/log"
            )
    )

    parser.add_argument(
        "--derivative_directory",
        dest="derivative_directory",
        required=True,
        type=str,
        help=(
            "Path to the directory that contains the subject folders corresponding to the log files. "
            "For example 'BABIES-Stanford/MRI/newborn/derivatives/bibsnet'."
        ),
    )
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = parse_args()
    log_directory = args.log_directory
    derivative_directory = args.derivative_directory
    main(log_directory, derivative_directory)