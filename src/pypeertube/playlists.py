"""Functions for managing playlists on Peertube."""

from contextlib import nullcontext
from datetime import datetime
from enum import Enum
from io import BufferedReader
from os.path import basename
from mimetypes import guess_type
from typing import Any, Dict, Optional, List, Literal, Tuple, Union

from . import Account
from .channels import VideoChannel
from .client import ApiClient
from .exceptions import raise_api_bad_response_error
from .videos import Privacy, Video


class PlaylistType(Enum):
    """The type of playlist this is."""

    REGULAR = 1
    WATCH_LATER = 2


class PlaylistVideo:
    """A video within a playlist on Peertube."""

    id: int
    position: int
    start_timestamp: Optional[int]
    stop_timestamp: Optional[int]
    video: Video

    def __init__(self, input_dict: Dict[str, Any]):
        self.id = input_dict["id"]
        self.position = input_dict["position"]
        self.start_timestamp = input_dict["startTimestamp"]
        self.stop_timestamp = input_dict["stopTimestamp"]
        self.video = Video(input_dict["video"])

    def __repr__(self):
        return f"Playlist Video: {self.id}"

    def __str__(self):
        return f"{self.id} ({self.video.name})"


class PlaylistEndpoints(Enum):
    """Endpoints for managing playlists on Peertube."""

    PLAYLIST = "api/v1/video-playlists/{playlist_id}"
    """Gets/updates a playlist"""

    PLAYLIST_ITEM = "api/v1/video-playlists/{playlist_id}/videos/{playlist_item_id}"
    """Removes a video from a playlist"""

    PLAYLISTS = "api/v1/video-playlists"
    """Gets all playlists on the instance"""

    PLAYLISTS_IN_ACCOUNT = "api/v1/accounts/{account_name}/video-playlists"
    """Gets list of playlists in a given account"""

    PLAYLISTS_IN_CHANNEL = "api/v1/video-channels/{channel}/video-playlists"
    """Gets list of playlists in a given channel"""

    VIDEOS_IN_PLAYLIST = "api/v1/video-playlists/{playlist_id}/videos"
    """Gets list of videos within a playlist"""


# pylint: disable=too-many-instance-attributes
class Playlist:
    """A playlist of videos on Peertube"""

    id: int
    uuid: str
    short_uuid: str
    channel_position: Optional[int]
    channel: Optional[VideoChannel]
    created_at: datetime
    description: str
    display_name: str
    embed_path: str
    is_local: bool
    owner: Account
    privacy: Privacy
    thumbnail_path: str
    type: PlaylistType
    updated_at: datetime
    url: str
    videos_length: int
    videos: List[PlaylistVideo]

    def __init__(self, client: ApiClient, input_dict: Dict[str, Any]):
        self.id = input_dict["id"]
        self.uuid = input_dict["uuid"]
        self.short_uuid = input_dict["shortUUID"]
        self.channel = (
            VideoChannel(input_dict["videoChannel"])
            if input_dict["videoChannel"] is not None
            else None
        )
        self.channel_position = input_dict["videoChannelPosition"]
        self.created_at = input_dict["createdAt"]
        self.description = input_dict["description"]
        self.display_name = input_dict["displayName"]
        self.embed_path = input_dict["embedPath"]
        self.is_local = input_dict["isLocal"]
        self.owner = Account(input_dict["ownerAccount"])
        self.privacy = Privacy(input_dict["privacy"]["id"])
        self.thumbnail_path = input_dict["thumbnailPath"]
        self.type = PlaylistType(input_dict["type"]["id"])
        self.updated_at = input_dict["updatedAt"]
        self.url = input_dict["url"]
        self.videos_length = input_dict["videosLength"]
        self.videos = get_videos_in_playlist(client, self.id)

    def __repr__(self):
        return f"Playlist: {self.short_uuid}"

    def __str__(self):
        return f"{self.display_name} ({self.short_uuid})"


