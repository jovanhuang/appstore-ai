import base64
import json
from io import StringIO
from typing import List

from fastapi.responses import JSONResponse
from pydantic import validator

from .IOSchema import IOSchema
from .validators import check_files_exist


class MultipleMediaFileIO(IOSchema):
    media = List[str]

    _check_file_exists = validator("media", allow_reuse=True, each_item=True)(
        check_files_exist
    )

    def response(self) -> JSONResponse:
        """Stream back media files.
        :return: FileResponse
        :rtype: Response

        TODO: Consider other methods (e.g. zip, streaming response)
        """
        response = {"media": []}
        for file_path in self.media:
            # assume media is list of filenames
            with open(file_path, "rb") as f:
                response["media"].append(base64.b64encode(f.read()))
        return JSONResponse(response)
