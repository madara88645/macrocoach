"""
Base data connector interface.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from ..core.models import HealthMetric


class BaseConnector(ABC):
    """
    Base interface for all health data connectors.
    """

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.is_authenticated = False

    @abstractmethod
    async def authenticate(self) -> bool:
        """
        Authenticate with the health platform.
        Returns True if successful.
        """
        pass

    @abstractmethod
    async def get_health_metrics(
        self, start_date: datetime, end_date: datetime
    ) -> list[HealthMetric]:
        """
        Retrieve health metrics for the specified date range.
        Returns normalized HealthMetric objects.
        """
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        """
        Check if the connector is available and properly configured.
        """
        pass

    async def test_connection(self) -> dict[str, Any]:
        """
        Test the connection and return status information.
        """
        try:
            is_auth = await self.authenticate()
            is_avail = await self.is_available()

            return {
                "connector": self.__class__.__name__,
                "available": is_avail,
                "authenticated": is_auth,
                "status": "ok" if (is_auth and is_avail) else "error",
            }
        except Exception as e:
            return {
                "connector": self.__class__.__name__,
                "available": False,
                "authenticated": False,
                "status": "error",
                "error": str(e),
            }