def add_video_to_playlist(
    client: ApiClient,
    playlist_id: int,
    video_id: Union[int, str],
    *,
    start: Optional[int] = None,
    end: Optional[int] = None,
) -> Literal[True]:
    """Add a video to a playlist.

    Args:
        client (ApiClient): The client to use to talk to the API.
        playlist_id (int): The numeric ID of the playlist to add to.
        video_id (Union[int, str]): The numeric ID, UUID or Short UUID of the video to add.
        start (int, optional): The start second of the sub-clip to add. Defaults to None.
        end (int, optional): The end second of the sub-clip to add. Defaults to None.

    Returns:
        True: If the video is added successfully.
    """

    data = {"videoId": video_id}
    if start is not None:
        data["startTimestamp"] = start
    if end is not None:
        data["stopTimestamp"] = end

    response = client.session.post(
        client.base_url
        + PlaylistEndpoints.VIDEOS_IN_PLAYLIST.value.format(playlist_id=playlist_id),
        data=data,
        timeout=30,
    )

    if response.status_code != 200:
        raise_api_bad_response_error(response)

    return True


# pylint: disable=too-many-arguments,too-many-positional-arguments
def create_playlist(
    client: ApiClient,
    channel_id: int,
    display_name: str,
    description: Optional[str] = None,
    privacy: Privacy = Privacy.PUBLIC,
    thumbnail_file: Optional[str] = None,
) -> Playlist:
    """Create a new playlist.

    Args:
        client (ApiClient): The client to use to talk to the API.
        channel_id (int): The numeric ID of the target channel to create the playlist in.
        display_name (str): The name of the new playlist.
        description (str, optional): A description of the new playlist. Defaults to None.
        privacy (Privacy, optional): The privacy level of the new playlist. Defaults to PUBLIC.
        thumbnail_file (str, optional): The path to a thumbnail for the playlist. Defaults to None.

    Returns:
        Playlist: The newly created playlist.
    """

    data: Dict[str, Union[int, str]] = {
        "videoChannelId": channel_id,
        "displayName": display_name[:120],
        "privacy": privacy.value,
    }
    if description is not None:
        data["description"] = description[:1000]

    files: Dict[str, Tuple[str, BufferedReader, Optional[str]]] = {}

    with (
        open(thumbnail_file, "br") if thumbnail_file is not None else nullcontext()
    ) as thumbnail_f:
        if thumbnail_file is not None:
            files["thumbnailfile"] = (  # type: ignore
                basename(thumbnail_file),
                thumbnail_f,
                guess_type(thumbnail_file)[0],
            )

        response = client.session.post(
            client.base_url + PlaylistEndpoints.PLAYLISTS.value,
            data=data,
            files=files,  # pyright: ignore[reportArgumentType]
            timeout=30,
        )

    if response.status_code != 200:
        raise_api_bad_response_error(response)

    return get_playlist(client, response.json()["videoPlaylist"]["id"])


def delete_playlist(client: ApiClient, playlist_id: int) -> Literal[True]:
    """Delete a playlist.

    Args:
        client (ApiClient): The client to use to talk to the API.
        playlist_id (int): The numeric ID of the playlist.

    Returns:
        True: If the playlist was deleted.
    """

    response = client.session.delete(
        client.base_url
        + PlaylistEndpoints.PLAYLIST.value.format(playlist_id=playlist_id),
        timeout=10,
    )
    if response.status_code != 200:
        raise_api_bad_response_error(response)
    return True


def get_playlist(client: ApiClient, playlist_id: int) -> Playlist:
    """Get a playlist.

    Args:
        client (ApiClient): The client to use to talk to the API.
        playlist_id (int): The numeric ID of the playlist.
        load_videos (bool, optional): Whether to load the list of videos in the playlist.
            Defaults to False.

    Returns:
        Playlist: The requested playlist.
    """

    response = client.session.get(
        client.base_url
        + PlaylistEndpoints.PLAYLIST.value.format(playlist_id=playlist_id),
        timeout=10,
    )
    if response.status_code != 200:
        raise_api_bad_response_error(response)
    return Playlist(client, response.json())


