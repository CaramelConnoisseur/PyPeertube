"""Functions for managing videos on Peertube."""

from contextlib import nullcontext
from datetime import datetime
from enum import Enum
from os.path import basename
from mimetypes import guess_type
from typing import Any, Dict, Optional, List, Union

from . import Account
from .channels import VideoChannel
from .client import ApiClient
from .exceptions import raise_api_bad_response_error


class Category(Enum):
    """Video Category"""

    MUSIC = 1
    FILMS = 2
    VEHICLES = 3
    ART = 4
    SPORTS = 5
    TRAVEL = 6
    GAMING = 7
    PEOPLE = 8
    COMEDY = 9
    ENTERTAINMENT = 10
    NEWS_POLITICS = 11
    HOW_TO = 12
    EDUCATION = 13
    ACTIVISM = 14
    SCIENCE_TECH = 15
    ANIMALS = 16
    KIDS = 17
    FOOD = 18


class CommentsPolicy(Enum):
    """Comments Policy"""

    ENABLED = 1
    DISABLED = 2
    REQUIRE_APPROVAL = 3


class Licence(Enum):
    """License applied to the video."""

    BY = 1
    BY_SA = 2
    BY_ND = 3
    BY_NC = 4
    BY_NC_SA = 5
    BY_NC_ND = 6
    PDD = 7


class Privacy(Enum):
    """The privacy setting of a video"""

    PUBLIC = 1
    """Public viewable"""

    UNLISTED = 2
    PRIVATE = 3
    INTERNAL = 4
    PASSWORD = 5


class VideoFile:  # pylint: disable=too-few-public-methods,too-many-instance-attributes
    """A file for a video on Peertube."""

    id: int
    magnet_uri: Optional[str]
    resolution: int
    size: int
    torrent_url: Optional[str]
    torrent_download_url: Optional[str]
    file_url: str
    playlist_url: Optional[str]
    file_download_url: str
    fps: int
    width: int
    height: int
    metadata_url: str
    has_audio: bool
    has_video: bool
    storage: int

    def __init__(self, input_dict: Dict[str, Any]):
        self.id = input_dict["id"]
        self.magnet_uri = input_dict["magnetUri"] if "magnetUri" in input_dict else None
        self.resolution = input_dict["resolution"]["id"]
        self.size = input_dict["size"]
        self.torrent_url = (
            input_dict["torrentUrl"] if "torrentUrl" in input_dict else None
        )
        self.torrent_download_url = (
            input_dict["torrentDownloadUrl"]
            if "torrentDownloadUrl" in input_dict
            else None
        )
        self.file_url = input_dict["fileUrl"]
        self.playlist_url = (
            input_dict["playlistUrl"] if "playlistUrl" in input_dict else None
        )
        self.file_download_url = input_dict["fileDownloadUrl"]
        self.fps = input_dict["fps"]
        self.width = input_dict["width"]
        self.height = input_dict["height"]
        self.metadata_url = input_dict["metadataUrl"]
        self.has_audio = input_dict["hasAudio"]
        self.has_video = input_dict["hasVideo"]
        self.storage = input_dict["storage"]

    def __repr__(self):
        return f"Video File: {self.id} - {self.file_url}"

    def __str__(self):
        return self.file_url


class StreamingPlaylist:  # pylint: disable=too-few-public-methods
    """A HLS playlist for a video on Peertube."""

    id: int
    type: int
    url: str
    segments_sha256_url: str
    files: List[VideoFile]
    redundancies: List[str]

    def __init__(self, input_dict: Dict[str, Any]):
        self.id = input_dict["id"]
        self.type = input_dict["type"]
        self.url = input_dict["playlistUrl"]
        self.segments_sha256_url = input_dict["segmentsSha256Url"]
        self.files = []
        for file in input_dict["files"]:
            self.files.append(VideoFile(file))
        self.redundancies = []
        for redundancy in input_dict["redundancies"]:
            self.redundancies.append(redundancy["baseUrl"])

    def __repr__(self):
        return f"Streaming Playlist: {self.id} - {self.url}"

    def __str__(self):
        return self.url


