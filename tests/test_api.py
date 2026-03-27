from typing import Any
from unittest.mock import Mock, patch

import pytest
import responses

from eocanvas import API
from eocanvas.api import Job, JobRunner, Key, Paginator, Process, S3KeyConfig, WebDavKeyConfig
from eocanvas.auth import Credentials
from eocanvas.config import URLs
from eocanvas.exceptions import JobFailed
from eocanvas.processes import SnapProcess
from eocanvas.snap.graph import Graph

PROCESSES_RESPONSE = {
    "processes": [
        {
            "title": "snap",
            "description": "Function based on the ESA SNAP tool version 10.",
            "id": "snap-function",
            "version": "10.0.0",
            "jobControlOptions": ["async-execute"],
            "outputTransmission": ["value"],
            "links": [
                {
                    "href": "https://gateway.impl.wekeo2.eu/serverless/snap-function",
                    "rel": "self",
                    "type": "application/json",
                    "title": "Process description",
                },
                {
                    "href": "https://gateway.impl.wekeo2.eu/serverless/snap-function/execution",
                    "rel": "http://www.opengis.net/def/rel/ogc/1.0/execute",
                    "type": "application/json",
                    "title": "Execute endpoint",
                },
            ],
        },
        {
            "title": "EUMETSAT Data Tailor",
            "description": "The EUMETSAT Data Tailor provides format conversion.",
            "id": "dataTailor",
            "version": "3.4.0",
            "jobControlOptions": ["async-execute"],
            "outputTransmission": ["value"],
            "links": [
                {
                    "href": "https://gateway.impl.wekeo2.eu/serverless/dataTailor",
                    "rel": "self",
                    "type": "application/json",
                    "title": "Process description",
                },
                {
                    "href": "https://gateway.impl.wekeo2.eu/serverless/dataTailor/execution",
                    "rel": "http://www.opengis.net/def/rel/ogc/1.0/execute",
                    "type": "application/json",
                    "title": "Execute endpoint",
                },
            ],
        },
    ],
    "links": [],
}


JOBS_RESPONSE = {
    "jobs": [
        {
            "jobID": "1237bb85-3f19-5786-8cc0-1582bb45903a",
            "processID": "snap-function",
            "type": "process",
            "status": "failed",
            "created": "2026-03-05T16:07:08Z",
            "started": "2026-03-05T16:07:08Z",
            "finished": "2026-03-05T16:07:46Z",
            "updated": "2026-03-05T16:07:46Z",
            "links": [
                {
                    "href": "https://example.com/serverless/jobs/1237bb85",
                    "rel": "self",
                    "type": "application/json",
                },
                {
                    "href": "https://example.com/serverless/jobs/1237bb85",
                    "rel": "monitor",
                    "type": "application/json",
                },
            ],
        },
        {
            "jobID": "93fc7efb-4860-5de1-bd75-ca850685bed5",
            "processID": "snap-function",
            "type": "process",
            "status": "successful",
            "created": "2026-03-05T16:07:08Z",
            "started": "2026-03-05T16:07:08Z",
            "finished": "2026-03-05T16:07:46Z",
            "updated": "2026-03-05T16:07:46Z",
            "links": [
                {
                    "href": "https://example.com/serverless/jobs/1237bb85",
                    "rel": "self",
                    "type": "application/json",
                },
                {
                    "href": "https://example.com/serverless/jobs/1237bb85",
                    "rel": "monitor",
                    "type": "application/json",
                },
            ],
        },
    ],
    "links": [],
}


JOBS_RESULTS_RESPONSE = [
    {
        "href": "https://example.com/download/result/1",
        "title": "title1",
    },
    {
        "href": "https://example.com/download/result/2",
        "title": "title2",
    },
    {
        "href": "https://example.com/download/result/3",
        "title": "title3",
    },
]


JOBS_LOGS_RESPONSE = [
    {
        "timestamp": "2024-12-06T15:31:45.123456789+00:00",
        "message": "message1",
    },
    {
        "timestamp": "2024-12-06T15:31:45.123456789+00:00",
        "message": "message2",
    },
    {
        "timestamp": "2024-12-06T15:31:45.123456789+00:00",
        "message": "message3",
    },
]


KEYS_RESPONSE = [
    {
        "name": "eodata2",
        "creationDate": "2024-09-19 13:43:02",
        "expirationDate": None,
        "description": "eodata key",
        "expireSeconds": 0,
        "owner": "jlgauthier",
        "type": "S3",
        "public": True,
    },
    {
        "name": "eodata",
        "creationDate": "2024-09-19 13:43:02",
        "expirationDate": None,
        "description": "eodata key",
        "expireSeconds": 150,
        "owner": "jlgauthier",
        "type": "S3",
        "public": False,
    },
]


