from __future__ import annotations

import os
import time
from dataclasses import dataclass, fields
from datetime import datetime
from logging import INFO
from typing import Any, List, Optional, Union

from .auth import Credentials, HTTPOAuth2, OAuthToken
from .config import URLs
from .exceptions import JobFailed
from .http import get, post
from .logging import logger, setup_logger
from .utils import Singleton


def transform_data(input_dict, mapping):
    """Remaps the dictionary keys according to the mapping."""
    return {mapping.get(k, k): v for k, v in input_dict.items()}


def filter_dict_for_dataclass(data_class, input_dict):
    """Discards dictionary keys that don't match with any dataclass field."""
    data_class_fields = {f.name for f in fields(data_class)}
    return {k: v for k, v in input_dict.items() if k in data_class_fields}


class API(metaclass=Singleton):
    """Models the Serverless Functions API endpoints.

    Attributes:
        urls: The :class:`eocanvas.config.URLs` object that maps all the API endpoints
        token: The authentication :class:`eocanvas.auth.OAuthToken` object
    """

    def __init__(
        self,
        urls: Optional[URLs] = None,
        token: Optional[OAuthToken] = None,
        log_level: int = INFO,
    ):
        """"""
        setup_logger(log_level)

        if urls is None:
            urls = URLs()

        if token is None:
            token = OAuthToken(url=urls.token_url, credentials=Credentials.load())

        self.urls = urls
        self.auth = HTTPOAuth2(token)

    def get_process(self, process_id: str) -> Process:
        """Gets the details of a process.

        Returns:
            A :class:`eocanvas.api.Process` instance.
        """
        url = self.urls.get("process_detail", process_id=process_id)
        response = get(url, auth=self.auth)
        return self._build_process(response.json())

    def get_processes(self) -> List[Process]:
        """Gets the list of available processes.
        There should be only Snap and Datatailor functions.

        Returns:
            A list of :class:`eocanvas.api.Process` instances.
        """
        url = self.urls.get("process_list")
        response = get(url, auth=self.auth)
        return [self._build_process(data) for data in response.json()]

    def exec_process(self, process: Process) -> Job:
        """Submits a process to the API.

        Returns:
            A :class:`eocanvas.api.Job` instance.
        """
        inputs = process.prepare_inputs()
        url = self.urls.get("process_execution", process_id=process.process_id)
        response = post(url, json=inputs, auth=self.auth)
        return self._build_job(response.json())

    def get_job(self, job_id) -> Job:
        """Gets the details of a job.

        Returns:
            A :class:`eocanvas.api.Job` instance.
        """
        url = self.urls.get("job_detail", job_id=job_id)
        response = get(url, auth=self.auth)
        return self._build_job(response.json())

    def get_jobs(self) -> List[Job]:
        """Gets the list of user submitted jobs.

        Returns:
            A list of :class:`eocanvas.api.Job` instances.
        """
        url = self.urls.get("job_list")
        response = get(url, auth=self.auth)
        return [self._build_job(data) for data in response.json()["jobs"]]

    def get_job_logs(self, job: Union[Job, str]) -> List[LogEntry]:
        """Gets the log entries for a job.

        Args:
            job: Either a :class:`eocanvas.api.Job` instance or the `job_id`

        Returns:
            A list of :class:`eocanvas.api.LogEntry` instances.
        """
        if isinstance(job, Job):
            job_id = job.job_id
        else:
            job_id = job

        url = self.urls.get("job_logs", job_id=job_id)
        response = get(url, auth=self.auth)
        return [self._build_log_entry(data) for data in response.json()]

    def get_job_results(self, job: Union[Job, str]) -> List[Result]:
        """Gets the results for a job.

        Args:
            job: Either a :class:`eocanvas.api.Job` instance or the `job_id`

        Returns:
            A list of :class:`eocanvas.api.Result` instances.
        """
        if isinstance(job, Job):
            job_id = job.job_id
        else:
            job_id = job

        url = self.urls.get("job_results", job_id=job_id)
        response = get(url, auth=self.auth)
        return [self._build_result(data) for data in response.json()]

    def download_result(self, result: Result, download_dir: str = "."):
        os.makedirs(download_dir, exist_ok=True)
        url = self.urls.get("download", result_href=result.href)
        response = get(url, auth=self.auth, stream=True)
        download_path = os.path.join(download_dir, result.title)
        logger.info(f"Downloading {download_path}")
        with open(download_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)

    def _build_process(self, data) -> Process:
        mapping = {"processId": "process_id"}
        data = filter_dict_for_dataclass(Process, transform_data(data, mapping))
        data["api"] = self
        return Process(**data)

    def _build_job(self, data) -> Job:
        mapping = {"jobID": "job_id"}
        data = filter_dict_for_dataclass(Job, transform_data(data, mapping))
        data["api"] = self
        return Job(**data)

    def _build_result(self, data) -> Result:
        data = filter_dict_for_dataclass(Result, data)
        data["api"] = self
        return Result(**data)

    def _build_log_entry(self, data) -> LogEntry:
        data = filter_dict_for_dataclass(LogEntry, data)
        # Truncate the nanoseconds to microseconds for compatibility with datetime
        data["timestamp"] = data["timestamp"][:26] + data["timestamp"][-6:]
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return LogEntry(**data)


