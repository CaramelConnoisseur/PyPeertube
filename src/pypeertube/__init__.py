"""Tools to upload videos to a PeerTube instance"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

__author__ = "CaramelConnoisseur"
__copyright__ = "Copyright 2025, CaramelConnoisseur"
__email__ = "me@CaramelConnoisseur.dev"
__license__ = "GPL-3.0-only"
__maintainer__ = "CaramelConnoisseur"
__status__ = "Prototype"
__version__ = "0.0.1"


@dataclass
class Image:
    """An image on Peertube."""

    path: str
    width: int
    created_at: datetime
    updated_at: datetime

    def __repr__(self):
        return f"Image: {self.path}"

    def __str__(self):
        return self.path


class Account:  # pylint: disable=too-few-public-methods,too-many-instance-attributes
    """A user account on Peertube."""

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
    user_id: Optional[int]
    display_name: str
    description: Optional[str]

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
        self.created_at = input_dict["createdAt"] if "createdAt" in input_dict else None
        self.updated_at = input_dict["updatedAt"] if "updatedAt" in input_dict else None
        self.user_id = input_dict["userId"] if "userId" in input_dict else None
        self.display_name = input_dict["displayName"]
        self.description = (
            input_dict["description"] if "description" in input_dict else None
        )

    def __repr__(self):
        return f"Account: {self.id} - {self.name}"

    def __str__(self):
        return self.name
