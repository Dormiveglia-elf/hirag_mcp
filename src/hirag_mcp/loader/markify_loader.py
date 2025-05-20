import time
from typing import List, Optional, Union

import requests
import tiktoken
from requests_toolbelt.multipart.encoder import MultipartEncoder


class MarkifyClient:
    def __init__(
        self,
        base_url: str = "http://markify:20926",
        timeout: int = 30,
        default_mode: str = "simple",
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.default_mode = default_mode
        self.session = requests.Session()

        retry_strategy = requests.adapters.Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST", "GET"],
        )
        adapter = requests.adapters.HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def create_job(
        self,
        file_path: str,
        mode: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> str:
        endpoint = f"{self.base_url}/api/jobs"
        # content type detection
        if not content_type:
            content_type = self._detect_mime_type(file_path)
        # request body
        multipart_data = MultipartEncoder(
            fields={
                "file": (file_path, open(file_path, "rb"), content_type),
                "mode": mode or self.default_mode,
            }
        )
        response = self.session.post(
            url=endpoint,
            data=multipart_data,
            headers={
                "Accept": "application/json",
                "Content-Type": multipart_data.content_type,
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()["job_id"]

    def get_job_status(self, job_id: str) -> dict:
        endpoint = f"{self.base_url}/api/jobs/{job_id}"
        try:
            response = self.session.get(
                url=endpoint,
                headers={"Accept": "application/json"},
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()

        except requests.HTTPError as e:
            if e.response.status_code == 404:
                raise ValueError("Job ID not found") from e
            raise

    def get_result(
        self, job_id: str, output_file: Optional[str] = None
    ) -> Union[str, None]:
        endpoint = f"{self.base_url}/api/jobs/{job_id}/result"
        try:
            response = self.session.get(
                url=endpoint, headers={"Accept": "text/markdown"}, timeout=self.timeout
            )
            response.raise_for_status()
            if output_file:
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(response.text)
                return None
            return response.text
        except requests.HTTPError as e:
            if e.response.status_code == 202:
                raise RuntimeError("Job still processing") from e
            raise

    def convert_pdf(
        self,
        file_path: str,
        mode: Optional[str] = None,
        poll_interval: int = 2,
        max_wait: int = 3600,
    ) -> str:
        start_time = time.time()
        job_id = self.create_job(file_path, mode)
        while True:
            if time.time() - start_time > max_wait:
                raise TimeoutError("Max wait time exceeded")
            status = self.get_job_status(job_id)
            if status["status"] == "completed":
                return self.get_result(job_id)
            elif status["status"] == "failed":
                raise RuntimeError(f"Job failed: {status.get('error')}")
            time.sleep(poll_interval)

    @staticmethod
    def _detect_mime_type(file_path: str) -> str:
        ext = file_path.split(".")[-1].lower()
        mime_map = {
            "pdf": "application/pdf",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "jpg": "image/jpeg",
            "png": "image/png",
            "zip": "application/zip",
            "txt": "text/plain",
            "csv": "text/csv",
            "text": "text/plain",
            "tsv": "text/tab-separated-values",
        }
        return mime_map.get(ext, "application/octet-stream")


markify_client = MarkifyClient(base_url="http://markify:20926")