class VideoScheduledUpdate:  # pylint: disable=too-few-public-methods
    """A scheduled change of privacy for a video on Peertube."""

    update_at: datetime
    new_privacy_level: Privacy

    def __init__(self, input_dict: Dict[str, Union[int, str]]):
        self.update_at = input_dict["updateAt"]
        self.new_privacy_level = Privacy(input_dict["privacy"])

    def __repr__(self):
        return f"To {self.new_privacy_level.name} at {self.update_at}"


class VideoState(Enum):
    """The state of a video on Peertube."""

    PUBLISHED = 1
    TO_TRANSCODE = 2
    TO_IMPORT = 3
    WAITING_FOR_LIVE = 4
    LIVE_ENDED = 5
    TO_MOVE_TO_EXTERNAL_STORAGE = 6
    TRANSCODING_FAILED = 7
    TO_MOVE_TO_EXTERNAL_STORAGE_FAILED = 8
    TO_EDIT = 9
    TO_MOVE_TO_FILE_SYSTEM = 10
    TO_MOVE_TO_FILE_SYSTEM_FAILED = 11


class Video:  # pylint: disable=too-few-public-methods,too-many-instance-attributes
    """A video on Peertube."""

    id: int
    uuid: str
    short_uuid: str
    live: bool
    created_at: datetime
    published_at: datetime
    updated_at: datetime
    originally_published_at: datetime
    category: Optional[Category]
    licence: Licence
    language: str
    privacy: Privacy
    truncated_description: str
    duration: int
    aspect_ratio: float
    local: bool
    name: str
    thumbnail_path: str
    preview_path: str
    embed_path: str
    views: int
    likes: int
    dislikes: int
    comments: int
    nsfw: bool
    nsfw_flags: int
    nsfw_summary: Optional[str]
    wait_transcoding: Optional[bool]
    state: Optional[VideoState]
    scheduled_update: Optional[VideoScheduledUpdate]
    blocklisted: Optional[bool]
    blocklist_reason: Optional[str]
    owner: Account
    channel: VideoChannel
    viewers: int
    description: str
    support: Optional[str]
    tags: Optional[List[str]]
    comments_enabled: Optional[bool]
    comments_policy: Optional[CommentsPolicy]
    download_enabled: Optional[bool]
    input_file_updated_at: Optional[datetime]
    tracker_urls: Optional[List[str]]
    files: Optional[List[VideoFile]]
    streaming_playlists: Optional[List[StreamingPlaylist]]

    def __init__(
        self, input_dict: Dict[str, Any]
    ):  # pylint: disable=too-many-statements
        self.id = input_dict["id"]
        self.uuid = input_dict["uuid"]
        self.short_uuid = input_dict["shortUUID"]
        self.live = input_dict["isLive"]
        self.created_at = input_dict["createdAt"]
        self.published_at = input_dict["publishedAt"]
        self.updated_at = input_dict["updatedAt"]
        self.originally_published_at = input_dict["originallyPublishedAt"]
        self.category = (
            Category(input_dict["category"]["id"])
            if input_dict["category"]["id"] is not None
            else None
        )
        self.licence = Licence(input_dict["licence"]["id"])
        self.language = input_dict["language"]["id"]
        self.privacy = Privacy(input_dict["privacy"]["id"])
        self.truncated_description = input_dict["truncatedDescription"]
        self.duration = input_dict["duration"]
        self.aspect_ratio = input_dict["aspectRatio"]
        self.local = input_dict["isLocal"]
        self.name = input_dict["name"]
        self.thumbnail_path = input_dict["thumbnailPath"]
        self.preview_path = input_dict["previewPath"]
        self.embed_path = input_dict["embedPath"]
        self.views = input_dict["views"]
        self.likes = input_dict["likes"]
        self.dislikes = input_dict["dislikes"]
        self.comments = input_dict["comments"] if "comments" in input_dict else 0
        self.nsfw = input_dict["nsfw"]
        self.nsfw_flags = input_dict["nsfwFlags"] if "nsfwFlags" in input_dict else 0
        self.nsfw_summary = (
            input_dict["nsfwSummary"] if "nsfwSummary" in input_dict else None
        )
        self.wait_transcoding = (
            input_dict["waitTranscoding"] if "waitTranscoding" in input_dict else None
        )
        self.state = (
            VideoState(input_dict["state"]["id"]) if "state" in input_dict else None
        )
        self.scheduled_update = (
            VideoScheduledUpdate(input_dict["scheduledUpdate"])
            if "scheduledUpdate" in input_dict
            else None
        )
        self.blocklisted = (
            input_dict["blacklisted"] if "blacklisted" in input_dict else None
        )
        self.blocklist_reason = (
            input_dict["blacklistedReason"]
            if "blacklistedReason" in input_dict
            else None
        )
        self.owner = Account(input_dict["account"])
        self.channel = VideoChannel(input_dict["channel"])
        self.viewers = input_dict["viewers"]
        self.description = input_dict["description"]
        self.support = input_dict["support"] if "support" in input_dict else None
        self.tags = input_dict["tags"] if "tags" in input_dict else None
        self.comments_enabled = (
            input_dict["commentsEnabled"] if "commentsEnabled" in input_dict else None
        )
        self.comments_policy = (
            CommentsPolicy(input_dict["commentsPolicy"]["id"])
            if "commentsPolicy" in input_dict
            else None
        )
        self.download_enabled = (
            input_dict["downloadEnabled"] if "downloadEnabled" in input_dict else None
        )
        self.input_file_updated_at = (
            input_dict["inputFileUpdatedAt"]
            if "inputFileUpdatedAt" in input_dict
            else None
        )
        self.tracker_urls = (
            input_dict["trackerUrls"] if "trackerUrls" in input_dict else None
        )
        if "files" in input_dict:
            self.files = []
            for file in input_dict["files"]:
                self.files.append(VideoFile(file))
        else:
            self.files = None
        if "streamingPlaylists" in input_dict:
            self.streaming_playlists = []
            for playlist in input_dict["streamingPlaylists"]:
                self.streaming_playlists.append(StreamingPlaylist(playlist))
        else:
            self.streaming_playlists = None

    def __repr__(self):
        return f"Video: {self.uuid}"

    def __str__(self):
        return f"{self.name} ({self.uuid})"