TEST_PUBLIC_KEY_PEM = b"""
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAnYQFvD8MZ2NiGtf7OEqn
gVZ0mkvDzoShIWk7y5sA2WtLHoFTIN93Gj8VtuGa6z1fnTxyw+u+TNgHRGQBgHT4
LQf7YlfcLVNRFB4VzTFVjb2IjJZdg7gkp8q4C1+e7LjRkXkt4pJkkhSfV5PqeS3E
sImE6BopLZBzKkqElZ4woUgEDZ5EpICLPm+eQk0sq+gjHiPpEcRniNyRi1fPAFSH
DRUgFNyU3TsIrYq5DdTCJcyAHo/JUNIsvjC+ArVnD/m0t8g6Q50vhA9PQfSnGBL6
QwPZCxTQSAprhgsgOBUMUpFm2RnFob/YiFFu4Udo5EkN1PVJZuBo4ZpTPNdI1IwB
DQIDAQAB
-----END PUBLIC KEY-----
"""


PUBLIC_KEY_RESPONSE = TEST_PUBLIC_KEY_PEM


@pytest.fixture
def mock_api():
    urls = URLs()
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        rsps.add(
            responses.POST,
            url=urls.token_url,
            json={
                "access_token": "fake_token",
                "refresh_token": "fake_token",
                "scope": "openid",
                "id_token": "fake_token",
                "token_type": "Bearer",
                "expires_in": 1744,
            },
            status=200,
        )
        rsps.add(
            responses.GET,
            url=urls.get("key_detail", key_id="cert/public"),
            body=TEST_PUBLIC_KEY_PEM,
            status=200,
        )
        yield rsps


@pytest.fixture
def mock_credentials():
    with patch.object(Credentials, "load", return_value=Credentials("abc", "abc")) as mock:
        yield mock


def test_get_processes(mock_api, mock_credentials):
    urls = URLs()
    mock_api.add(
        responses.GET,
        url=urls.get("process_list"),
        json=PROCESSES_RESPONSE,
        status=200,
    )

    api = API()
    processes = api.get_processes()
    assert len(processes) == 2
    assert processes[0].title == "snap"
    assert processes[1].title == "EUMETSAT Data Tailor"


def test_get_process(mock_api):
    urls = URLs()
    mock_api.add(
        responses.GET,
        url=urls.get("process_detail", process_id=PROCESSES_RESPONSE["processes"][0]["id"]),
        json=PROCESSES_RESPONSE["processes"][0],
        status=200,
    )

    api = API()
    process = api.get_process(PROCESSES_RESPONSE["processes"][0]["id"])
    assert process.title == "snap"
    assert process.links[0].title == "Process description"


def test_exec_process(mock_api):
    process = Process(process_id="fake_process")
    urls = URLs()
    mock_api.add(
        responses.POST,
        url=urls.get("process_execution", process_id=process.process_id),
        json={
            "processID": "snap-function",
            "type": "process",
            "jobID": "93fc7efb-4860-5de1-bd75-ca850685bed4",
            "status": "accepted",
            "started": "2024-08-01:13.23.46",
        },
        status=201,
    )

    api = API()
    job = api.exec_process(process)
    assert job.job_id == "93fc7efb-4860-5de1-bd75-ca850685bed4"
    assert job.status == "accepted"


def test_get_jobs(mock_api):
    urls = URLs()
    mock_api.add(responses.GET, url=urls.get("job_list"), json=JOBS_RESPONSE, status=200)

    api = API()
    jobs = api.get_jobs()
    assert len(jobs) == 2
    assert jobs[0].job_id == JOBS_RESPONSE["jobs"][0]["jobID"]


def test_get_job(mock_api):
    urls = URLs()
    mock_api.add(
        responses.GET,
        url=urls.get("job_detail", job_id=JOBS_RESPONSE["jobs"][0]["jobID"]),
        json=JOBS_RESPONSE["jobs"][0],
        status=200,
    )

    api = API()
    job = api.get_job(job_id=JOBS_RESPONSE["jobs"][0]["jobID"])
    assert job.job_id == JOBS_RESPONSE["jobs"][0]["jobID"]
    assert job.links[0].href == "https://example.com/serverless/jobs/1237bb85"


def test_get_job_results(mock_api):
    urls = URLs()
    mock_api.add(
        responses.GET,
        url=urls.get("job_results", job_id=JOBS_RESPONSE["jobs"][0]["jobID"]),
        json=JOBS_RESULTS_RESPONSE,
        status=200,
    )

    api = API()
    results = api.get_job_results(JOBS_RESPONSE["jobs"][0]["jobID"])
    assert len(results) == 3
    assert results[0].title == "title1"


