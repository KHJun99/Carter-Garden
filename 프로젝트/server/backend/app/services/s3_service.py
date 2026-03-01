import boto3
from botocore.exceptions import NoCredentialsError
from flask import current_app

class S3Service:
    def __init__(self):
        self.s3 = boto3.client(
            's3',
            aws_access_key_id=current_app.config['AWS_ACCESS_KEY_ID'],
            aws_secret_access_key=current_app.config['AWS_SECRET_ACCESS_KEY'],
            region_name=current_app.config['AWS_REGION']
        )
        self.bucket = current_app.config['AWS_BUCKET_NAME']

    def upload_file(self, file_obj, object_name=None):
        if object_name is None:
            object_name = file_obj.filename

        try:
            self.s3.upload_fileobj(file_obj, self.bucket, object_name)
            url = f"https://{self.bucket}.s3.{current_app.config['AWS_REGION']}.amazonaws.com/{object_name}"
            return url
        except NoCredentialsError:
            print("Credentials not available")
            return None
        except Exception as e:
            print(f"Error uploading file: {e}")
            return None

def get_s3_service():
    return S3Service()
