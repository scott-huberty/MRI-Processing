# MRI-PROCESSING 

These scripts facilitate processing MRI files from the SEAlab BABIES and ABC studies, through the Nibabies Pipeline.

## Quick Links
- [Running BIBSnet](#Running-BIBSnet)
- [Running on WHALE](#Running-from-the-Whale-Computer)

- [Running on ACCRE](#Running-the-Pipeline-on-the-ACCRE-Cluster)

  - [submitting a SLURM job](#Submit-a-SLURM-job-to-process-these-files-with-Nibabies)

  - [Inspecting the status or success of a job](#Inspecting-the-log-files-for-a-job/Nibabies-run)

## Running BIBSnet

BIBSnet must be run on the ACCRE cluster. You must be in the `MRI-Processing/SLURM` directory, which is where the scripts to initiate the job are located. Here is an example command to run BABIES participant `sub-1011_ses-sixmonth` through BIBSnet.

```bash

sbatch submit_bibsnet_job.sbatch "BABIES" "1011" "sixmonth"
```

In this case, the output would be written to ``MRI-Processing/BABIES/MRI/six_month/sub-1011``.


> [!NOTE]
> - Make sure you have your virtual environment activated! Otherwise the script may try to call python version 2 instead of 3
## Running from the Whale Computer

- This repository is already cloned on the Whale Computer at `/Users/sealab/MRI_Processing`.

### Reset the Conda environemnt and activate this virtual environment

From the terminal, assuming you are on the WHALE computer file system:

```bash
conda deactivate
conda activate
conda activate mri_processing
which python
```

### Move to the directory for this Repository
```bash
cd ~/MRI_Processing`
```

### Run a participant

The command below will do the following:

- pull the necessary files for sub-1073_ses-newborn from the server.
- Create the precomputed files from the nifti files inside the derivatives directory.
- run Nibabies
- Push nibabies derivatives back to the server
- Delete the local files that were used

```bash
ipython -- 00_process_subjects.py --project "BABIES" --subjects "1073" --session "newborn"
```

#### Other options

The command below add the following:

- `--pdb` flag to run the script in debugging mode.
- `--surface-recon-method` argument to specify `'mcribs'`. Can also be `infantfs` which is the default.
- `--anat-only` argument to only run the anatomical workflows in nibabies.
- Notice we passed two subjects (1073 and 1366). This will repeate the pipeline for both subjects, sequentially

```bash

ipython --pdb -- 00_process_subjects.py --project "BABIES" --subjects "1073" "1366" --session "newborn" --anat-only --surface-recon-method "mcribs"
```

> [!NOTE]
> - Our scripts pull the files into the `project/MRI/session/bids`, and `project/MRI/session/derivatvies/recon-all` directories.
> - precompute files are generated locally and saved to `project/MRI/session/derivatives/precomputed`
> - Nibabies will save the derivatives files to `project/MRI/session/derivatives/Nibabies` directory, and `Nibabies/sourcedata/freesurfer/sub-xxxx` will also be copied to `project/MRI/session/derivatives/recon-all/sub-xxxx`.
> - intermittent files are saved by Nibabies to `project/MRI/session/derivatives/work/nibabies_work`

## Running the Pipeline on the ACCRE Cluster.

A few extra steps are required to process files on the ACCRE Cluster. Instead of using `00_process-subjects`, we will manually execute the following steps

### Clone this repository

> [!IMPORTANT]
> You MUST clone this repository to your home folder. If you don't the scripts WON'T work!

```bash
cd ~/
git clone https://github.com/scott-huberty/MRI-Processing.git
```

Or better yet, replace `scott-huberty` with your fork of this repository.

### Create and activate a virtual environment

I usually like to keep my python virtual environments in a dedicated folder, like below:

```bash

mkdir ~/dev
mkdir ~/dev/venvs

python -m ~/dev/venvs/my_virtual_env

source ~/dev/venvs/my_virtual_env/bin/activate

pip install ipython
```

You can replace `my_virtual_env` with any name you like (for example, `mri_processing`)


### copy the necessary files for each subject we want to process:

For example

```bash
ipython --pdb -- _0_pull_subject_files.py --project "BABIES" --subject "1462" --session "newborn" --ip-address XX.X.XXX.XXX --username "SEALAB_USERNAME"
```

- Will copy the needed files for sub-1462_ses-newborn.
- Notice that we need to provide the ip-address for the whale computer and the username for the lab account on the computer.
- I don't display the IP address or Username here, for security reasons. Please contact Scott or Yanbin for the actual values.

> [!IMPORTANT]
> - Currently, we must run this command for every subject + session combination individually.

### Submit a SLURM job to process these files with Nibabies

```bash
sbatch nibabies.sbatch BABIES 1462 newborn infantfs
```

#### Check the status of your submitted job

Below is an example. Replace `hubers2` with your ACCRE username

```bash

squeue --user hubers2
```

If you need to cancel a job that you submitted. Run command above, copy the job ID, and run

```
scancel JOBID_YOU_COPIED
```

#### Inspecting the log files for a job/Nibabies run

Check the directory `SLURM/log`. You'll see `.out` files, where the filenames are the JOB ID's. If you open one, you'll see the subject
and session listed near teh top. These files capture everything that is done during the Job. So in our case, the entire Nibabies output will be here.

Will submit a job to process sub-1462_ses-newborn using nibabies, and the infantfs anatomical workflow.

> [!IMPORTANT]
> - Currently, we must run this command for every subject + session combination individually.

### Push the processed files back to the Lab Server (via whale)

Again, we need to provide the ip-address and username for the whale computer.

```bash

ipython -- _2_push_derivatives.py --project "BABIES" --subject "1462" --session "newborn" --ip-address XX.X.XXX.XXX --username "SEALAB_USERNAME"
```

### delete local files

```bash
ipython -- _3_delete_local_directories --project "BABIES" --subject "1462" --session "newborn" --surface-recon-method "infantfs"



