import datetime
import json
from colorama import Fore
from fastapi import Depends
from minio import Minio

from ..dependencies.mongo_client import get_db
from ..dependencies.minio_client import (
    minio_api_client,
    upload_data,
    compose_data,
    get_data,
)

from ...config.config import config
from ...internal.preprocess_html import process_html_to_base64
from ...models.common import S3Storage
from ...models.iam import TokenData
from ...models.model import ModelCardPackage


async def export_selected_models(
    card_package: ModelCardPackage,
    user: TokenData,
    s3_client: Minio = Depends(minio_api_client),
):
    try:
        db, mongo_client = get_db()
        pkg = card_package.dict()["card_package"]
        current_time_stringified = datetime.datetime.now().strftime(
            "%Y-%m-%d_%H:%M:%S.%f"
        )
        current_time = str(datetime.datetime.now())
        BUCKET_NAME = config.MINIO_BUCKET_NAME or "default"

        async with await mongo_client.start_session() as session:
            async with session.start_transaction():
                await db["exports"].insert_one(
                    {
                        "userId": user.user_id,
                        "timeInitiated": current_time,
                        "models": pkg,
                    }
                )
                for x in pkg:
                    try:
                        existing_card = await db["models"].find_one(
                            {
                                "modelId": x["model_id"],
                                "creatorUserId": x["creator_user_id"],
                            }
                        )
                        existing_card["markdown"] = process_html_to_base64(
                            existing_card["markdown"]
                        )
                        existing_card["performance"] = process_html_to_base64(
                            existing_card["performance"]
                        )
                        subfile_name = f'{x["creator_user_id"]}-{x["model_id"]}'
                        dumped_JSON: str = json.dumps(
                            existing_card,
                            ensure_ascii=False,
                            indent=4,
                            sort_keys=True,
                            default=str,
                        )
                        try:
                            upload_data(
                                s3_client,
                                dumped_JSON.encode("utf-8"),
                                f"exports/{current_time_stringified}/{subfile_name}/card-metadata.json",
                                BUCKET_NAME,
                                "application/json",
                            )
                        except Exception as err:
                            await db["exports"].update_one(
                                {
                                    "userId": user.user_id,
                                    "timeInitiated": current_time,
                                    "models.model_id": x["model_id"],
                                    "models.creator_user_id": x["creator_user_id"],
                                },
                                {
                                    "$set": {
                                        "models.$.progress": "Failed",
                                    },
                                    "$push": {
                                        "models.$.reason": "Card metadata could not be retrieved",
                                    },
                                },
                            )
                            print(
                                f"{Fore.YELLOW}WARNING{Fore.WHITE}:  Could not retrieve card metadata info. Skipping...!"
                            )
                        try:

                            artifactSet = existing_card["artifacts"]
                            modelFileLocation = str(
                                list(
                                    filter(
                                        lambda d: d["artifactType"] == "mainModel",
                                        artifactSet,
                                    )
                                )[0]["url"]
                            )
                            (model_bucket, model_object) = modelFileLocation.split(
                                "s3://"
                            )[1].split("/", 1)
                            compose_data(
                                s3_client,
                                [
                                    S3Storage(
                                        bucket_name=model_bucket,
                                        object_name=model_object,
                                    )
                                ],
                                f"exports/{current_time_stringified}/{subfile_name}/{model_object.split('/')[-1]}",
                                BUCKET_NAME,
                            )
                        except Exception as err:
                            await db["exports"].update_one(
                                {
                                    "userId": user.user_id,
                                    "timeInitiated": current_time,
                                    "models.model_id": x["model_id"],
                                    "models.creator_user_id": x["creator_user_id"],
                                },
                                {
                                    "$set": {
                                        "models.$.progress": "Failed",
                                    },
                                    "$push": {
                                        "models.$.reason": "Model file could not be retrieved",
                                    },
                                },
                            )
                            print(
                                f"{Fore.YELLOW}WARNING{Fore.WHITE}:  Could not retrieve model file. Skipping...!"
                            )
                        if (
                            existing_card["task"] == "Reinforcement Learning"
                            and existing_card["videoLocation"] is not None
                        ):
                            try:
                                url: str = existing_card["videoLocation"]
                                url = url.removeprefix("s3://")
                                bucket, object_name = url.split("/", 1)
                                response = get_data(s3_client, object_name, bucket)

                                file_extension = object_name.split(".").pop()
                                upload_data(
                                    s3_client,
                                    response.data,
                                    f"exports/{current_time_stringified}/{subfile_name}/example-video.{file_extension}",
                                    BUCKET_NAME,
                                    f"video/{file_extension}",
                                )
                                response.close()
                                response.release_conn()
                            except Exception as err:
                                await db["exports"].update_one(
                                    {
                                        "userId": user.user_id,
                                        "timeInitiated": current_time,
                                        "models.model_id": x["model_id"],
                                        "models.creator_user_id": x["creator_user_id"],
                                    },
                                    {
                                        "$set": {
                                            "models.$.progress": "Failed",
                                        },
                                        "$push": {
                                            "models.$.reason": "Example video could not be retrieved",
                                        },
                                    },
                                )
                                print(
                                    f"{Fore.YELLOW}WARNING{Fore.WHITE}:  Could not retrieve video from bucket. Skipping...!"
                                )
                        else:
                            try:
                                existing_service = await db["services"].find_one(
                                    {
                                        "modelId": x["model_id"],
                                        "creatorUserId": x["creator_user_id"],
                                    }
                                )
                                dumped_JSON_service: str = json.dumps(
                                    existing_service,
                                    ensure_ascii=False,
                                    indent=4,
                                    sort_keys=True,
                                    default=str,
                                )
                                upload_data(
                                    s3_client,
                                    dumped_JSON_service.encode("utf-8"),
                                    f"exports/{current_time_stringified}/{subfile_name}/service-metadata.json",
                                    BUCKET_NAME,
                                    "application/json",
                                )
                            except Exception as err:
                                await db["exports"].update_one(
                                    {
                                        "userId": user.user_id,
                                        "timeInitiated": current_time,
                                        "models.model_id": x["model_id"],
                                        "models.creator_user_id": x["creator_user_id"],
                                    },
                                    {
                                        "$set": {
                                            "models.$.progress": "Failed",
                                        },
                                        "$push": {
                                            "models.$.reason": "Service metadata could not be retrieved",
                                        },
                                    },
                                )
                                print(
                                    f"{Fore.YELLOW}WARNING{Fore.WHITE}:  Could not retrieve service info from database. Skipping...!"
                                )
                        log = await db["exports"].find_one(
                            {
                                "userId": user.user_id,
                                "timeInitiated": current_time,
                            },
                            {
                                "models": {
                                    "$elemMatch": {
                                        "model_id": x["model_id"],
                                        "creator_user_id": x["creator_user_id"],
                                    }
                                },
                            },
                        )
                        if not "progress" in log["models"][0].keys():
                            await db["exports"].update_one(
                                {
                                    "userId": user.user_id,
                                    "timeInitiated": current_time,
                                    "models.model_id": x["model_id"],
                                    "models.creator_user_id": x["creator_user_id"],
                                },
                                {
                                    "$set": {
                                        "models.$.progress": "Completed",
                                    }
                                },
                            )
                        elif log["models"][0]["progress"] != "Failed":
                            await db["exports"].update_one(
                                {
                                    "userId": user.user_id,
                                    "timeInitiated": current_time,
                                    "models.model_id": x["model_id"],
                                    "models.creator_user_id": x["creator_user_id"],
                                },
                                {
                                    "$set": {
                                        "models.$.progress": "Completed",
                                    }
                                },
                            )
                    except Exception as err:
                        await db["exports"].update_one(
                            {
                                "userId": user.user_id,
                                "timeInitiated": current_time,
                                "models.model_id": x["model_id"],
                                "models.creator_user_id": x["creator_user_id"],
                            },
                            {
                                "$set": {
                                    "models.$.progress": "Failed",
                                },
                                "$push": {
                                    "models.$.reason": "Unexpected error",
                                },
                            },
                        )
                        print(
                            f"{Fore.YELLOW}WARNING{Fore.WHITE}:  Unexpected error was returned: {err}. Skipping...!"
                        )
                        continue
                await db["exports"].update_one(
                    {
                        "userId": user.user_id,
                        "timeInitiated": current_time,
                    },
                    {
                        "$set": {
                            "timeCompleted": str(datetime.datetime.now()),
                            "exportLocation": f"s3://{BUCKET_NAME}/exports/{current_time_stringified}",
                        }
                    },
                )
                print(f"{Fore.GREEN}INFO{Fore.WHITE}:\t  Models export task completed!")
    except Exception as err:
        print(f"{Fore.YELLOW}WARNING{Fore.WHITE}:  Models export task failed... Reason: {err}")