@dataclass
class Input:
    key: str
    url: str

    def asdict(self):
        return {self.key: self.url}


@dataclass
class ConfigOption:
    uncompress: bool
    sub_path: str

    def asdict(self):
        return {"uncompress": self.uncompress, "subPath": self.sub_path}


@dataclass
class Config:
    key: str
    options: ConfigOption

    def asdict(self):
        return {self.key: self.options.asdict()}


@dataclass
class Job:
    """Represents an API job, that is a submission of a process."""

    api: API
    job_id: str
    status: Optional[str]
    started: Optional[str]
    created: Optional[str] = None
    updated: Optional[str] = None
    finished: Optional[str] = None

    def refresh_from_api(self):
        """Reloads the job attributes from the API."""
        job = self.api.get_job(self.job_id)
        self.status = job.status
        self.created = job.created
        self.updated = job.updated
        self.finished = job.finished

    @property
    def completed(self) -> bool:
        return self.status == "completed"

    @property
    def logs(self) -> List[LogEntry]:
        return self.api.get_job_logs(self)

    @property
    def results(self) -> List[Result]:
        return self.api.get_job_results(self)


@dataclass
class Result:
    api: API
    href: str
    title: str
    rel: str = "result"

    def download(self, download_dir: Optional[str] = None):
        return self.api.download_result(self, download_dir)


@dataclass
class LogEntry:
    timestamp: datetime
    message: str


@dataclass
class Process:
    """A process defines either a Snap or a Datatailor function."""

    api: Optional[API] = None
    process_id: Optional[str] = None
    version: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    inputs: Optional[Any] = None

    def __post_init__(self):
        if self.api is None:
            self.api = API()

    def prepare_inputs(self) -> Any:
        return {}

    def submit(self) -> Job:
        return self.api.exec_process(self)

    def run(self, job: Optional[Job] = None, download_dir: Optional[str] = None):
        if job is None:
            job = self.submit()
        return JobRunner(job).run(download_dir)


class JobRunner:
    def __init__(self, job: Job):
        self.job = job

    def run(self, download_dir: Optional[str] = None):
        sleep = 1
        status = self.job.status
        while status != "successful":
            logger.info(f"Job: {self.job.job_id} - Status: {status}")
            if status == "failed":
                raise JobFailed(
                    f"Job {self.job.job_id} failed. Try checking the logs for more info."
                )
            assert status in ["accepted", "running"]
            time.sleep(sleep)
            sleep = sleep * 1.1
            self.job.refresh_from_api()
            status = self.job.status

        for result in self.job.results:
            result.download(download_dir)
