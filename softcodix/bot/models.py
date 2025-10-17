from django.db import models

class PageContent(models.Model):
    url = models.URLField(max_length=500, unique=True)   # store full URL
    page = models.CharField(max_length=200, blank=True)  # optional path name
    title = models.CharField(max_length=255, blank=True, null=True)
    content = models.TextField()
    last_scraped = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.url