def get_playlists(
    client: ApiClient, playlist_type: Optional[PlaylistType] = None
) -> List[Playlist]:
    """Get all playlists in a channel.

    Args:
        client (ApiClient): The client to use to talk to the API.
        playlist_type (PlaylistType, optional): The type of playlist to get. Defaults to None.
        load_videos (bool, optional): Whether to load the list of videos in the playlist.
            Defaults to False.

    Returns:
        List[Playlist]: The playlists in the channel.
    """

    start = 0
    total = -1
    params: Dict[str, Union[str, int]] = {
        "count": 100,
        "sort": "videoChannelPosition",
        "start": start,
    }
    if playlist_type is not None:
        params["type"] = playlist_type.value
    playlists: List[Playlist] = []
    while len(playlists) != total:
        params["start"] = start
        response = client.session.get(
            client.base_url + PlaylistEndpoints.PLAYLISTS.value,
            params=params,
            timeout=10,
        )
        if response.status_code != 200:
            raise_api_bad_response_error(response)
        start = start + 100
        body = response.json()
        total = body["total"]
        for playlist in body["data"]:
            playlists.append(Playlist(client, playlist))
    return playlists


def get_playlists_in_account(
    client: ApiClient, account_name: str, playlist_type: Optional[PlaylistType] = None
) -> List[Playlist]:
    """Get all playlists in an account.

    Args:
        client (ApiClient): The client to use to talk to the API.
        channel (str): The handle of the channel to look in.
        playlist_type (PlaylistType, optional): The type of playlist to get. Defaults to None.
        load_videos (bool, optional): Whether to load the list of videos in the playlist.
            Defaults to False.

    Returns:
        List[Playlist]: The playlists in the channel.
    """

    start = 0
    total = -1
    params: Dict[str, Union[str, int]] = {
        "count": 100,
        "sort": "videoChannelPosition",
        "start": start,
    }
    if playlist_type is not None:
        params["type"] = playlist_type.value
    playlists: List[Playlist] = []
    while len(playlists) != total:
        params["start"] = start
        response = client.session.get(
            client.base_url
            + PlaylistEndpoints.PLAYLISTS_IN_ACCOUNT.value.format(
                account_name=account_name
            ),
            params=params,
            timeout=10,
        )
        if response.status_code != 200:
            raise_api_bad_response_error(response)
        start = start + 100
        body = response.json()
        total = body["total"]
        for playlist in body["data"]:
            playlists.append(Playlist(client, playlist))
    return playlists


def get_playlists_in_channel(
    client: ApiClient, channel: str, playlist_type: Optional[PlaylistType] = None
) -> List[Playlist]:
    """Get all playlists in a channel.

    Args:
        client (ApiClient): The client to use to talk to the API.
        channel (str): The handle of the channel to look in.
        playlist_type (PlaylistType, optional): The type of playlist to get. Defaults to None.
        load_videos (bool, optional): Whether to load the list of videos in the playlist.
            Defaults to False.

    Returns:
        List[Playlist]: The playlists in the channel.
    """

    start = 0
    total = -1
    params: Dict[str, Union[str, int]] = {
        "count": 100,
        "sort": "videoChannelPosition",
        "start": start,
    }
    if playlist_type is not None:
        params["type"] = playlist_type.value
    playlists: List[Playlist] = []
    while len(playlists) != total:
        params["start"] = start
        response = client.session.get(
            client.base_url
            + PlaylistEndpoints.PLAYLISTS_IN_CHANNEL.value.format(channel=channel),
            params=params,
            timeout=10,
        )
        if response.status_code != 200:
            raise_api_bad_response_error(response)
        start = start + 100
        body = response.json()
        total = body["total"]
        for playlist in body["data"]:
            playlists.append(Playlist(client, playlist))
    return playlists


