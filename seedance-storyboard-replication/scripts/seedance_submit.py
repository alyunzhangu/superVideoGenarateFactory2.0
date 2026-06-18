from __future__ import annotations

import argparse
import json
from pathlib import Path
import time
from typing import Any, Callable
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from config import DEFAULT_ENV_FILE, load_settings


CREATE_PATH = "/api/open-api/v1/seedance/videos"
QUERY_PATH = "/api/open-api/v1/videos/{task_id}"
RUNNING = {"queued", "processing"}
FINAL = {"completed", "failed"}
SUCCESS_CODES = {0, "0", 200, "200", 20000, "20000"}


class PayloadError(ValueError):
    pass


class SeedanceApiError(RuntimeError):
    pass


class TaskFailedError(SeedanceApiError):
    pass


class PollTimeoutError(SeedanceApiError):
    pass


def _require_public_https_urls(urls: list[str]) -> None:
    for url in urls:
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.netloc:
            raise PayloadError("media URLs must be public HTTPS URLs")


def build_payload(
    prompt: str,
    duration: int,
    ratio: str,
    image_urls: list[str],
    reference_video_urls: list[str],
) -> dict[str, Any]:
    normalized_prompt = prompt.strip()
    if not normalized_prompt or len(normalized_prompt) > 5000:
        raise PayloadError("prompt must contain 1-5000 characters")
    if not 1 <= int(duration) <= 15:
        raise PayloadError("duration must be between 1 and 15 seconds")
    if ratio not in {"16:9", "9:16", "1:1"}:
        raise PayloadError("ratio must be one of 16:9, 9:16, 1:1")
    if len(image_urls) > 4:
        raise PayloadError("seedance2.0-fast-md accepts at most 4 images")
    _require_public_https_urls([*image_urls, *reference_video_urls])
    return {
        "model": "seedance2.0-fast-md",
        "prompt": normalized_prompt,
        "duration": int(duration),
        "ratio": ratio,
        "images": list(image_urls),
        "reference_videos": list(reference_video_urls),
    }


def _is_success_code(code: Any) -> bool:
    return code is None or code in SUCCESS_CODES


def _data_or_raise(response: dict[str, Any]) -> dict[str, Any]:
    if not _is_success_code(response.get("code")):
        message = response.get("message") or response.get("msg") or "JimmyAI request failed"
        raise SeedanceApiError(str(message))
    data = response.get("data", {})
    if not isinstance(data, dict):
        raise SeedanceApiError("JimmyAI response data must be an object")
    return data


def parse_task_id(response: dict[str, Any]) -> str:
    data = _data_or_raise(response)
    task_id = data.get("task_id") or data.get("id") or response.get("task_id")
    if not task_id:
        raise SeedanceApiError("JimmyAI response did not include task_id")
    return str(task_id)


def _split_response(raw_response: Any) -> tuple[int, dict[str, Any]]:
    if isinstance(raw_response, tuple) and len(raw_response) == 2:
        status_code, payload = raw_response
        return int(status_code), dict(payload)
    return 200, dict(raw_response)


def _read_json_bytes(payload: bytes) -> dict[str, Any]:
    if not payload:
        return {}
    return json.loads(payload.decode("utf-8"))


def _urllib_request_json(
    *,
    method: str,
    url: str,
    headers: dict[str, str],
    json_body: dict[str, Any] | None,
    timeout: float,
) -> tuple[int, dict[str, Any]]:
    body = None
    if json_body is not None:
        body = json.dumps(json_body, ensure_ascii=False).encode("utf-8")
    request = Request(url, data=body, headers=headers, method=method)
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.status, _read_json_bytes(response.read())
    except HTTPError as exc:
        return exc.code, _read_json_bytes(exc.read())


def _download_file(url: str, output_path: Path) -> None:
    request = Request(url, method="GET")
    with urlopen(request, timeout=120) as response:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(response.read())