class VideoEndpoints(Enum):
    """Endpoints for managing videos on Peertube."""

    VIDEO = "api/v1/videos/{id}"
    """Get a video"""

    UPLOAD_VIDEO = "api/v1/videos/upload"
    """Upload a new video"""

    VIDEO_SEARCH = "api/v1/search/videos"
    """Search for videos"""

    VIDEOS_IN_CHANNEL = "api/v1/video-channels/{channel}/videos"
    """Gets list of videos in a given channel"""


def delete_video(client: ApiClient, video_id: str):
    """Delete a video.

    Args:
        client (ApiClient): The authenticated client to use.
        short_uuid (str): The ShortUUID of the video to delete.
    """

    response = client.session.delete(
        client.base_url + VideoEndpoints.VIDEO.value.format(id=video_id),
        timeout=5,
    )
    if response.status_code != 204:
        raise_api_bad_response_error(response)


def get_video(  # pylint: disable=inconsistent-return-statements
    client: ApiClient, video_id: str
) -> Video:
    """Get details about a video on Peertube.

    Args:
        client (ApiClient): The authenticated client to use.
        video_id (str): The id, UUID, or ShortUUID of the video.

    Returns:
        Video: The details of the video.
    """

    response = client.session.get(
        client.base_url + VideoEndpoints.VIDEO.value.format(id=video_id),
        timeout=5,
    )
    if response.status_code == 200:
        return Video(response.json())

    raise_api_bad_response_error(response)


def get_videos_in_channel(client: ApiClient, channel: str) -> List[Video]:
    """Get a list of videos in a channel.

    Args:
        client (ApiClient): The authenticated client to use.
        channel (str): The name of the channel to look in.

    Returns:
        List[Video]: The videos in the specified channel.
    """

    start = 0
    total = -1
    videos: List[Video] = []
    while len(videos) != total:
        response = client.session.get(
            client.base_url
            + VideoEndpoints.VIDEOS_IN_CHANNEL.value.format(channel=channel),
            params={"count": 100, "start": start},
            timeout=5,
        )
        if response.status_code != 200:
            raise_api_bad_response_error(response)
        start = start + 100
        body = response.json()
        total = body["total"]
        for video in body["data"]:
            videos.append(Video(video))
    return videos


