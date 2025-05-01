import logging
from datetime import date

from httpx import AsyncClient, HTTPStatusError

from app.core.schemas import ReactionUpdate, UserMessage

logger = logging.getLogger(__name__)


class APIGateway:
    """A gateway to interact with the backend API."""

    def __init__(self, base_url: str, timeout: int = 10):  # pragma: no mutate
        """Initializes the APIGateway.

        Args:
            base_url: The base URL of the API.
            timeout: The request timeout in seconds.
        """
        self.client = AsyncClient(  # pragma: no mutate
            base_url=base_url, timeout=timeout)  # pragma: no mutate

    async def create_user_message(self, user_message: UserMessage) -> None:
        """Sends a request to create a new user message.

        Args:
            user_message: The user message data to create.
        """
        try:
            response = await self.client.post(  # pragma: no mutate
                url="/user_messages",  # pragma: no mutate
                json=user_message.model_dump(mode="json"),  # pragma: no mutate
            )
            response.raise_for_status()
        except Exception as e:
            logger.exception(  # pragma: no mutate
                "Error occurred while "
                "creating user message: %s", e  # pragma: no mutate
            )

    async def update_reaction(self, reaction_update: ReactionUpdate) -> None:
        """Sends a request to update a reaction on a message.

        Args:
            reaction_update: The reaction update data.
        """
        try:
            response = await self.client.put(  # pragma: no mutate
                url="/reactions",
                json=reaction_update.model_dump(mode="json"),
            )
            response.raise_for_status()
        except Exception as e:
            logger.exception(
                "Error occurred "
                "while updating reaction: %s", e)  # pragma: no mutate

    async def delete_user_message(self, message_id: int) -> None:
        """Sends a request to delete a user message.

        Args:
            message_id: The ID of the message to delete.
        """
        try:
            response = await self.client.delete(
                url=f"/user_messages/{message_id}"
            )
            response.raise_for_status()
        except Exception as e:
            logger.exception(
                "Error occurred "
                "while deleting user message: %s", e  # pragma: no mutate
            )

    async def get_user_stats(self, user_id: str) -> int:
        """Sends a request to get statistics for a user.

        Args:
            user_id: The ID of the user.

        Returns:
            The user's message count, or 0 if an error occurs.
        """
        try:
            response = await self.client.get(f"/stats/{user_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.exception(
                "Error occurred while "
                "getting user stats: %s", e)  # pragma: no mutate
        return 0

    async def get_best_message_id(self, today: date) -> int | None:
        """Sends a request to get the ID of the best message for a given date.

        Args:
            today: The date for which to find the best message.

        Returns:
            The ID of the best message,
                or None if not found or an error occurs.
        """
        try:
            response = await self.client.get(
                url="/user_messages/best",
                params={"today": today.isoformat()},
            )
            response.raise_for_status()
            return response.json()
        except HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(
                    "No reactions found for today %s",  # pragma: no mutate
                    today,
                )
            else:
                logger.exception(
                    "HTTP error occurred while "
                    "getting best message: %s",  # pragma: no mutate
                    e,
                )
        except Exception as e:
            logger.exception(
                "Error occurred while "
                "getting best message: %s",  # pragma: no mutate
                e,
            )
        return None

    async def get_message_text(self, message_id: int) -> str | None:
        """Sends a request to get the text of a specific message.

        Args:
            message_id: The ID of the message.

        Returns:
            The text content of the message,
                or None if not found or an error occurs.
        """
        try:
            response = await self.client.get(
                url=f"/user_messages/{message_id}"
            )
            response.raise_for_status()
            text = response.json().get("message")
            logger.info(
                "Message text for "
                "id %s retrieved: %s", message_id, text  # pragma: no mutate
            )
            return text
        except Exception as e:
            logger.exception(
                "Error occurred while getting message text: %s",
                e,
            )
        return None
