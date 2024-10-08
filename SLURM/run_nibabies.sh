#!/bin/bash

# Function to convert from descriptive age arg to months for Nibabies
get_age_in_months() {
    case "$1" in
        "newborn")
            echo "1"
            ;;
        "sixmonth")
            echo "6"
            ;;
        "twelvemonth")
            echo "12"
            ;;
        *)
            echo "Invalid age description. Must be newborn, sixmonth or twelvemonth. got $1"
            exit 1
            ;;
    esac
}

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

# Define the image and options
IMAGE="docker://nipreps/nibabies:23.1.0"
PROJECT=$1
PARTICIPANT_LABEL=$2
AGE_DESCRIPTION=$3
SURFACE_RECON_METHOD=$4

# Convert age description to months
AGE_MONTHS=$(get_age_in_months $AGE_DESCRIPTION)

# Check if --anat-only flag is passed
ANAT_ONLY_FLAG=""
if [ "$#" -eq 5 ] && [ "$5" == "--anat-only" ]; then
    ANAT_ONLY_FLAG="--anat-only"
fi


# Validate project
if [[ "$PROJECT" != "ABC" && "$PROJECT" != "BABIES" ]]; then
    echo "Error: PROJECT must be either 'ABC' or 'BABIES' but got $PROJECT"
    exit 1
fi

# Validate surface-recon-method
if [[ "$SURFACE_RECON_METHOD" != "mcribs" && "$SURFACE_RECON_METHOD" != "infantfs" ]]; then
    echo "Error: SURFACE_RECON_METHOD must be either 'mcribs' or 'infantfs' but got $SURFACE_RECON_METHOD"
    exit 1
fi

# Set paths based on project
ROOT_DIR="$HOME/MRI_Processing"
PROJECT_DIR="$ROOT_DIR/$PROJECT/MRI"
SESSION_DIR="$PROJECT_DIR/$AGE_DESCRIPTION"
BIDS_DIR="$SESSION_DIR/bids"
DERIVATIVES_DIR="$SESSION_DIR/derivatives"
OUT_DIR="$DERIVATIVES_DIR/Nibabies"
SCRATCH_DIR="$DERIVATIVES_DIR/work/nibabies_work"
PRECOMPUTED_DIR="$DERIVATIVES_DIR/precomputed"
LICENSE_FILE="$ROOT_DIR/utils/assets/license.txt"

echo "Passing these parameters to singularity"
echo "---------------------------------------"
echo " BIDS: $BIDS_DIR"
echo " OUT: $OUT_DIR"
echo " SCRATCH: $SCRATCH_DIR"
echo " LICENSE: $LICENSE_FILE"
echo " PRECOMPUTED ASEG: $PRECOMPUTED_DIR"
echo " AGE MONTHS: $AGE_MONTHS"
echo " PARTICIPANT: $PARTICIPANT_LABEL"
echo " METHOD: $SURFACE_RECON_METHOD"
echo " ANAT_ONLY: $ANAT_ONLY_FLAG"
echo " IMAGE: $IMAGE"
echo "----------------------------------------"
# XXX: add arguments for anat_only, CIFTI output?
# Execute the Singularity command
singularity run -e \
  -B ${BIDS_DIR}:/data:ro \
  -B ${OUT_DIR}:/out \
  -B ${SCRATCH_DIR}:/scratch \
  -B ${LICENSE_FILE}:/opt/freesurfer/license.txt:ro \
  -B ${PRECOMPUTED_DIR}:/opt/derivatives/precomputed \
  ${IMAGE} \
  /data /out participant \
  --age-months ${AGE_MONTHS} \
  --participant-label ${PARTICIPANT_LABEL} \
  --derivatives /opt/derivatives/precomputed \
  -w /scratch \
  --surface-recon-method ${SURFACE_RECON_METHOD} \
  --cifti-output 91k \
  --verbose ${ANAT_ONLY_FLAG}