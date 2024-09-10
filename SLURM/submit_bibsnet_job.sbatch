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

# get the directory of the script
if ["$#" -ne 3]; then
    echo "Usage: $0 <project> <subject> <session>"
    echo "Project: Can be "BABIES" or "ABC". Got $0."
    echo "subject: For example 1461. Got $1."
    echo "session: must be 'newborn', 'sixmonth' or 'twelvemonth'. Got $2."

python ./run_bibsnet.py $1 $2 $3