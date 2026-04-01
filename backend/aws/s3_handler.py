import os
from dotenv import load_dotenv

try:
    import boto3
except Exception:
    boto3 = None

load_dotenv()

# ---------- S3 Client ----------

if boto3 is not None:
    s3_client = boto3.client(
        "s3",
        region_name=os.getenv("AWS_REGION", "ap-south-1"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    )
else:
    s3_client = None

BUCKET = os.getenv("S3_BUCKET", "omnivoice-demo")
REGION = os.getenv("AWS_REGION", "ap-south-1")


def upload_audio(audio_bytes: bytes, session_id: str) -> str:
    """
    Upload audio bytes to S3.
    Key pattern: audio/{session_id}.wav
    Returns: S3 URL string
    """
    key = f"audio/{session_id}.wav"

    if s3_client is None:
        return f"s3://mock/{key}"

    s3_client.put_object(
        Bucket=BUCKET,
        Key=key,
        Body=audio_bytes,
        ContentType="audio/wav",
        ServerSideEncryption="AES256",
    )

    s3_url = f"https://{BUCKET}.s3.{REGION}.amazonaws.com/{key}"
    return s3_url


def upload_pdf(pdf_bytes: bytes, session_id: str) -> str:
    """
    Upload PDF bytes to S3.
    Key pattern: prescriptions/{session_id}.pdf
    Returns: S3 URL string (CloudFront URL is built in approve.py)
    """
    key = f"prescriptions/{session_id}.pdf"

    if s3_client is None:
        return f"s3://mock/{key}"

    s3_client.put_object(
        Bucket=BUCKET,
        Key=key,
        Body=pdf_bytes,
        ContentType="application/pdf",
        ServerSideEncryption="AES256",
    )

    s3_url = f"https://{BUCKET}.s3.{REGION}.amazonaws.com/{key}"
    return s3_url


# ---------- Quick Test ----------
# Run: python aws/s3_handler.py
# Expected: prints two S3 URLs

if __name__ == "__main__":
    print("Testing S3 uploads...\n")

    dummy_audio = b"RIFF....WAVEfmt " + b"\x00" * 100
    dummy_pdf   = b"%PDF-1.4 mock content"

    audio_url = upload_audio(dummy_audio, "test-session-001")
    print(f"Audio uploaded:\n  {audio_url}\n")

    pdf_url = upload_pdf(dummy_pdf, "test-session-001")
    print(f"PDF uploaded:\n  {pdf_url}\n")

    print("S3 test complete.")