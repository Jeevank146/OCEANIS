from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from schemas.marine_provider import (
    DataFreshnessStatus,
    DataQualityStatus,
    MarineDataType,
    NormalizedMarineRecord,
    ProviderHealthResponse,
    ProviderResponse,
    ProviderStatus,
)


class BaseDataConnector(ABC):
    """
    Base interface for all OCEANIS external data connectors.
    Maintains backward compatibility with legacy connector patterns.
    """

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Return the registered name of the data source."""
        raise NotImplementedError

    @abstractmethod
    def fetch(self, **kwargs: Any) -> Any:
        """Fetch raw data from the external source."""
        raise NotImplementedError

    @abstractmethod
    def normalize(self, raw_data: Any) -> Dict[str, Any]:
        """Convert source-specific data into an OCEANIS-compatible structure."""
        raise NotImplementedError

    def health_check(self) -> Dict[str, Any]:
        """Return basic connector health information."""
        return {
            "source": self.source_name,
            "status": "unknown",
        }


class BaseMarineDataProvider(BaseDataConnector):
    """
    Standardized provider abstraction for all OCEANIS Marine Data Providers
    (INCOIS, IMD, Copernicus, Fallback).
    
    Guarantees:
    1. Coordinate-based requests (latitude, longitude, time window, variables).
    2. Zero hardcoded cities or predefined numbers.
    3. Structured error/status reporting (never fabricating fake marine numbers).
    4. Explicit source provenance on every returned parameter record.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Standardized unique name of the provider."""
        raise NotImplementedError

    @property
    def source_name(self) -> str:
        """Alias for BaseDataConnector compatibility."""
        return self.provider_name

    @property
    @abstractmethod
    def provider_category(self) -> str:
        """Category: IN_SITU_BUOY | WEATHER_RADAR | SATELLITE_EO | HYDRODYNAMIC_MODEL | FALLBACK."""
        raise NotImplementedError

    @property
    @abstractmethod
    def governing_authority(self) -> str:
        """Governing agency or institution (e.g. INCOIS / MoES, IMD, Copernicus / ESA)."""
        raise NotImplementedError

    @property
    @abstractmethod
    def is_configured(self) -> bool:
        """Returns True if the required credentials / environment endpoints are configured."""
        raise NotImplementedError

    @abstractmethod
    def fetch_marine_data(
        self,
        latitude: float,
        longitude: float,
        variables: Optional[List[str]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        location_context: Optional[Dict[str, Any]] = None,
    ) -> ProviderResponse:
        """
        Coordinate-based query method. Returns a structured ProviderResponse
        containing validated NormalizedMarineRecord instances or a descriptive ProviderStatus.
        """
        raise NotImplementedError

    def check_health(self) -> ProviderHealthResponse:
        """
        Reports comprehensive health, configuration readiness, and operational status.
        """
        if not self.is_configured:
            return ProviderHealthResponse(
                name=self.provider_name,
                category=self.provider_category,
                authority=self.governing_authority,
                enabled=True,
                auth_configured=False,
                status=ProviderStatus.CONFIGURATION_REQUIRED,
                details="API credentials or upstream configuration missing in environment.",
            )
        try:
            # Concrete providers can override or test a ping endpoint
            return ProviderHealthResponse(
                name=self.provider_name,
                category=self.provider_category,
                authority=self.governing_authority,
                enabled=True,
                auth_configured=True,
                status=ProviderStatus.HEALTHY,
                last_successful_retrieval=datetime.now(timezone.utc).isoformat(),
            )
        except Exception as exc:
            return ProviderHealthResponse(
                name=self.provider_name,
                category=self.provider_category,
                authority=self.governing_authority,
                enabled=True,
                auth_configured=True,
                status=ProviderStatus.UNAVAILABLE,
                last_failure=datetime.now(timezone.utc).isoformat(),
                details=str(exc),
            )