from __future__ import annotations

import base64
import json
import os
import time
from dataclasses import dataclass, field, fields
from datetime import datetime
from logging import INFO
from typing import TYPE_CHECKING, Any, Dict, Generator, List, Optional, Protocol, Union

import requests

from .auth import Credentials, HTTPOAuth2, OAuthToken
from .config import URLs
from .exceptions import APINotInitializedError, JobFailed, NotDownloadableError
from .http import delete, get, post
from .keystore import encrypt_data
from .logging import logger
from .utils import Singleton

# -----------------------------------------------------
# Utils
# -----------------------------------------------------


def transform_data(input_dict: Dict, mapping: Dict) -> Dict:
    """Remaps the dictionary keys according to the mapping."""
    return {mapping.get(k, k): v for k, v in input_dict.items()}


def filter_dict_for_dataclass(data_class: Any, input_dict: Dict) -> Dict:
    """Discards dictionary keys that don't match with any dataclass field."""
    data_class_fields = {f.name for f in fields(data_class)}
    return {k: v for k, v in input_dict.items() if k in data_class_fields}


# -----------------------------------------------------
# API
# -----------------------------------------------------


class API(metaclass=Singleton):
    """Models the Serverless Functions API endpoints.

    Attributes:
        urls: The :class:`eocanvas.config.URLs` object that maps all the API endpoints
        credentials: A :class:`eocanvas.auth.Credentials` object with username and password
    """

    def __init__(
        self,
        urls: Optional[URLs] = None,
        credentials: Optional[Credentials] = None,
        log_level: int = INFO,
    ):
        """"""
        logger.setLevel(log_level)

        if urls is None:
            urls = URLs()

        if credentials is None:
            credentials = Credentials.load()

        token = OAuthToken(url=urls.token_url, credentials=credentials)

        self.urls = urls
        self.auth = HTTPOAuth2(token)
        self._builder = Builder(self)

    def get_public_key(self) -> str | Any:
        url = self.urls.get("key_detail", key_id="cert/public")
        response = get(url, auth=self.auth)
        return response.content

    def landing_page(self) -> LandingPage:
        """Returns the standard OGC Landing Page."""
        url = self.urls.get("landing_page")
        response = get(url, auth=self.auth)
        return self._builder.build_landing_page(response.json())

    def get_api(self) -> Dict:
        """Gets the current API definition as a dictionary."""
        url = self.urls.get("api")
        response = get(url, auth=self.auth)
        return response.json()

    def get_conformance(self) -> Dict:
        """Gets the OGC conformance list."""
        url = self.urls.get("conformance")
        response = get(url, auth=self.auth)
        return response.json()

    def get_key(self, key_id: str) -> Key:
        """Gets the detail of a key.

        Args:
            key_id (str): The ID of the key.

        Returns:
            A :class:`eocanvas.api.Key` instance.
        """
        url = self.urls.get("key_detail", key_id=key_id)
        response = get(url, auth=self.auth)
        return self._builder.build_key(response.json())

    def get_keys(self) -> List[Key]:
        """Gets the list of available keys.

        Returns:
            A list of :class:`eocanvas.api.Key` instances.
        """
        url = self.urls.get("key_list")
        response = get(url, auth=self.auth)
        return [self._builder.build_key(data) for data in response.json()]

    def create_key(self, key: Key) -> Key:
        """Creates a new Key object.

        Args:
            key (Key): The Key to be saved on the backend.

        Returns:
            Key: The newly created Key
        """
        url = self.urls.get("key_list")
        post(url, json=key.asdict(), auth=self.auth)
        # The API response is empty. We return the key itself.
        return key

    def delete_key(self, key_id: str) -> None:
        """Deletes a Key.

        Args:
            key_id (str): The ID of the key.
        """
        url = self.urls.get("key_detail", key_id=key_id)
        delete(url, auth=self.auth)

    def get_process(self, process_id: str) -> Process:
        """Gets the details of a process.

        Args:
            process_id (str): The ID of the process.

        Returns:
            A :class:`eocanvas.api.Process` instance.
        """
        url = self.urls.get("process_detail", process_id=process_id)
        response = get(url, auth=self.auth)
        return self._builder.build_process(response.json())

    def get_processes(self) -> List[Process]:
        """Gets the list of available processes.

        Returns:
            A list of :class:`eocanvas.api.Process` instances.
        """
        url = self.urls.get("process_list")
        paginator = Paginator(get, url, "processes")
        return [self._builder.build_process(data) for data in paginator.run(auth=self.auth)]

    def exec_process(self, process: Process) -> Job:
        """Submits a process to the API.

        Returns:
            A :class:`eocanvas.api.Job` instance.
        """
        inputs = process.prepare_inputs()
        url = self.urls.get("process_execution", process_id=process.process_id)
        response = post(url, json=inputs, auth=self.auth)
        return self._builder.build_job(response.json())

    def get_job(self, job_id) -> Job:
        """Gets the details of a job.

        Returns:
            A :class:`eocanvas.api.Job` instance.
        """
        url = self.urls.get("job_detail", job_id=job_id)
        response = get(url, auth=self.auth)
        return self._builder.build_job(response.json())

    def get_jobs(self) -> List[Job]:
        """Gets the list of user submitted jobs.

        Returns:
            A list of :class:`eocanvas.api.Job` instances.
        """
        url = self.urls.get("job_list")
        paginator = Paginator(get, url, "jobs")
        return [self._builder.build_job(data) for data in paginator.run(auth=self.auth)]

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
        return [self._builder.build_log_entry(data) for data in response.json()]

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
        results = response.json()

        # If the results are paginated, on the first page the last item is the link
        # to the next one. In that case, we follow it.
        next_page = results[-1]
        while next_page["title"] == "next-page":
            results.pop()
            response = get(self.urls.base_url + next_page["href"], auth=self.auth)
            paginated_results = response.json()
            next_page = paginated_results[-1]
            # From the second page on, the last item is the link to the previous page
            # and the second last the link to the next, if any
            if next_page["title"] == "prev-page":
                next_page = paginated_results[-2]
                results.extend(paginated_results[:-1])
            else:
                results.extend(paginated_results)

        return [self._builder.build_result(data) for data in results]

    def download_result(self, result: Result, download_dir: Optional[str] = None):
        if download_dir is None:
            download_dir = "."

        os.makedirs(download_dir, exist_ok=True)
        response = get(result.full_url, auth=self.auth, stream=True)
        filename = result.title.split("/")[-1]
        download_path = os.path.join(download_dir, filename)
        logger.info(f"Downloading {download_path}")
        with open(download_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)