def test_job_results(mock_api):
    urls = URLs()
    mock_api.add(
        responses.GET,
        url=urls.get("job_results", job_id=JOBS_RESPONSE["jobs"][0]["jobID"]),
        json=JOBS_RESULTS_RESPONSE,
        status=200,
    )

    job = Job(
        api=API(),
        job_id=JOBS_RESPONSE["jobs"][0]["jobID"],
        status="successful",
        started="2013",
    )
    assert len(job.results) == 3
    assert job.results[0].title == "title1"


def test_get_job_logs(mock_api):
    urls = URLs()
    mock_api.add(
        responses.GET,
        url=urls.get("job_logs", job_id=JOBS_RESPONSE["jobs"][0]["jobID"]),
        json=JOBS_LOGS_RESPONSE,
        status=200,
    )

    api = API()
    results = api.get_job_logs(JOBS_RESPONSE["jobs"][0]["jobID"])
    assert len(results) == 3
    assert results[0].message == "message1"


def test_job_logs(mock_api):
    urls = URLs()
    mock_api.add(
        responses.GET,
        url=urls.get("job_logs", job_id=JOBS_RESPONSE["jobs"][0]["jobID"]),
        json=JOBS_LOGS_RESPONSE,
        status=200,
    )

    job = Job(
        api=API(),
        job_id=JOBS_RESPONSE["jobs"][0]["jobID"],
        status="successful",
        started="2013",
    )
    assert len(job.logs) == 3
    assert job.logs[0].message == "message1"


def test_job_runner_failed(mock_api):
    urls = URLs()
    mock_api.add(
        responses.GET,
        url=urls.get("job_detail", job_id=JOBS_RESPONSE["jobs"][0]["jobID"]),
        json=JOBS_RESPONSE["jobs"][0],
        status=200,
    )
    api = API()
    job = api.get_job(job_id=JOBS_RESPONSE["jobs"][0]["jobID"])
    runner = JobRunner(job)
    with pytest.raises(JobFailed):
        runner.run()


def test_job_runner(mock_api, tmp_path):
    urls = URLs()
    mock_api.add(
        responses.GET,
        url=urls.get("job_detail", job_id=JOBS_RESPONSE["jobs"][1]["jobID"]),
        json=JOBS_RESPONSE["jobs"][1],
        status=200,
    )
    mock_api.add(
        responses.GET,
        url=urls.get("job_results", job_id=JOBS_RESPONSE["jobs"][1]["jobID"]),
        json=JOBS_RESULTS_RESPONSE,
        status=200,
    )
    for result in JOBS_RESULTS_RESPONSE:
        mock_api.add(
            responses.GET,
            url=result["href"],
            status=200,
        )

    api = API()
    job = api.get_job(job_id=JOBS_RESPONSE["jobs"][1]["jobID"])
    runner = JobRunner(job)
    runner.run(tmp_path)


def test_process_run(mock_api, tmp_path):
    urls = URLs()
    mock_api.add(
        responses.GET,
        url=urls.get("job_detail", job_id=JOBS_RESPONSE["jobs"][1]["jobID"]),
        json=JOBS_RESPONSE["jobs"][1],
        status=200,
    )
    mock_api.add(
        responses.GET,
        url=urls.get("job_results", job_id=JOBS_RESPONSE["jobs"][1]["jobID"]),
        json=JOBS_RESULTS_RESPONSE,
        status=200,
    )
    mock_api.add(
        responses.POST,
        url=urls.get("process_execution", process_id="snap-function"),
        json={
            "processID": "snap-function",
            "type": "process",
            "jobID": JOBS_RESPONSE["jobs"][1]["jobID"],
            "status": "successful",
            "started": "2024-08-01:13.23.46",
        },
        status=200,
    )
    for result in JOBS_RESULTS_RESPONSE:
        mock_api.add(
            responses.GET,
            url=result["href"],
            status=200,
        )

    g = Graph.from_text(b'<?xml version="1.0"?><data></data>')
    p = SnapProcess(snap_graph=g)
    p.run(download_dir=tmp_path)


def test_get_keys(mock_api, mock_credentials):
    urls = URLs()
    mock_api.add(
        responses.GET,
        url=urls.get("key_list"),
        json=KEYS_RESPONSE,
        status=200,
    )

    api = API()
    keys = api.get_keys()
    assert len(keys) == 2
    assert keys[0].name == "eodata2"
    assert keys[1].name == "eodata"


