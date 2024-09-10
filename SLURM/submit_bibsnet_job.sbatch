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


python ./run_bibsnet.py