# -----------------------------------------------------
# Builder
# -----------------------------------------------------


class Builder:
    """A container for methods that builds EOCanvas models instances from dictionaries."""

    def __init__(self, api: API):
        self.api = api

    def build_key(self, data) -> Key:
        mapping = {
            "creationDate": "creation_date",
            "expirationDate": "expiration_date",
            "expireSeconds": "expire_seconds",
            "type": "type_",
        }
        data = filter_dict_for_dataclass(Key, transform_data(data, mapping))
        data["api"] = self.api
        return Key(**data)

    def build_link(self, data) -> Link:
        mapping = {"type": "type_"}
        data = filter_dict_for_dataclass(Link, transform_data(data, mapping))
        return Link(**data)

    def build_process(self, data) -> Process:
        mapping = {"id": "process_id"}
        data = filter_dict_for_dataclass(Process, transform_data(data, mapping))
        data["api"] = self.api
        if "links" in data and data["links"]:
            data["links"] = [self.build_link(link) for link in data["links"]]
        return Process(**data)

    def build_job(self, data) -> Job:
        mapping = {"jobID": "job_id"}
        data = filter_dict_for_dataclass(Job, transform_data(data, mapping))
        data["api"] = self.api
        if "links" in data and data["links"]:
            data["links"] = [self.build_link(link) for link in data["links"]]
        return Job(**data)

    def build_landing_page(self, data) -> LandingPage:
        data = filter_dict_for_dataclass(LandingPage, data)
        if "links" in data and data["links"]:
            data["links"] = [self.build_link(link) for link in data["links"]]
        return LandingPage(**data)

    def build_result(self, data) -> Result:
        data = filter_dict_for_dataclass(Result, data)
        data["api"] = self.api
        return Result(**data)

    def build_log_entry(self, data) -> LogEntry:
        data = filter_dict_for_dataclass(LogEntry, data)
        # Truncate the nanoseconds to microseconds for compatibility with datetime
        data["timestamp"] = data["timestamp"][:26] + data["timestamp"][-6:]
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return LogEntry(**data)


# -----------------------------------------------------
# Models
# -----------------------------------------------------