def test_get_public_key(mock_api):
    urls = URLs()
    mock_api.add(
        responses.GET,
        url=urls.get("key_detail", key_id="cert/public"),
        body=PUBLIC_KEY_RESPONSE,
        status=200,
    )

    api = API()
    public_key = api.get_public_key()
    assert public_key == TEST_PUBLIC_KEY_PEM


def test_get_key(mock_api):
    urls = URLs()
    mock_api.add(
        responses.GET,
        url=urls.get("key_detail", key_id=KEYS_RESPONSE[0]["name"]),
        json=KEYS_RESPONSE[0],
        status=200,
    )

    api = API()
    key = api.get_key(KEYS_RESPONSE[0]["name"])
    assert key.name == "eodata2"


def test_webdav_encode(mock_api):
    urls = URLs()
    mock_api.add(
        responses.GET,
        url=urls.get("key_detail", key_id="cert/public"),
        body=PUBLIC_KEY_RESPONSE,
        status=200,
    )
    data = WebDavKeyConfig(username="abc", endpoint="https://", password="abc")
    encoded = data.encode()
    assert isinstance(encoded, str)


def test_s3_encode(mock_api):
    urls = URLs()
    mock_api.add(
        responses.GET,
        url=urls.get("key_detail", key_id="cert/public"),
        body=PUBLIC_KEY_RESPONSE,
        status=200,
    )
    data = S3KeyConfig(
        access_key="abc", bucket="abc", endpoint="https://", region="abc", secret_key="abc"
    )
    encoded = data.encode()
    assert isinstance(encoded, str)


def test_create_s3_key(mock_api):
    config = S3KeyConfig(
        access_key="abc", bucket="abc", endpoint="https://", region="abc", secret_key="abc"
    )
    key = Key(name="fake_key", description="test", config=config)
    urls = URLs()
    mock_api.add(
        responses.POST,
        url=urls.get("key_list"),
        body="",
        status=201,
    )

    key = key.create()
    assert key.name == "fake_key"


def test_create_s3_key_from_api(mock_api):
    config = S3KeyConfig(
        access_key="abc", bucket="abc", endpoint="https://", region="abc", secret_key="abc"
    )
    key = Key(name="fake_key", description="test", config=config)
    urls = URLs()
    mock_api.add(
        responses.POST,
        url=urls.get("key_list"),
        body="",
        status=201,
    )

    api = API()
    key = api.create_key(key)
    assert key.name == "fake_key"


def test_create_webdav_key(mock_api):
    config = WebDavKeyConfig(username="abc", endpoint="https://", password="abc")
    key = Key(name="fake_key", description="test", config=config)
    urls = URLs()
    mock_api.add(
        responses.POST,
        url=urls.get("key_list"),
        body="",
        status=201,
    )

    key = key.create()
    assert key.name == "fake_key"


def test_create_webdav_key_from_api(mock_api):
    config = WebDavKeyConfig(username="abc", endpoint="https://", password="abc")
    key = Key(name="fake_key", description="test", config=config)
    urls = URLs()
    mock_api.add(
        responses.POST,
        url=urls.get("key_list"),
        body="",
        status=201,
    )

    api = API()
    key = api.create_key(key)
    assert key.name == "fake_key"


def test_invalid_key_type():
    with pytest.raises(ValueError):
        Key(name="test", type_="test")


def test_paginator_yields_all_items_across_pages():
    page1_data = {
        "processes": [{"id": "p1"}, {"id": "p2"}],
        "links": [{"rel": "next", "href": "https://api.example.org/processes?offset=2"}],
    }
    page2_data = {
        "processes": [{"id": "p3"}],
        "links": [{"rel": "prev", "href": "https://api.example.org/processes?offset=0"}],
    }

    def mock_get(url: str, params: Any = None, **kwargs: Any) -> Mock:
        response = Mock()
        if "offset=2" in url or (params and params.get("offset") == 2):
            response.json.return_value = page2_data
        else:
            response.json.return_value = page1_data

        response.raise_for_status = Mock()
        return response

    paginator = Paginator(
        get_func=mock_get,
        start_url="https://api.example.org/processes",
        results_key="processes",
        limit=2,
    )

    results = list(paginator.run())

    assert len(results) == 3
    assert results[0]["id"] == "p1"
    assert results[1]["id"] == "p2"
    assert results[2]["id"] == "p3"


def test_paginator_handles_empty_results():
    def mock_get_empty(url: str, **kwargs: Any) -> Mock:
        response = Mock()
        response.json.return_value = {"processes": [], "links": []}
        return response

    paginator = Paginator(mock_get_empty, "https://api.url", "processes")
    results = list(paginator.run())

    assert results == []
