from storages.backends.s3boto3 import S3Boto3Storage
from decouple import config

class StaticStorage(S3Boto3Storage):

    def __init__(self, *args, **kwargs):
        kwargs['custom_domain'] = config('AWS_CLOUDFRONT_DOMAIN')  
        kwargs['signature_version'] = "s3v4"
        kwargs['region_name'] = config('AWS_DEFAULT_REGION')
        kwargs['default_acl'] = "public-read"
        kwargs['location'] = "static"
        
        super(StaticStorage, self).__init__(*args, **kwargs)

    
class PublicMediaStorage(S3Boto3Storage):

    location = 'media'
    file_overwrite = False

    def __init__(self, *args, **kwargs):
        kwargs['custom_domain'] = config('AWS_CLOUDFRONT_DOMAIN')    
        kwargs['signature_version'] = "s3v4"
    
        super(PublicMediaStorage, self).__init__(*args, **kwargs)