@dataclass
class Link:
    """A link as represented by the API."""

    href: str
    rel: str
    type_: str
    title: Optional[str] = None


@dataclass
class LandingPage:
    title: str
    description: str
    links: List[Link]


@dataclass
class Input:
    key: str
    url: str
    keystore: Optional[Union[str, Key]] = None

    def asdict(self) -> Dict:
        value = {self.key: self.url}
        if self.keystore is not None:
            if isinstance(self.keystore, str):
                value["schema"] = f"keystore://{self.keystore}"
            else:
                value["schema"] = f"keystore://{self.keystore.name}"

        return value


@dataclass
class ConfigOption:
    sub_path: str
    uncompress: Optional[bool] = None

    def asdict(self) -> Dict:
        if self.uncompress is None:
            return {"subPath": self.sub_path}

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
    links: Optional[list[Link]] = field(default_factory=list)

    def refresh_from_api(self):
        """Reloads the job attributes from the API."""
        job = self.api.get_job(self.job_id)
        self.status = job.status
        self.created = job.created
        self.updated = job.updated
        self.finished = job.finished

    @property
    def completed(self) -> bool:
        return self.status == "successful"

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

    @property
    def full_url(self) -> str:
        return self.href

    def download(self, download_dir: Optional[str] = None):
        if self.title.startswith("keystore"):
            raise NotDownloadableError(
                "External reference to the result, not served by this service."
            )
        else:
            return self.api.download_result(self, download_dir)


@dataclass
class LogEntry:
    timestamp: datetime
    message: str


@dataclass
class Key:
    """A key object as returned by the API.
    Keys are used to configure external storages such as S3, EODATA and WEkEO Drive.
    """

    name: str
    type_: Optional[str] = None
    config: Optional[KeyConfig] = None
    description: Optional[str] = None
    creation_date: Optional[str] = None
    owner: Optional[str] = None
    public: Optional[bool] = False
    api: Optional[API] = None
    expiration_date: Optional[str] = None
    expire_seconds: Optional[int] = 0

    def __post_init__(self):
        if self.config is not None:
            if isinstance(self.config, S3KeyConfig):
                self.type_ = "S3"
            elif isinstance(self.config, WebDavKeyConfig):
                self.type_ = "WEBDAV"

        if self.type_ is not None and self.type_ not in ("S3", "WEBDAV"):
            raise ValueError("Type must be either 'S3' or 'WEBDAV'")

        if self.api is None:
            self.api = API()

    def asdict(self) -> Dict:
        data = {
            f"{self.name}": {
                "type": self.type_,
                "expire": self.expire_seconds or 3600,
                "public": self.public,
                "description": self.description or self.name,
                "data": self.config and self.config.encode() or None,
            }
        }
        return data

    def create(self) -> Key:
        assert self.api is not None, "API not initialized."

        if self.config is None:
            raise ValueError("Cannot create a key without config")

        return self.api.create_key(self)

    def delete(self):
        return self.api.delete_key(self.name)


@dataclass
class _APIParam:
    """
    A simple dataclass with an optional api parameter.
    This is used to avoid `non-default argument 'foo' follows default argument`
    """

    api: Optional[API] = None

    def __post_init__(self):
        super().__post_init__()
        if self.api is None:
            self.api = API()


@dataclass
class KeyConfig:
    """A configuration object that encrypt either an S3 or a WEBDAV key"""

    if TYPE_CHECKING:
        api: Optional[API] = None

    def asdict(self: Any):
        return {f.name: getattr(self, f.name) for f in fields(self) if f.name != "api"}

    def encode(self) -> Optional[str]:
        if self.api is not None:
            encrypted = encrypt_data(json.dumps(self.asdict()).encode(), self.api.get_public_key())
            encoded = base64.b64encode(encrypted).decode("utf-8")
            return encoded
        return None


@dataclass
class _S3KeyParams:
    secret_key: str
    access_key: str
    bucket: str
    endpoint: str
    region: str

    def __post_init__(self):
        if not self.endpoint.startswith("https://"):
            raise ValueError("Endpoint does not look like a URL")


@dataclass
class _WebDavKeyParams:
    endpoint: str
    username: str
    password: str

    def __post_init__(self):
        if not self.endpoint.startswith("https://"):
            raise ValueError("Endpoint does not look like a URL")


@dataclass
class S3KeyConfig(KeyConfig, _APIParam, _S3KeyParams):
    """A configuration for S3-like keys."""


