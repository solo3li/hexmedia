import io
import boto3
from botocore.client import Config
from django.conf import settings

def get_s3_client():
    return boto3.client(
        's3',
        endpoint_url=settings.MINIO_ENDPOINT,
        aws_access_key_id=settings.MINIO_ACCESS_KEY,
        aws_secret_access_key=settings.MINIO_SECRET_KEY,
        config=Config(signature_version='s3v4'),
        region_name='us-east-1'
    )

def ensure_bucket_exists():
    s3 = get_s3_client()
    try:
        s3.create_bucket(Bucket=settings.MINIO_BUCKET)
    except Exception:
        pass
    try:
        import json
        policy = {
            'Version': '2012-10-17',
            'Statement': [{
                'Sid': 'PublicReadGetObject',
                'Effect': 'Allow',
                'Principal': '*',
                'Action': ['s3:GetObject'],
                'Resource': [f'arn:aws:s3:::{settings.MINIO_BUCKET}/*']
            }]
        }
        s3.put_bucket_policy(Bucket=settings.MINIO_BUCKET, Policy=json.dumps(policy))
    except Exception:
        pass

def upload_bytes(file_bytes: bytes, object_name: str, content_type: str = "audio/wav") -> str:
    ensure_bucket_exists()
    s3 = get_s3_client()
    s3.upload_fileobj(
        io.BytesIO(file_bytes),
        settings.MINIO_BUCKET,
        object_name,
        ExtraArgs={
            'ContentType': content_type,
            'ACL': 'public-read'
        }
    )
    # Return direct accessible URL (via public proxy or MinIO endpoint)
    # Using Django media proxy or direct MinIO endpoint
    return f"{settings.MINIO_PUBLIC_ENDPOINT}/{settings.MINIO_BUCKET}/{object_name}"

def upload_file_path(file_path: str, object_name: str, content_type: str = "application/octet-stream") -> str:
    ensure_bucket_exists()
    s3 = get_s3_client()
    with open(file_path, 'rb') as f:
        s3.upload_fileobj(
            f,
            settings.MINIO_BUCKET,
            object_name,
            ExtraArgs={
                'ContentType': content_type,
                'ACL': 'public-read'
            }
        )
    return f"{settings.MINIO_PUBLIC_ENDPOINT}/{settings.MINIO_BUCKET}/{object_name}"
