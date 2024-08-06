import argparse

from utils.run import prepare_subject_files

def main(**kwargs):
    # get the subject id, session id, and project name
    subject = kwargs["subject"]
    session = kwargs["session"]
    project = kwargs["project"]
    anat_only = kwargs.get("anat_only", False)
    prepare_subject_files(project, subject, session, anat_only=anat_only)


def parse_args():
    # use argparse to get the subject id, session id, and project name
    parser = argparse.ArgumentParser(description='Pull down MRI BIDS Files for a subject.')
    parser.add_argument('project', choices=["BABIES", "ABC"], help='project name, such as BABIES')
    parser.add_argument('subject', type=str, help='subject label. such as 1103')
    parser.add_argument('session', type=str, help='session label, such as newborn')
    parser.add_argument("--dry-run", action="store_true", help="If included, the function will not copy any files, but will print the rsync command.")
    parser.add_argument("--verbose", default="INFO", choices=["QUIET", "INFO", "DEBUG"], help="The verbosity level. Default is 'INFO'.")
    parser.add_argument("--spatial-file", help="Path to the spatial file", type=str, default=None)
    args = parser.parse_args()
    return vars(args)


def run_main():
    args = parse_args()
    main(**args)

if __name__ == "__main__":
    run_main()