class JimmyAiClient:
    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = "https://www.jimmyai.cn",
        request_json: Callable[..., Any] | None = None,
        download: Callable[[str, Path], None] | None = None,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
        request_timeout: float = 60,
        max_attempts: int = 3,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.request_json = request_json or _urllib_request_json
        self.download = download or _download_file
        self.sleep = sleep
        self.clock = clock
        self.request_timeout = request_timeout
        self.max_attempts = max_attempts
        self.last_response: dict[str, Any] = {}
        self.last_status_response: dict[str, Any] = {}

    def create_video(self, payload: dict[str, Any]) -> str:
        response = self._request("POST", CREATE_PATH, payload)
        self.last_response = response
        return parse_task_id(response)

    def get_status(self, task_id: str) -> dict[str, Any]:
        response = self._request("GET", QUERY_PATH.format(task_id=task_id), None)
        self.last_status_response = response
        return response

    def download_video(self, video_url: str, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        self.download(video_url, output_path)

    def _request(
        self,
        method: str,
        path: str,
        json_body: dict[str, Any] | None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        delay = 1.0
        for attempt in range(1, self.max_attempts + 1):
            status_code, payload = _split_response(
                self.request_json(
                    method=method,
                    url=url,
                    headers=headers,
                    json_body=json_body,
                    timeout=self.request_timeout,
                )
            )
            if status_code == 429 or 500 <= status_code < 600:
                if attempt == self.max_attempts:
                    raise SeedanceApiError(f"JimmyAI request failed with HTTP {status_code}")
                self.sleep(delay)
                delay = min(delay * 2, 30)
                continue
            if status_code in {401, 403}:
                raise SeedanceApiError(f"JimmyAI request rejected with HTTP {status_code}; check JIMMYAI_API_KEY")
            if status_code >= 400:
                message = payload.get("message") or payload.get("msg") or "request failed"
                raise SeedanceApiError(f"JimmyAI request failed with HTTP {status_code}: {message}")
            return payload
        raise SeedanceApiError("JimmyAI request failed")


def poll_task(
    client: JimmyAiClient,
    task_id: str,
    *,
    timeout: float = 1800,
    poll_interval: float = 20,
) -> str:
    deadline = client.clock() + timeout
    while True:
        response = client.get_status(task_id)
        data = _data_or_raise(response)
        status = str(data.get("status", "")).lower()
        if status == "completed":
            result = data.get("result") or {}
            video_url = result.get("video_url")
            if not video_url:
                raise SeedanceApiError("completed task did not include data.result.video_url")
            return str(video_url)
        if status == "failed":
            message = data.get("message") or data.get("error") or response.get("message") or "Seedance task failed"
            raise TaskFailedError(str(message))
        if status not in RUNNING:
            raise SeedanceApiError(f"unknown Seedance task status: {status or '<empty>'}")
        if client.clock() >= deadline:
            raise PollTimeoutError(f"Seedance task {task_id} timed out")
        client.sleep(poll_interval)


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Submit or resume JimmyAI Seedance 2.0 Fast MD video tasks.")
    parser.add_argument("--prompt-file", type=Path, required=True)
    parser.add_argument("--image-url", action="append", default=[])
    parser.add_argument("--reference-video-url", action="append", default=[])
    parser.add_argument("--duration", type=int, required=True)
    parser.add_argument("--ratio", default="9:16")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--poll", action="store_true")
    parser.add_argument("--resume-task-id")
    parser.add_argument("--timeout", type=float, default=1800)
    parser.add_argument("--poll-interval", type=float, default=20)
    args = parser.parse_args()

    settings = load_settings(args.env_file)
    settings.require_jimmy()
    prompt = args.prompt_file.read_text(encoding="utf-8")
    payload = build_payload(
        prompt,
        args.duration,
        args.ratio,
        args.image_url,
        args.reference_video_url,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(args.output_dir / "request.redacted.json", payload)
    if args.dry_run:
        _write_json(args.output_dir / "create_response.json", {"status": "dry_run"})
        _write_json(args.output_dir / "status.json", {"status": "dry_run"})
        return 0

    client = JimmyAiClient(settings.jimmy_api_key, base_url=settings.jimmy_base_url)
    if args.resume_task_id:
        task_id = args.resume_task_id
        _write_json(args.output_dir / "create_response.json", {"resume_task_id": task_id})
    else:
        task_id = client.create_video(payload)
        _write_json(args.output_dir / "create_response.json", client.last_response)
    (args.output_dir / "task_id.txt").write_text(task_id, encoding="utf-8")

    if args.poll:
        video_url = poll_task(
            client,
            task_id,
            timeout=args.timeout,
            poll_interval=args.poll_interval,
        )
        _write_json(args.output_dir / "status.json", client.last_status_response)
        client.download_video(video_url, args.output_dir / "result.mp4")
    else:
        _write_json(args.output_dir / "status.json", {"task_id": task_id, "status": "created"})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
