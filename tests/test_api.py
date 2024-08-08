import pytest
import responses

from eocanvas import API
from eocanvas.api import Job, JobRunner, Process
from eocanvas.config import URLs
from eocanvas.exceptions import JobFailed

PROCESSES_RESPONSE = [
    {
        "processId": "snap-function",
        "version": "v0.11",
        "title": "snap-function",
        "description": "Function based on the ESA SNAP tool version 10.",
        "inputs": {
            "eo_config": {
                "title": "Configuration for eo_input",
                "description": "Configuration for the eo_input in JSON format. They instruct the function on how to deal with the eo_input (e.g., uncompress).",  # noqa: E501
                "minOccurs": 0,
                "maxOccurs": 1,
                "schema": {"$ref": "https://string"},
            },
            "snap_graph": {
                "title": "ESA SNAP GPT graph",
                "description": "A base64-encoded gpt graph. It should contain placeholders referring to the eo_input field.",  # noqa: E501
                "minOccurs": 0,
                "maxOccurs": 1,
                "schema": {"$ref": "https://string"},
            },
            "eo_input": {
                "title": "eo_inputs Title",
                "description": "Named inputs provided to the ESA SNAP tool in JSON encoding. They should match the placeholders in the SNAP's GPT graph.",  # noqa: E501
                "minOccurs": 0,
                "maxOccurs": 1,
                "schema": {"$ref": "http://named_inputs"},
            },
        },
        "outputs": {
            "output": {
                "title": "SNAP output",
                "description": "A set of artifacts produced by the ESA SNAP Tool.",
                "schema": {"$ref": "https://string"},
            }
        },
    },
    {
        "processId": "dataTailor",
        "version": "v1.3",
        "title": "EUMETSAT Data Tailor",
        "description": "The EUMETSAT Data Tailor provides format conversion and basic product customisation capabilities for a set of EUMETSAT products in native formats.",  # noqa: E501
        "inputs": {
            "epct_input": {
                "title": "eo_inputs Title",
                "description": "Named inputs provided to the EUMETSAT Data Tailor tool in JSON encoding.",  # noqa: E501
                "minOccurs": 0,
                "maxOccurs": 1,
                "schema": {"$ref": "http://named_inputs"},
            },
            "epct_chain": {
                "title": "EUMETSAT Data Tailor chain file",
                "description": "Customisation file describing the chain of customisation to apply to the epct_input files.",  # noqa: E501
                "minOccurs": 0,
                "maxOccurs": 1,
                "schema": {"$ref": "https://string"},
            },
        },
        "outputs": {
            "output": {
                "title": "Data Tailor output",
                "description": "A set of artifacts produced by the EUMETSAT Data Tailor Tool.",
                "schema": {"$ref": "https://string"},
            }
        },
    },
]


JOBS_RESPONSE = {
    "jobs": [
        {
            "processID": "snap-function",
            "type": "process",
            "jobID": "93fc7efb-4860-5de1-bd75-ca850685bed4",
            "status": "failed",
            "created": "2024-08-01:13.23.46",
            "started": "2024-08-01:13.23.46",
            "finished": "2024-08-01T13:24:08Z",
            "updated": "2024-08-01T13:24:08.592105096Z",
        },
        {
            "processID": "snap-function",
            "type": "process",
            "jobID": "93fc7efb-4860-5de1-bd75-ca850685bed5",
            "status": "successful",
            "created": "2024-08-01:13.23.46",
            "started": "2024-08-01:13.23.46",
            "finished": "2024-08-01T13:24:08Z",
            "updated": "2024-08-01T13:24:08.592105096Z",
        },
    ],
    "links": [],
}


JOBS_RESULTS_RESPONSE = [
    {
        "href": "/download/result/1",
        "title": "title1",
    },
    {
        "href": "/download/result/2",
        "title": "title2",
    },
    {
        "href": "/download/result/3",
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
        yield rsps


def test_get_processes(mock_api):
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
    assert processes[0].title == "snap-function"
    assert processes[1].title == "EUMETSAT Data Tailor"


def test_get_process(mock_api):
    urls = URLs()
    mock_api.add(
        responses.GET,
        url=urls.get("process_detail", process_id=PROCESSES_RESPONSE[0]["processId"]),
        json=PROCESSES_RESPONSE[0],
        status=200,
    )

    api = API()
    process = api.get_process(PROCESSES_RESPONSE[0]["processId"])
    assert process.title == "snap-function"


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
        status=200,
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
        status="completed",
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
        status="completed",
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
            url=urls.get("download", result_href=result["href"]),
            status=200,
        )

    api = API()
    job = api.get_job(job_id=JOBS_RESPONSE["jobs"][1]["jobID"])
    runner = JobRunner(job)
    runner.run(tmp_path)
