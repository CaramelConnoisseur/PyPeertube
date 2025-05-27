"""Functions for managing Peertube Video Channels."""

from datetime import datetime
from enum import Enum
from mimetypes import guess_type
from os.path import basename
from typing import Any, Dict, List, Optional

from . import Account, Image, validators
from .client import ApiClient
from .exceptions import PeertubeError, raise_api_bad_response_error


class VideoChannel:  # pylint: disable=too-few-public-methods,too-many-instance-attributes
    """A Video Channel on Peertube."""

    id: int
    url: str
    name: str
    avatars: List[Image]
    host: str
    host_redundancy_allowed: Optional[bool]
    following_count: Optional[int]
    followers_count: Optional[int]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    display_name: str
    description: Optional[str]
    support: Optional[str]
    local: Optional[bool]
    banners: Optional[List[Image]]
    owner: Optional[Account]

    def __init__(self, input_dict: Dict[str, Any]):
        self.id = input_dict["id"]
        self.url = input_dict["url"]
        self.name = input_dict["name"]
        self.avatars = []
        for avatar in input_dict["avatars"]:
            self.avatars.append(
                Image(
                    avatar["path"],
                    avatar["width"],
                    avatar["createdAt"],
                    avatar["updatedAt"],
                )
            )
        self.host = input_dict["host"]
        self.host_redundancy_allowed = (
            input_dict["hostRedundancyAllowed"]
            if "hostRedundancyAllowed" in input_dict
            else None
        )
        self.following_count = (
            input_dict["followingCount"] if "followingCount" in input_dict else None
        )
        self.followers_count = (
            input_dict["followersCount"] if "followersCount" in input_dict else None
        )
        self.created_at = (
            datetime.fromisoformat(input_dict["createdAt"])
            if "createdAt" in input_dict
            else None
        )
        self.updated_at = (
            datetime.fromisoformat(input_dict["updatedAt"])
            if "updatedAt" in input_dict
            else None
        )
        self.display_name = input_dict["displayName"]
        self.description = (
            input_dict["description"] if "description" in input_dict else None
        )
        self.support = input_dict["support"] if "support" in input_dict else None
        self.local = input_dict["isLocal"] if "isLocal" in input_dict else None
        if "banners" in input_dict:
            self.banners = []
            for banner in input_dict["banners"]:
                self.banners.append(
                    Image(
                        banner["path"],
                        banner["width"],
                        banner["createdAt"],
                        banner["updatedAt"],
                    )
                )
        else:
            self.banners = None
        self.owner = (
            Account(input_dict["ownerAccount"])
            if "ownerAccount" in input_dict
            else None
        )

    def __repr__(self):
        return f"Channel: {self.id} - {self.name}"

    def __str__(self):
        return self.name


class ChannelEndpoints(Enum):
    """Endpoints for channel management."""

    CREATE_VIDEO_CHANNEL = "api/v1/video-channels"
    """Create a video channel."""

    GET_VIDEO_CHANNELS = "api/v1/video-channels?count=100&sort=name&start={start}"
    """List video channels."""

    VIDEO_CHANNEL = "api/v1/video-channels/{channel}"
    """Get a video channel."""

    SET_VIDEO_CHANNEL_AVATAR = "api/v1/video-channels/{channel}/avatar/pick"
    """Update channel avatar."""

    SET_VIDEO_CHANNEL_BANNER = "api/v1/video-channels/{channel}/banner/pick"
    """Update channel avatar."""


class PeertubeChannelError(PeertubeError):
    """A generic Peertube Channel error."""


class PeertubeNonChannelExistsError(PeertubeChannelError):
    """The requested channel already exists."""


class PeertubeNonExistentChannelError(PeertubeChannelError):
    """The requested channel does not exist."""


def create_channel(  # final call raises exception pylint: disable=inconsistent-return-statements
    client: ApiClient,
    name: str,
    display_name: str,
    description: Optional[str] = None,
    sponsor: Optional[str] = None,
) -> VideoChannel:
    """Create a new Video Channel on Peertube.

    Args:
        client (ApiClient): The authenticated client to use.
        name (str): The name of the new channel. Up to 50 alphanumeric, `_` or `.` characters.
        display_name (str): _description_
        description (Optional[str]): _description_
        sponsor (Optional[str], optional): _description_. Defaults to None.

    Raises:
        PeertubeNonChannelExistsError: _description_
        PeerTubeAPIBadResponseError: _description_

    Returns:
        int: _description_
    """

    if not validators.channel_name(name):
        raise ValueError("Invalid channel name", name)

    try:
        channel_id = get_channel(client, name)
        raise PeertubeNonChannelExistsError(client.base_url, name, channel_id)
    except PeertubeNonExistentChannelError:
        pass

    response = client.session.post(
        client.base_url + ChannelEndpoints.CREATE_VIDEO_CHANNEL.value,
        json={
            "displayName": display_name,
            "name": name,
            "description": description,
            "sponsor": sponsor,
        },
        timeout=3,
    )
    if response.status_code == 200:
        return get_channel(client, name)

    raise_api_bad_response_error(response)


def delete_channel(client: ApiClient, channel: str):
    """Delete a channel.

    Args:
        client (ApiClient): The authenticated client to use.
        channel (str): The channel to delete.

    Raises:
        ValueError: If the channel name is malformed.
    """

    if not validators.channel_name(channel):
        raise ValueError("Invalid channel name", channel)

    response = client.session.delete(
        client.base_url + ChannelEndpoints.VIDEO_CHANNEL.value.format(channel=channel)
    )

    if response.status_code != 204:
        raise_api_bad_response_error(response)


