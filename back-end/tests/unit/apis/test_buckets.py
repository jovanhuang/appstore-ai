from pathlib import Path
from urllib3 import HTTPResponse

import pytest
from fastapi.testclient import TestClient
from minio import Minio

from src.config.config import config

BUCKET_NAME = config.MINIO_BUCKET_NAME


@pytest.mark.usefixtures("flush_s3")
@pytest.mark.parametrize("file_path", ["./test_data/video1.mp4"])
def test_upload_video(file_path: str, client: TestClient, s3_client: Minio):
    # Check that s3 is empty at start
    assert len(list(s3_client.list_objects(BUCKET_NAME, recursive=True))) == 0
    response = client.post(
        "/buckets/video",
        files={"video": open(Path(__file__).parent.joinpath(file_path), "rb")},
    )
    data = response.json()
    response.raise_for_status()
    assert "video_location" in data

    video_location: str = data["video_location"]
    bucket, object_name = video_location.removeprefix("s3://").split(
        "/", maxsplit=1
    )
    assert bucket == BUCKET_NAME

    # Check that path exists
    s3_response: HTTPResponse = s3_client.get_object(BUCKET_NAME, object_name)
    assert s3_response.status != 404
    s3_response.close()
    s3_response.release_conn()


@pytest.mark.usefixtures("flush_s3")
@pytest.mark.parametrize(
    "old_file,new_file", [("./test_data/video1.mp4", "./test_data/video2.mp4")]
)
def test_update_video(
    old_file: str, new_file: str, client: TestClient, s3_client: Minio
):
    test_upload_video(old_file, client, s3_client)

    # Check that file exists
    objects = list(s3_client.list_objects(BUCKET_NAME, recursive=True))
    old_object_name = objects[0].object_name
    assert len(objects) == 1

    # Now attempt to replace
    response = client.put(
        "/buckets/video",
        data={
            "old_video_location": f"{config.MINIO_API_HOST}/{BUCKET_NAME}/{old_object_name}"
        },
        files={"new_video": open(Path(__file__).parent.joinpath(new_file), "rb")},
    )
    response.raise_for_status()
    data = response.json()
    assert "video_location" in data

    # Then check whether it has been replaced
    objects = list(s3_client.list_objects(BUCKET_NAME, recursive=True))
    new_object_name = objects[0].object_name
    assert old_object_name != new_object_name
