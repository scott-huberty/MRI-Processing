import json
import logging
import sys
from pathlib import Path
from warnings import warn

import yaml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Config(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__ = self

    def read(self, filename):
        with open(filename, "r") as file:
            data = json.load(file)
            self.update(data)

    def save(self, filename):
        """Save the dictionary to a json file."""
        filename = Path(filename)
        # make posix path serializable
        data = {k: str(v) for k, v in self.items()}
        with open(filename, "w") as file:
            json.dump(data, file, indent=4)


class SubjectConfig(Config):
    def __init__(
        self,
        project,
        subject_id,
        session,
        *,
        spatial_file=None,
        get_spatial_file=True,
        check_local_paths=False,
        anat_only=False,
        bids_only=False,
        server_is_mounted=True,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.__dict__ = self
        self["project"] = project
        self["subject_id"] = subject_id
        self["session"] = _get_session(session)
        self["base_path"] = dict(
            server=Path("/Volumes/HumphreysLab/Daily_2") / project / "MRI",
            local=(Path(__file__).parent.parent / project / "MRI"),
        )
        self["server_paths"] = dict()
        self["local_paths"] = dict()
        self["anat_only"] = anat_only
        self["bids_only"] = bids_only
        self["server_is_mounted"] = server_is_mounted
        self.populate_server_fpaths(check=server_is_mounted)
        self.populate_local_fpaths(
            get_spatial_file=get_spatial_file,
            spatial_file=spatial_file,
            check=check_local_paths,
        )

    def __repr__(self):
        """Return a string representation of the Config object."""
        return (
            f"SubjectConfig |\n"
            f"Project: {self['project']}\n"
            f"Subject: {self['subject_id']}\n"
            f"Session: {self['session']}\n"
            f"Server Path: {self['base_path']['server']}\n"
            f"Local Path: {self['base_path']['local']}\n"
        )

    def populate_paths(self, base_path, path_dict, location, check=True, mode="raise"):
        """Populate the dictionary with paths to the subject's files and directories."""
        if location == "server":
            this_dict = self["server_paths"]
        elif location == "local":
            this_dict = self["local_paths"]
        else:
            raise ValueError(f"location must be 'server' or 'local', not {location}")
        for key, relative_path in path_dict.items():
            full_path = base_path / relative_path
            this_dict[key] = full_path
        if check:
            self.check_paths(
                server=location == "server", local=location == "local", mode=mode
            )

    def check_paths(self, server=True, local=False, mode="warn"):
        """Check if the paths exist."""
        paths = []
        if server:
            paths.append(self["server_paths"])
        if local:
            paths.append(self["local_paths"])
        for path_dict in paths:
            for name, path in path_dict.items():
                try:
                    self._check_path(path, name, mode)
                except FileNotFoundError as e:
                    # Don't raise an error if the precomputed or nibabies folder is missing on the server
                    # because they won't exist until the first run of Nibabies
                    if "precomputed" in name or "nibabies" in name:
                        logger.debug(e)
                    elif name.endswith("fname"):
                        logger.debug(e)
                    elif self["anat_only"] and (
                        name.endswith("func")
                        or name.endswith("funcpath")
                        or name.endswith("fmappath")
                    ):
                        logger.debug(e)
                    elif self["bids_only"] and (
                        name.endswith("recon-all")
                        or name.endswith("precomputed")
                        or name.endswith("nibabies")
                    ):
                        logger.debug(e)
                    else:
                        if "HumphreysLab" in path.parts:
                            extra_msg = "\n MRI-Processing NOTE: If you are not on the Whale computer, pass server_is_mounted=False to the SubjectConfig constructor."
                            raise FileNotFoundError(f"{str(e)} {extra_msg}") from e
                        raise e

    def _check_path(self, path, name, mode="raise"):
        """Check if a path exists."""
        msg = f"The path for {name} does not exist: {path}"
        path = Path(path)
        if not path.exists():
            if mode == "raise":
                raise FileNotFoundError(msg)
            elif mode == "warn":
                warn(msg)
        return path.exists()

    def create_path_dict(self, location="server"):
        subject_id = self["subject_id"]
        session = self["session"]
        # SEALAB sometimes uses six_month instead of sixmonth. bids expects sixmonth
        session_dir = "six_month" if session == "sixmonth" else session
        base_path = self["base_path"][location]
        paths = {
            "project": base_path,
            "bids": f"{session_dir}/bids",
            "derivatives": f"{session_dir}/derivatives",
            "nibabies": f"{session_dir}/derivatives/Nibabies",
            "reconall": f"{session_dir}/derivatives/recon-all",
            "precomputed": f"{session_dir}/derivatives/precomputed",
            "sub_bpath": f"{session_dir}/bids/sub-{subject_id}/ses-{session}",
            "sub_anatpath": f"{session_dir}/bids/sub-{subject_id}/ses-{session}/anat",
            "sub_funcpath": f"{session_dir}/bids/sub-{subject_id}/ses-{session}/func",
            "sub_fmappath": f"{session_dir}/bids/sub-{subject_id}/ses-{session}/fmap",
            "sub_reconall": f"{session_dir}/derivatives/recon-all/sub-{subject_id}",
            "sub_precomputed": f"{session_dir}/derivatives/precomputed/sub-{subject_id}/anat",
            "sub_nibabies": f"{session_dir}/derivatives/Nibabies/sub-{subject_id}/ses-{session}",
        }
        return paths

    def populate_server_fpaths(self, check=True):
        """Populate the dictionary with paths to the subject's files and directories on the server."""
        base_path = self["base_path"]["server"]
        paths = self.create_path_dict()
        self.populate_paths(base_path, paths, "server", check=check)

    def populate_local_fpaths(
        self, get_spatial_file=True, spatial_file=None, check=False
    ):
        """Populate the dictionary with paths to the subject's files and directories on the local machine."""
        base_path = self["base_path"]["local"]
        paths = self.create_path_dict(location="local")
        self.populate_paths(base_path, paths, "local", check=check)
        if get_spatial_file:
            self.get_spatial_file(spatial_file)

    def get_spatial_file(self, spatial_file=None, space="T2w"):
        if space not in ["T1w", "T2w"]:
            raise ValueError(f"space must be 'T1w' or 'T2w', not {space}")
        subject_id = self["subject_id"]
        session = self["session"]
        if spatial_file is None:
            pattern = f"sub-{subject_id}_ses-{session}_{space}.nii.gz"
            print(
                f"Looking for:\n "
                f"    {pattern} \n"
                f"    in {self['local_paths']['sub_anatpath']}"
            )
            spatial_file = list(self["local_paths"]["sub_anatpath"].glob(pattern))
            if not spatial_file:
                pattern = f"sub-{subject_id}_ses-{session}_run-??_{space}.nii.gz"
                spatial_file = list(self["local_paths"]["sub_anatpath"].glob(pattern))
            if not spatial_file:
                files = list(self["local_paths"]["sub_anatpath"].glob("*.nii.gz"))
                raise FileNotFoundError(
                    f"No spatial file in {self['local_paths']['sub_anatpath']} matching {pattern}. Out of: \n {files}"
                )
            spatial_file = spatial_file[0]
        else:
            spatial_file = Path(spatial_file)
            if not spatial_file.exists():
                raise FileNotFoundError(f"{spatial_file} does not exist")

        self["spatial_file"] = spatial_file.resolve()
        space_ = spatial_file.name.split("_")
        if space_[2].startswith("run"):
            self["space"] = space_[3][:3]
        else:
            self["space"] = space_[2][:3]
        if self["space"] not in ["T1w", "T2w"]:
            raise ValueError(f"Invalid space: {self['space']}")

        filenames = {
            "precomputed_aseg_fname": f"sub-{subject_id}_ses-{session}_space-{self['space']}_desc-aseg_dseg.nii.gz",
            "precomputed_mask_fname": f"sub-{subject_id}_ses-{session}_space-{self['space']}_desc-brain_mask.nii.gz",
            "aseg_json_fname": f"sub-{subject_id}_ses-{session}_space-{self['space']}_desc-aseg_dseg.json",
            "mask_json_fname": f"sub-{subject_id}_ses-{session}_space-{self['space']}_desc-brain_mask.json",
            "aseg_json_fpath": self["local_paths"]["sub_precomputed"]
            / f"sub-{subject_id}_ses-{session}_space-{self['space']}_desc-aseg_dseg.json",
            "mask_json_fpath": self["local_paths"]["sub_precomputed"]
            / f"sub-{subject_id}_ses-{session}_space-{self['space']}_desc-brain_mask.json",
        }

        self["local_paths"].update(filenames)

    def read(self, file_name):
        file_name = Path(file_name)
        if not file_name.exists():
            raise FileExistsError(
                f"Configuration file {file_name.absolute()} " "does not exist"
            )

        with file_name.open("r") as file:
            self.update(yaml.safe_load(file))
            self.update(
                {
                    key: (
                        Path(value)
                        if key not in ["project", "subject_id", "session"]
                        else value
                    )
                    for key, value in self.items()
                }
            )

    def save(self, file_name):
        """Save the current config object to disk as a YAML file.

        Parameters
        ----------
        file_name : str | pathlib.Path
            The file name to save the :class:`~pylossless.Config` object to.
        """
        file_name = Path(file_name)
        config = {
            key: str(value) if isinstance(value, Path) else value
            for key, value in self.items()
        }
        with file_name.open("w") as file:
            yaml.dump(config, file, indent=4, sort_keys=True)

    def print(self):
        """Print the Config contents."""
        yaml.dump(dict(self), sys.stdout, indent=4, sort_keys=True)


def _get_session(session):
    """SEALAB sometimes uses six_month instead of sixmonth. bids expects sixmonth"""
    if session == "six_month":
        return "sixmonth"
    return session


def read_subject_config(file_name):
    """Read a subject configuration file and return a SubjectConfig object."""
    config = SubjectConfig()
    config.read(file_name)
    return config
