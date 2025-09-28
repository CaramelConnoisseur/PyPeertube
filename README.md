# PyPeertube

Python module to interact with a Peertube instance's API.

```python
from pypeertube.client import ApiClient
from pypeertube.videos import search_videos

PEERTUBE_URL = "https://my.peertube.tld"
PEERTUBE_USERNAME = "my_username"
PEERTUBE_PASSWORD = "my_password"
SEARCH_STRING = "Puppy"
SEARCH_TAGS = ["animal", "dog"]

with ApiClient(PEERTUBE_URL, PEERTUBE_USERNAME, PEERTUBE_PASSWORD) as client:
    for video in search_videos(client, SEARCH_STRING, tags_or=SEARCH_TAGS):
        print(f"{video.name}: {client.base_url}/w/{video.short_uuid}")
```
