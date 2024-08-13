#!/bin/bash
#SBATCH --mail-user=scott.huberty@vanderbilt.edu
#SBATCH --mail-type=ALL
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=20G
#SBATCH --time=8:00:00
#SBATCH --output=./SLURM/log/%j.out

# Check for correct number of arguments
if [ "$#" -ne 4 ]; then
    echo "Nibabies sbatch expects 4 arguments but you passed $#"
    echo "Usage: $0 <PROJECT> <PARTICIPANT_LABEL> <AGE_DESCRIPTION> <SURFACE_RECON_METHOD>"
    echo "PROJECT can be: ABC, BABIES. Got $1"
    echo "PARTICIPANT_LABEL can be 1462, for example. Got $2"
    echo "AGE_DESCRIPTION can be: newborn, sixmonth, twelvemonth. Got $3"
    echo "SURFACE_RECON_METHOD must be: mcribs, infantfs. Got $4"
    exit 1
fi

# Assign command line arguments to variables
PROJECT=$1
PARTICIPANT_LABEL=$2
AGE_DESCRIPTION=$3
SURFACE_RECON_METHOD=$4

echo "Running ${SLURM_JOB_NAME}: $PROJECT sub-${PARTICIPANT_LABEL}_ses-$AGE_DESCRIPTION using $SURFACE_RECON_METHOD"

# Set the output file name to include participant label and age description
#SBATCH --output=nibabies_${PARTICIPANT_LABEL}_${AGE_DESCRIPTION}.txt

./SLURM/run_nibabies.sh $PROJECT $PARTICIPANT_LABEL $AGE_DESCRIPTION $SURFACE_RECON_METHOD