@dataclass
class WebDavKeyConfig(KeyConfig, _APIParam, _WebDavKeyParams):
    """A configuration for WebDav-like keys."""


@dataclass
class Process:
    """A process defines either a SNAP or a Datatailor function."""

    api: Optional[API] = None
    process_id: Optional[str] = None
    version: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    inputs: Optional[Any] = None
    keywords: Optional[Any] = None
    metadata: Optional[Any] = None
    output: Optional[Union[str, Key]] = None
    links: Optional[list[Link]] = field(default_factory=list)

    def __post_init__(self):
        if self.api is None:
            self.api = API()

    def prepare_inputs(self) -> Dict:
        inputs = {
            "inputs": {},  # To be defined in subclasses
            "outputs": {},
            "response": "raw",
        }
        if self.output is not None:
            if isinstance(self.output, str):
                keystore = self.output
            else:
                keystore = self.output.name

            inputs["outputs"] = {"output": {"format": {"schema": f"keystore://{keystore}"}}}

        return inputs

    def submit(self) -> Job:
        if self.api is None:
            raise APINotInitializedError("API not initialized")
        return self.api.exec_process(self)

    def run(
        self, job: Optional[Job] = None, download_dir: Optional[str] = None, download: bool = True
    ):
        if job is None:
            job = self.submit()
        return JobRunner(job, download).run(download_dir)


class JobRunner:
    def __init__(self, job: Job, download: bool = True):
        self.job = job
        self.download = download

    def run(self, download_dir: Optional[str] = None):
        sleep = 10.0
        status = self.job.status
        while status != "successful":
            now = datetime.now().isoformat()
            logger.info(f"Job: {self.job.job_id} - Status: {status} at {now}")
            if status == "failed":
                raise JobFailed(
                    f"Job {self.job.job_id} failed. Try checking the logs for more info."
                )
            assert status in ["accepted", "running"]
            time.sleep(sleep)
            sleep = sleep * 1.1
            self.job.refresh_from_api()
            status = self.job.status

        if self.download:
            for result in self.job.results:
                try:
                    result.download(download_dir)
                except NotDownloadableError:
                    logger.info(result.title)


class GetCallable(Protocol):
    """A simple protocol to mimic the http.get method interface."""

    def __call__(self, url: str, **kwargs: Any) -> requests.Response: ...


class Paginator:
    """A class that implements standard OGC pagination mechanism."""

    def __init__(
        self,
        get_func: GetCallable,
        start_url: str,
        results_key: str,
        limit: int = 10,
        initial_offset: int = 0,
    ):
        """Initialize a Paginator instance.
        A paginator can then be iterated over by calling its run method.

        Args:
            get_func (GetCallable): Usually the http.get function
            start_url (str): The URL of the first page
            results_key (str): The key of the response where the results are
            limit (int, optional): How many results per request. Defaults to 10.
            initial_offset (int, optional): The offset of the results from the beginning. Defaults to 0.
        """
        self.get_func = get_func
        self.current_url: Optional[str] = start_url
        self.results_key = results_key
        self.limit = limit
        self.initial_offset = initial_offset

    def _get_next_url(self, data: Dict[str, Any]) -> Optional[str]:
        """Get the next URL from the response or None if it is not
        set or if the results list is empty.

        Args:
            data (Dict[str, Any]): The JSON response

        Returns:
            Optional[str]: Either the next URL or None
        """
        # The API might send a next link even when the items are exhausted
        if not len(data.get(self.results_key, [])):
            return None

        links = data.get("links", [])
        for link in links:
            if link.get("rel") == "next":
                return link.get("href")
        return None

    def run(self, **kwargs: Any) -> Generator[Dict[str, Any], None, None]:
        """Iterate over the paginator until it is fully consumed.

        Yields:
            Generator[Dict[str, Any], None, None]: The JSON objects representing the results.
        """
        params = kwargs.pop("params", {})
        if self.limit is not None:
            params["limit"] = self.limit
        if self.initial_offset is not None:
            params["offset"] = self.initial_offset

        first_run = True
        while self.current_url:
            current_params = params if first_run else None
            response = self.get_func(self.current_url, params=current_params, **kwargs)
            data = response.json()
            # Yield data from the current page
            items = data.get(self.results_key, [])
            for item in items:
                yield item

            self.current_url = self._get_next_url(data)
            first_run = False