def search_videos(  # pylint: disable=:too-many-arguments,too-many-locals,too-many-branches
    client: ApiClient,
    search: str,
    *,
    category: Optional[Union[Category, List[Category]]] = None,
    duration_max: Optional[int] = None,
    duration_min: Optional[int] = None,
    include_nsfw: Optional[bool] = None,
    live: Optional[bool] = None,
    published_before: Optional[datetime] = None,
    published_after: Optional[datetime] = None,
    tags_and: Optional[Union[str, List[str]]] = None,
    tags_or: Optional[Union[str, List[str]]] = None,
) -> List[Video]:
    """Search for videos on Peertube.

    Args:
        client (ApiClient): The authenticated client to use.
        search (str): The search string.
        category (Category | List[Category], optional): The category or categories to look in.
            Defaults to None.
        duration_max (int, optional): The maximum duration in seconds. Defaults to None.
        duration_min (int, optional): The minimum duration in seconds. Defaults to None.
        include_nsfw (bool, optional): Whether to include NSFW content. Defaults to None.
        live (bool, optional): Limit to Live or VOD videos. Defaults to None.
        published_before (datetime, optional): Limit to videos published before date time.
            Defaults to None.
        published_after (datetime, optional): Limit to video published after date time.
            Defaults to None.
        tags_and (str | List[str], optional): Limit to videos with all these tags.
            Defaults to None.
        tags_or (str | List[str], optional): Limit to videos with any of these tags.
            Defaults to None.

    Returns:
        List[Video]: The matching videos.
    """

    search_parameters: Dict[str, Any] = {
        "count": 100,
        "search": search,
        "sort": "publishedAt",
        "start": 0,
    }
    if category is not None:
        if isinstance(category, Category):
            search_parameters["categoryOneOf"] = category.value
        else:
            search_parameters["categoryOneOf"] = []
            for cat in category:
                search_parameters["categoryOneOf"].append(cat.value)
    if duration_max is not None:
        search_parameters["durationMax"] = duration_max
    if duration_min is not None:
        search_parameters["durationMin"] = duration_min
    if include_nsfw is not None:
        search_parameters["nsfw"] = include_nsfw
    if live is not None:
        search_parameters["isLive"] = live
    if published_after is not None:
        search_parameters["startDate"] = published_before.isoformat()
    if published_before is not None:
        search_parameters["endDate"] = published_after.isoformat()
    if tags_and is not None:
        search_parameters["tagsAllOf"] = tags_and
    if tags_or is not None:
        search_parameters["tagsOneOf"] = tags_or

    total = -1
    matches: List[Video] = []
    while len(matches) != total:
        response = client.session.get(
            client.base_url + VideoEndpoints.VIDEO_SEARCH.value,
            params=search_parameters,
            timeout=10,
        )
        if response.status_code == 200:
            body = response.json()
            total = body["total"]
            for video in body["data"]:
                matches.append(Video(video))
        else:
            raise_api_bad_response_error(response)

        search_parameters["start"] = search_parameters["start"] + 100

    return matches


