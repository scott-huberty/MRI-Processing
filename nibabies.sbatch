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
if [ "$#" -lt 4 ] || [ "$#" -gt 5 ]; then
    echo "run_nibabies.sh expects 4 positional arguments, and 1 additinal argument can be added. You passed $#"
    echo "Usage: $0 <PROJECT> <PARTICIPANT_LABEL> <AGE_DESCRIPTION> <SURFACE_RECON_METHOD> <ANAT_ONLY>"
    echo "PROJECT can be: ABC, BABIES. Got $1"
    echo "PARTICIPANT_LABEL can be 1462, for example. Got $2"
    echo "AGE_DESCRIPTION can be: newborn, sixmonth, twelvemonth. Got $3"
    echo "SURFACE_RECON_METHOD must be: infantfs or mcribs. Got $4"
    echo "ANAT_Only is option and can be included by passing --anat-only. Got $5"
    exit 1
fi


# Assign command line arguments to variables
PROJECT=$1
PARTICIPANT_LABEL=$2
AGE_DESCRIPTION=$3
SURFACE_RECON_METHOD=$4
ANAT_ONLY=""
if [ "$#" -eq 5 ] && [ "$5" == "--anat-only" ]; then
    ANAT_ONLY="--anat-only"
fi

echo "Running ${SLURM_JOB_NAME}: $PROJECT sub-${PARTICIPANT_LABEL}_ses-$AGE_DESCRIPTION using $SURFACE_RECON_METHOD $ANAT_ONLY"

# Check for correct number of arguments
if [ "$#" -lt 4 ] || [ "$#" -gt 5 ]; then
    echo "run_nibabies.sh expects 4 positional arguments, and 1 additinal argument can be added. You passed $#"
    echo "Usage: $0 <PROJECT> <PARTICIPANT_LABEL> <AGE_DESCRIPTION> <SURFACE_RECON_METHOD> <ANAT_ONLY>"
    echo "PROJECT can be: ABC, BABIES. Got $1"
    echo "PARTICIPANT_LABEL can be 1462, for example. Got $2"
    echo "AGE_DESCRIPTION can be: newborn, sixmonth, twelvemonth. Got $3"
    echo "SURFACE_RECON_METHOD must be: infantfs or mcribs. Got $4"
    echo "ANAT_Only is option and can be included by passing --anat-only. Got $5"
    exit 1
fi

# Set the output file name to include participant label and age description
#SBATCH --output=nibabies_${PARTICIPANT_LABEL}_${AGE_DESCRIPTION}.txt

if [ "$#" -eq 5 ] && [ "$5" == "--anat-only" ]; then
    ./SLURM/run_nibabies.sh $PROJECT $PARTICIPANT_LABEL $AGE_DESCRIPTION $SURFACE_RECON_METHOD --anat-only
else
    ./SLURM/run_nibabies.sh $PROJECT $PARTICIPANT_LABEL $AGE_DESCRIPTION $SURFACE_RECON_METHOD
fi