def get_videos_in_playlist(client: ApiClient, playlist_id: int) -> List[PlaylistVideo]:
    """Get a list of videos in a given playlist.

    Args:
        client (ApiClient): The client to use to talk to the API.
        playlist_id (int): The numeric ID of the playlist to load.

    Returns:
        List[Video]: The videos in the playlist.
    """

    start = 0
    total = -1
    videos: List[PlaylistVideo] = []
    while len(videos) != total:
        response = client.session.get(
            client.base_url
            + PlaylistEndpoints.VIDEOS_IN_PLAYLIST.value.format(
                playlist_id=playlist_id
            ),
            params={"count": 100, "start": start},
            timeout=10,
        )
        if response.status_code != 200:
            raise_api_bad_response_error(response)
        start = start + 100
        body = response.json()
        total = body["total"]
        for video in body["data"]:
            videos.append(PlaylistVideo(video))
    return videos


# def reorder_channel_playlists():

# def reorder_playlist_videos():


def remove_video_from_playlist(
    client: ApiClient, playlist_id: int, playlist_item_id: int
) -> Literal[True]:
    """Remove a video from a playlist.

    Args:
        client (ApiClient): The client to use to talk to the API.
        playlist_id (int): The numeric ID of the playlist to remove from.
        playlist_item_id (Union[int, str]): The numeric ID of the item in the playlist to remove.

    Returns:
        True: If the video is removed successfully.
    """

    response = client.session.delete(
        client.base_url
        + PlaylistEndpoints.PLAYLIST_ITEM.value.format(
            playlist_id=playlist_id, playlist_item_id=playlist_item_id
        ),
        timeout=30,
    )

    if response.status_code != 200:
        raise_api_bad_response_error(response)

    return True


# pylint: disable=too-many-arguments
def update_playlist(
    client: ApiClient,
    playlist_id: int,
    *,
    channel_id: Optional[int] = None,
    display_name: Optional[str] = None,
    description: Optional[str] = None,
    privacy: Optional[Privacy] = None,
    thumbnail_file: Optional[str] = None,
) -> Playlist:
    """Update an existing playlist.

    Args:
        client (ApiClient): The client to use to talk to the API.
        playlist_id (int): The numeric ID of the playlist to update.
        channel_id (int, optional): The numeric ID of the channel to move the playlist to.
            Defaults to None.
        display_name (str, optional): The updated display name. Defaults to None.
        description (str, optional): The updated description. Defaults to None.
        privacy (Privacy, optional): The new privacy level for the playlist. Defaults to None.
        thumbnail_file (str, optional): The path to the new thumbnail file. Defaults to None.

    Returns:
        Playlist: The updated playlist.
    """

    playlist = get_playlist(client, playlist_id)

    data: Dict[str, Union[int, str, None]] = {
        "displayName": (
            display_name[:120] if display_name is not None else playlist.display_name
        ),
        "description": (
            description[:1000] if description is not None else playlist.description
        ),
        "privacy": privacy.value if privacy is not None else playlist.privacy.value,
    }

    if channel_id is not None:
        data["videoChannelId"] = channel_id
    elif playlist.channel is not None:
        data["videoChannelId"] = playlist.channel.id
    else:
        data["videoChannelId"] = None

    files: Dict[str, Tuple[str, BufferedReader, Optional[str]]] = {}
    if thumbnail_file is not None:
        with open(thumbnail_file, "br") as thumbnail_f:
            files["thumbnailfile"] = (
                basename(thumbnail_file),
                thumbnail_f,
                guess_type(thumbnail_file)[0],
            )

    response = client.session.put(
        client.base_url
        + PlaylistEndpoints.PLAYLIST.value.format(playlist_id=playlist_id),
        data=data,
        files=files,  # pyright: ignore[reportArgumentType]
        timeout=30,
    )

    if response.status_code != 200:
        raise_api_bad_response_error(response)

    return get_playlist(client, playlist_id)