def upload_video(  # pylint: disable=inconsistent-return-statements,too-many-arguments,too-many-branches,too-many-locals
    client: ApiClient,
    channel_id: int,
    name: str,
    video_file: str,
    *,
    category: Optional[Category] = None,
    comments_policy: Optional[CommentsPolicy] = None,
    description: Optional[str] = None,
    download_enabled: Optional[bool] = None,
    generate_transcription: Optional[bool] = None,
    language: Optional[str] = None,
    licence: Optional[Licence] = None,
    nsfw: Optional[bool] = None,
    originally_published: Optional[datetime] = None,
    preview_file: Optional[str] = None,
    privacy: Optional[Privacy] = None,
    support: Optional[str] = None,
    tags: Optional[List[str]] = None,
    thumbnail_file: Optional[str] = None,
    video_passwords: Optional[List[str]] = None,
    wait_transcoding: Optional[bool] = None,
) -> Video:
    """Upload a video to Peertube.

    Args:
        too (ApiClient): The authenticated client to use.
        too (_type_): _description_
        channel_id (int): The numeric identifier of the channel to upload to.
        name (str): The title for the new video.
        video_file (str): The path to the video to upload.
        category (Category, optional): The category to associated to the video. Defaults to None.
        comments_policy (CommentsPolicy, optional): The comments policy to apply to the video.
            Defaults to None.
        description (str, optional): The description to set on the video. Defaults to None.
        download_enabled (bool, optional): Whether to allow downloading of the video.
            Defaults to None.
        generate_transcription (bool, optional): Whether to generate subtitles for the video.
            Defaults to None.
        language (str, optional): The two letter language code for the video. Defaults to None.
        licence (Licence, optional): The license to apply to the video. Defaults to None.
        nsfw (bool, optional): Whether the video contains Not Safe For Work (NSFW) themes.
            Defaults to None.
        originally_published (datetime, optional): When the video was originally published.
            Defaults to None.
        preview_file (str, optional): The image to show on the video page before playing,
            will be stretched to the video aspect ratio. Defaults to None.
        privacy (Privacy, optional): The privacy level to apply to the video. Defaults to None.
        support (str, optional): The support message to associate with the video. Defaults to None.
        tags (List[str], optional): The tags to apply to the video. Defaults to None.
        thumbnail_file (str, optional): The image to show on channel listings and search results,
            will be stretched to a 9:5 aspect ratio. Defaults to None.
        video_passwords (List[str], optional): The passwords to accept for the video.
            Defaults to None.
        wait_transcoding (bool, optional): Whether to wait for transcoding to finish before
            publishing the video. Defaults to None.

    Returns:
        Video: The uploaded video.
    """

    metadata = {"channelId": channel_id, "name": name[:120]}
    if category is not None:
        metadata["category"] = category.value
    if comments_policy is not None:
        metadata["commentsPolicy"] = comments_policy.value
    if description is not None:
        metadata["description"] = description
    if download_enabled is not None:
        metadata["downloadEnabled"] = download_enabled
    if generate_transcription is not None:
        metadata["generateTranscription"] = generate_transcription
    if language is not None:
        metadata["language"] = language
    if licence is not None:
        metadata["licence"] = licence.value
    if nsfw is not None:
        metadata["nsfw"] = nsfw
    if originally_published is not None:
        metadata["originallyPublishedAt"] = originally_published.strftime(
            "%Y-%m-%d %H:%M"
        )
    if privacy is not None:
        metadata["privacy"] = privacy.value
    if support is not None:
        metadata["support"] = support
    if tags is not None:
        metadata["tags"] = tags
    if video_passwords is not None:
        metadata["videoPasswords"] = video_passwords
    if wait_transcoding is not None:
        metadata["waitTranscoding"] = wait_transcoding

    with open(video_file, "br") as video_f, (
        open(preview_file, "br") if preview_file is not None else nullcontext()
    ) as preview_f, (
        open(thumbnail_file, "br") if thumbnail_file is not None else nullcontext()
    ) as thumbnail_f:
        files = {
            "videofile": (
                basename(video_file),
                video_f,
                guess_type(video_file)[0],
            )
        }
        if preview_file is not None:
            files["previewfile"] = (
                basename(preview_file),
                preview_f,
                guess_type(preview_file)[0],
            )
        if thumbnail_file is not None:
            files["thumbnailfile"] = (
                basename(thumbnail_file),
                thumbnail_f,
                guess_type(thumbnail_file)[0],
            )

        response = client.session.post(
            client.base_url + VideoEndpoints.UPLOAD_VIDEO.value,
            data=metadata,
            files=files,
            timeout=900,
        )
    if response.status_code == 200:
        return get_video(client, response.json()["video"]["id"])

    raise_api_bad_response_error(response)


def update_video():
    """Not yet implemented"""

    raise NotImplementedError()
