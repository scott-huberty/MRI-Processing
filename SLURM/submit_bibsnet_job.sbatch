#!/bin/bash
#SBATCH --account=accre_guests_acc
#SBATCH --partition=turing
#SBATCH --gres=gpu:2
#SBATCH --mail-user=scott.huberty@vanderbilt.edu
#SBATCH --mail-type=ALL
#SBATCH --nodes=1
#SBATCH --ntasks=4
#SBATCH --mem=50G
#SBATCH --time=1:00:00
#SBATCH --output=./log/%j.out


# get the directory of the script
if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <project> <subject> <session>"
    echo "Project: Can be 'BABIES' or 'ABC'. Got $1."
    echo "subject: For example 1461. Got $2."
    echo "session: must be 'newborn', 'sixmonth' or 'twelvemonth'. Got $3."
    exit 1
fi

PROJECT=$1
SUBJECT=$2
SESSION=$3

echo "Running BibsNet for $PROJECT $SUBJECT $SESSION"

python ./run_bibsnet.py --project $PROJECT --subject $SUBJECT --session $SESSION