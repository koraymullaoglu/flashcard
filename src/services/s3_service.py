import json
from dataclasses import dataclass
from datetime import datetime, timezone

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from models import Deck
from services.errors import ExternalServiceError


@dataclass(frozen=True)
class S3ExportResult:
    bucket: str
    key: str
    etag: str | None

    @property
    def s3_uri(self) -> str:
        return f"s3://{self.bucket}/{self.key}"

    def to_dict(self) -> dict[str, str | None]:
        return {
            "bucket": self.bucket,
            "key": self.key,
            "etag": self.etag,
            "s3_uri": self.s3_uri,
        }


class S3Service:
    def __init__(
        self,
        bucket_name: str,
        region: str,
        endpoint_url: str | None = None,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
        export_prefix: str = "exports",
    ) -> None:
        self.bucket_name = bucket_name
        self.region = region
        self.export_prefix = export_prefix.strip("/") or "exports"
        self.client = boto3.client(
            "s3",
            region_name=region,
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
        )

    def export_deck(self, deck: Deck, user_id: int) -> S3ExportResult:
        exported_at = datetime.now(timezone.utc)
        payload = {
            "exported_at": exported_at.isoformat(),
            "user_id": user_id,
            "deck": deck.to_dict(include_flashcards=True),
        }
        key = (
            f"{self.export_prefix}/user-{user_id}/deck-{deck.id}-"
            f"{exported_at.strftime('%Y%m%dT%H%M%SZ')}.json"
        )
        body = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")

        try:
            self._ensure_bucket_exists()
            response = self.client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=body,
                ContentType="application/json",
            )
        except (BotoCoreError, ClientError) as exc:
            raise ExternalServiceError("S3 export islemi basarisiz oldu.") from exc

        return S3ExportResult(
            bucket=self.bucket_name,
            key=key,
            etag=response.get("ETag", "").strip('"') or None,
        )

    def _ensure_bucket_exists(self) -> None:
        try:
            self.client.head_bucket(Bucket=self.bucket_name)
            return
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code", "")
            if error_code not in {"404", "NoSuchBucket"}:
                raise

        params: dict[str, object] = {"Bucket": self.bucket_name}
        if self.region != "us-east-1":
            params["CreateBucketConfiguration"] = {"LocationConstraint": self.region}
        self.client.create_bucket(**params)
