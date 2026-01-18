"""Content type implementations for different ticket sources."""

from datetime import datetime
from typing import Any, Optional

from .base import TicketContent


class EmailContent(TicketContent):
    """Content from email submissions."""

    def __init__(
        self,
        sender_email: str,
        recipient_email: str,
        subject: str,
        body: str,
        timestamp: datetime,
        thread_id: Optional[str] = None,
        attachments: Optional[list[dict[str, Any]]] = None,
        headers: Optional[dict[str, str]] = None,
    ):
        self._sender_email = sender_email
        self._recipient_email = recipient_email
        self._subject = subject
        self._body = body
        self._timestamp = timestamp
        self._thread_id = thread_id
        self._attachments = attachments or []
        self._headers = headers or {}

    @property
    def raw_content(self) -> str:
        return f"Subject: {self._subject}\n\n{self._body}"

    @property
    def sender(self) -> str:
        return self._sender_email

    @property
    def timestamp(self) -> datetime:
        return self._timestamp

    @property
    def metadata(self) -> dict[str, Any]:
        return {
            "recipient_email": self._recipient_email,
            "subject": self._subject,
            "thread_id": self._thread_id,
            "headers": self._headers,
        }

    @property
    def sender_email(self) -> str:
        return self._sender_email

    @property
    def recipient_email(self) -> str:
        return self._recipient_email

    @property
    def subject(self) -> str:
        return self._subject

    @property
    def body(self) -> str:
        return self._body

    @property
    def thread_id(self) -> Optional[str]:
        return self._thread_id

    def extract_body(self) -> str:
        return self._body

    def extract_attachments(self) -> list[dict[str, Any]]:
        return self._attachments

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "email",
            "sender_email": self._sender_email,
            "recipient_email": self._recipient_email,
            "subject": self._subject,
            "body": self._body,
            "timestamp": self._timestamp.isoformat(),
            "thread_id": self._thread_id,
            "attachments": self._attachments,
            "headers": self._headers,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EmailContent":
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        return cls(
            sender_email=data["sender_email"],
            recipient_email=data["recipient_email"],
            subject=data["subject"],
            body=data["body"],
            timestamp=timestamp,
            thread_id=data.get("thread_id"),
            attachments=data.get("attachments"),
            headers=data.get("headers"),
        )


class DiscordContent(TicketContent):
    """Content from Discord messages."""

    def __init__(
        self,
        channel_id: str,
        user_id: str,
        message_id: str,
        message_text: str,
        timestamp: datetime,
        username: Optional[str] = None,
        guild_id: Optional[str] = None,
        attachments: Optional[list[dict[str, Any]]] = None,
    ):
        self._channel_id = channel_id
        self._user_id = user_id
        self._message_id = message_id
        self._message_text = message_text
        self._timestamp = timestamp
        self._username = username
        self._guild_id = guild_id
        self._attachments = attachments or []

    @property
    def raw_content(self) -> str:
        return self._message_text

    @property
    def sender(self) -> str:
        return self._username or self._user_id

    @property
    def timestamp(self) -> datetime:
        return self._timestamp

    @property
    def metadata(self) -> dict[str, Any]:
        return {
            "channel_id": self._channel_id,
            "user_id": self._user_id,
            "message_id": self._message_id,
            "guild_id": self._guild_id,
        }

    @property
    def channel_id(self) -> str:
        return self._channel_id

    @property
    def user_id(self) -> str:
        return self._user_id

    @property
    def message_id(self) -> str:
        return self._message_id

    @property
    def message_text(self) -> str:
        return self._message_text

    def extract_body(self) -> str:
        return self._message_text

    def extract_attachments(self) -> list[dict[str, Any]]:
        return self._attachments

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "discord",
            "channel_id": self._channel_id,
            "user_id": self._user_id,
            "message_id": self._message_id,
            "message_text": self._message_text,
            "timestamp": self._timestamp.isoformat(),
            "username": self._username,
            "guild_id": self._guild_id,
            "attachments": self._attachments,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DiscordContent":
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        return cls(
            channel_id=data["channel_id"],
            user_id=data["user_id"],
            message_id=data["message_id"],
            message_text=data["message_text"],
            timestamp=timestamp,
            username=data.get("username"),
            guild_id=data.get("guild_id"),
            attachments=data.get("attachments"),
        )


class GitHubContent(TicketContent):
    """Content from GitHub issues."""

    def __init__(
        self,
        repo: str,
        issue_number: int,
        author: str,
        issue_title: str,
        issue_body: str,
        timestamp: datetime,
        labels: Optional[list[str]] = None,
        url: Optional[str] = None,
    ):
        self._repo = repo
        self._issue_number = issue_number
        self._author = author
        self._issue_title = issue_title
        self._issue_body = issue_body
        self._timestamp = timestamp
        self._labels = labels or []
        self._url = url

    @property
    def raw_content(self) -> str:
        return f"{self._issue_title}\n\n{self._issue_body}"

    @property
    def sender(self) -> str:
        return self._author

    @property
    def timestamp(self) -> datetime:
        return self._timestamp

    @property
    def metadata(self) -> dict[str, Any]:
        return {
            "repo": self._repo,
            "issue_number": self._issue_number,
            "labels": self._labels,
            "url": self._url,
        }

    @property
    def repo(self) -> str:
        return self._repo

    @property
    def issue_number(self) -> int:
        return self._issue_number

    @property
    def issue_title(self) -> str:
        return self._issue_title

    @property
    def issue_body(self) -> str:
        return self._issue_body

    @property
    def url(self) -> Optional[str]:
        return self._url

    def extract_body(self) -> str:
        return self._issue_body

    def extract_attachments(self) -> list[dict[str, Any]]:
        return []  # GitHub issues don't have traditional attachments

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "github",
            "repo": self._repo,
            "issue_number": self._issue_number,
            "author": self._author,
            "issue_title": self._issue_title,
            "issue_body": self._issue_body,
            "timestamp": self._timestamp.isoformat(),
            "labels": self._labels,
            "url": self._url,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GitHubContent":
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        return cls(
            repo=data["repo"],
            issue_number=data["issue_number"],
            author=data["author"],
            issue_title=data["issue_title"],
            issue_body=data["issue_body"],
            timestamp=timestamp,
            labels=data.get("labels"),
            url=data.get("url"),
        )