def get_channel(  # final call raises exception pylint: disable=inconsistent-return-statements
    client: ApiClient, name: str
) -> VideoChannel:
    """Get the numeric identifier of a given video channel.

    Args:
        client (ApiClient): The authenticated client to use.
        channel_name (str): The channel to look for.

    Raises:
        PeertubeNonExistentChannelError: If the channel does not exist and creation is not enabled.
        PeerTubeAPIBadResponseError: If an error occurs talking to the Peertube API.

    Returns:
        int: The channels ID.
    """

    if not validators.channel_name(name):
        raise ValueError("Invalid channel name", name)

    response = client.session.get(
        client.base_url + ChannelEndpoints.VIDEO_CHANNEL.value.format(channel=name),
        timeout=10,
    )

    if response.status_code == 200:
        return VideoChannel(response.json())

    if response.status_code == 404:
        raise PeertubeNonExistentChannelError(client.base_url, name)

    raise_api_bad_response_error(response)


def get_channels(client: ApiClient) -> List[VideoChannel]:
    """Get list of all know channels.

    Args:
        client (ApiClient): The authenticated client to use.

    Returns:
        List[VideoChannel]: A list of known channels.
    """

    channels: List[VideoChannel] = []
    total = -1
    start = 0
    while len(channels) != total:
        response = client.session.get(
            client.base_url
            + ChannelEndpoints.GET_VIDEO_CHANNELS.value.format(start=start),
            timeout=10,
        )
        response.raise_for_status()
        start = start + 100
        body = response.json()
        total = body["total"]
        for channel in body["data"]:
            channels.append(VideoChannel(channel))

    return channels


def set_channel_avatar(client: ApiClient, channel: str, avatar_path: str):
    """Upload an avatar image to the specified Peertube channel, it will be stretched to a square.

    Args:
        client (ApiClient): The authenticated client to use.
        channel (str): The channel to update.
        avatar_path (str): The path to the file to use as the new avatar.

    Raises:
        ValueError: If the channel name is in the wrong format.
        PeerTubeAPIBadResponseError: If an error occurs talking to the Peertube API.
    """

    if not validators.channel_name(channel):
        raise ValueError("Invalid channel name", channel)

    with open(avatar_path, "br") as f:
        response = client.session.post(
            client.base_url
            + ChannelEndpoints.SET_VIDEO_CHANNEL_AVATAR.value.format(channel=channel),
            files={
                "avatarfile": (
                    basename(avatar_path),
                    f,
                    guess_type(avatar_path)[0],
                )
            },
            timeout=30,
        )
    if not response.status_code == 200:
        raise_api_bad_response_error(response)


def set_channel_banner(client: ApiClient, channel: str, banner_path: str):
    """Upload a banner image to the specified Peertube channel, it will be stretched to 6:1.

    Args:
        client (ApiClient): The authenticated client to use.
        channel (str): The channel to update.
        banner_path (str): The path to the file to use as the new banner.

    Raises:
        ValueError: If the channel name is in the wrong format.
        PeerTubeAPIBadResponseError: If an error occurs talking to the Peertube API.
    """

    if not validators.channel_name(channel):
        raise ValueError("Invalid channel name", channel)

    with open(banner_path, "br") as f:
        response = client.session.post(
            client.base_url
            + ChannelEndpoints.SET_VIDEO_CHANNEL_BANNER.value.format(channel=channel),
            files={
                "bannerfile": (
                    basename(banner_path),
                    f,
                    guess_type(banner_path)[0],
                )
            },
            timeout=30,
        )
    if not response.status_code == 200:
        raise_api_bad_response_error(response)


# pylint: disable=inconsistent-return-statements,too-many-arguments,too-many-positional-arguments
def update_channel(
    client: ApiClient,
    name: str,
    display_name: Optional[str] = None,
    description: Optional[str] = None,
    support: Optional[str] = None,
    update_support_on_videos: bool = False,
) -> VideoChannel:
    """Create a new Video Channel on Peertube.

    Args:
        client (ApiClient): The authenticated client to use.
        name (str): The name of the new channel. Up to 50 alphanumeric, `_` or `.` characters.
        display_name (str), optional): _description_. Defaults to None.
        description (Optional[str]): _description_. Defaults to None.
        support (Optional[str], optional): _description_. Defaults to None.
        update_support_on_videos (bool, optional): Defaults to False.

    Raises:
        PeertubeNonChannelExistsError: _description_
        PeerTubeAPIBadResponseError: _description_

    Returns:
        int: _description_
    """

    if not validators.channel_name(name):
        raise ValueError("Invalid channel name", name)

    get_channel(client, name)

    json = {}
    if display_name is not None:
        json["displayName"] = display_name
    if description is not None:
        json["description"] = description

    if support is not None:
        json["bulkVideosSupportUpdate"] = update_support_on_videos
        json["support"] = support

    if len(json) > 0:
        response = client.session.put(
            f"{client.base_url}{ChannelEndpoints.VIDEO_CHANNEL.value.format(channel=name)}",
            json=json,
            timeout=3,
        )
        if response.status_code == 204:
            return get_channel(client, name)

        raise_api_bad_response_error(response)
