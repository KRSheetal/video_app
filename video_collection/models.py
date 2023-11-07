from urllib import parse
from django.db import models
from django.core.exceptions import ValidationError

# Create your models here.

# beginning of the model. Adding all the required datatypes on web page
class Video(models.Model):
    name = models.CharField(max_length=200)
    url = models.CharField(max_length=400)
    notes = models.TextField(blank=True, null=True)
    video_id = models.CharField(max_length=40, unique=True) # display video's frame. max_lenght and unique to avoid duplicate videos

    def save(self, *args, **kwargs):
        # extract video ID from youtube url
        # if not self.url.startswith('https://www.youtube.com/watch'): # checks is the url is a youtube url
        #     raise ValidationError(f'Not a YouTube URL {self.url}')        

# split the url to pieces to validate
        url_components = parse.urlparse(self.url)  

        if url_components.scheme != 'https':
            raise ValidationError(f'Not a YouTube URL {self.url}')
        
        if url_components.netloc != 'www.youtube.com':
            raise ValidationError(f'Not a YouTube URL {self.url}')
        
        if url_components.path != '/watch':
            raise ValidationError(f'Not a YouTube URL {self.url}')

        query_string = url_components.query
        if not query_string:
            raise ValidationError(f'Invalid YouTube URL {self.url}')
        parameters = parse.parse_qs(query_string, strict_parsing=True)
        v_parameters_list = parameters.get('v') # return None if no key found, e.g abc = 1234
        if not v_parameters_list: # checking if None or empty list
            raise ValidationError(f'Invalid YouTube URL, missing parameters {self.url}')
        self.video_id = v_parameters_list[0]  # string

        super().save(*args, **kwargs)


    def __str__(self) -> str:
        return f'ID: {self.pk}, Name: {self.name}, URL: {self.url}, Video ID: {self.video_id}, Notes:{self.notes[:200]}'