class FormContent(TicketContent):
    """Content from form submissions."""

    def __init__(
        self,
        form_fields: dict[str, Any],
        submission_time: datetime,
        form_id: Optional[str] = None,
        submitter_email: Optional[str] = None,
        submitter_name: Optional[str] = None,
    ):
        self._form_fields = form_fields
        self._submission_time = submission_time
        self._form_id = form_id
        self._submitter_email = submitter_email
        self._submitter_name = submitter_name

    @property
    def raw_content(self) -> str:
        return "\n".join(f"{k}: {v}" for k, v in self._form_fields.items())

    @property
    def sender(self) -> str:
        return self._submitter_email or self._submitter_name or "anonymous"

    @property
    def timestamp(self) -> datetime:
        return self._submission_time

    @property
    def metadata(self) -> dict[str, Any]:
        return {
            "form_id": self._form_id,
            "submitter_email": self._submitter_email,
            "submitter_name": self._submitter_name,
        }

    @property
    def form_fields(self) -> dict[str, Any]:
        return self._form_fields

    @property
    def submission_time(self) -> datetime:
        return self._submission_time

    @property
    def form_id(self) -> Optional[str]:
        return self._form_id

    @property
    def submitter_email(self) -> Optional[str]:
        return self._submitter_email

    @property
    def submitter_name(self) -> Optional[str]:
        return self._submitter_name

    def extract_body(self) -> str:
        # Try to find a 'message' or 'body' field, otherwise return all fields
        for key in ["message", "body", "description", "content", "text"]:
            if key in self._form_fields:
                return str(self._form_fields[key])
        return self.raw_content

    def extract_attachments(self) -> list[dict[str, Any]]:
        return []  # Form submissions typically don't have attachments in this context

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "form",
            "form_fields": self._form_fields,
            "submission_time": self._submission_time.isoformat(),
            "form_id": self._form_id,
            "submitter_email": self._submitter_email,
            "submitter_name": self._submitter_name,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FormContent":
        submission_time = data.get("submission_time")
        if isinstance(submission_time, str):
            submission_time = datetime.fromisoformat(
                submission_time.replace("Z", "+00:00")
            )
        return cls(
            form_fields=data["form_fields"],
            submission_time=submission_time,
            form_id=data.get("form_id"),
            submitter_email=data.get("submitter_email"),
            submitter_name=data.get("submitter_name"),
        )


class SMSContent(TicketContent):
    """Content from SMS messages."""

    def __init__(
        self,
        sender_phone_number: str,
        recipient_phone_number: str,
        message_body: str,
        timestamp: datetime,
        message_sid: Optional[str] = None,
    ):
        self._sender_phone_number = sender_phone_number
        self._recipient_phone_number = recipient_phone_number
        self._message_body = message_body
        self._timestamp = timestamp
        self._message_sid = message_sid

    @property
    def raw_content(self) -> str:
        return self._message_body

    @property
    def sender(self) -> str:
        return self._sender_phone_number

    @property
    def timestamp(self) -> datetime:
        return self._timestamp

    @property
    def metadata(self) -> dict[str, Any]:
        return {
            "recipient_phone_number": self._recipient_phone_number,
            "message_sid": self._message_sid,
        }

    @property
    def sender_phone_number(self) -> str:
        return self._sender_phone_number
    
    @property
    def recipient_phone_number(self) -> str:
        return self._recipient_phone_number

    @property
    def message_body(self) -> str:
        return self._message_body
    
    @property
    def message_sid(self) -> Optional[str]:
        return self._message_sid

    def extract_body(self) -> str:
        return self._message_body

    def extract_attachments(self) -> list[dict[str, Any]]:
        return []

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "sms",
            "sender_phone_number": self._sender_phone_number,
            "recipient_phone_number": self._recipient_phone_number,
            "message_body": self._message_body,
            "timestamp": self._timestamp.isoformat(),
            "message_sid": self._message_sid,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SMSContent":
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        return cls(
            sender_phone_number=data["sender_phone_number"],
            recipient_phone_number=data["recipient_phone_number"],
            message_body=data["message_body"],
            timestamp=timestamp,
            message_sid=data.get("message_sid"),
        )


def content_from_dict(data: dict[str, Any]) -> TicketContent:
    """Factory function to create the appropriate content type from a dictionary."""
    content_type = data.get("type", "").lower()

    if content_type == "email":
        return EmailContent.from_dict(data)
    elif content_type == "discord":
        return DiscordContent.from_dict(data)
    elif content_type == "github":
        return GitHubContent.from_dict(data)
    elif content_type == "form":
        return FormContent.from_dict(data)
    elif content_type == "sms":
        return SMSContent.from_dict(data)
    else:
        raise ValueError(f"Unknown content type: {content_type}")
