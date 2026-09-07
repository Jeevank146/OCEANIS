import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import SessionLocal
from connectors.incois import INCOISProvider
from connectors.copernicus import CopernicusProvider
from connectors.earth_observation import EarthObservationConnector
from connectors.imd import IMDProvider
from models.data_source import DataSource
from models.data_refresh_log import DataRefreshLog
from models.earth_observation import EarthObservation
from schemas.marine_provider import (
    DataFreshnessStatus,
    DataQualityStatus,
    MarineDataType,
    NormalizedMarineRecord,
    ProviderStatus,
)
from services.marine_data import MarineDataService
from services.validation import DataValidator
from services.freshness import evaluate_parameter_freshness
from ingestion.config import IngestionConfig, MonitoredLocation

logger = logging.getLogger(__name__)


class BackgroundIngestionWorker:
    """
    Lightweight, asynchronous background worker responsible for periodic
    data ingestion and database cache refresh for OCEANIS marine and EO sources.
    """

    _instance: Optional["BackgroundIngestionWorker"] = None

    def __init__(self, config: Optional[IngestionConfig] = None):
        self.config = config or IngestionConfig.from_env()
        self.locks: Dict[str, asyncio.Lock] = {
            "INCOIS": asyncio.Lock(),
            "Copernicus": asyncio.Lock(),
            "EarthObservation": asyncio.Lock(),
            "IMD": asyncio.Lock(),
        }
        self.tasks: List[asyncio.Task] = []
        self.is_running: bool = False
        self._status_tracker: Dict[str, Dict[str, Any]] = {
            "INCOIS": {
                "status": "INITIALIZED",
                "last_run": None,
                "last_success": None,
                "last_error": None,
                "records_processed": 0,
                "interval_minutes": self.config.incois_interval_minutes,
                "next_run": None,
            },
            "Copernicus": {
                "status": "INITIALIZED",
                "last_run": None,
                "last_success": None,
                "last_error": None,
                "records_processed": 0,
                "interval_minutes": self.config.copernicus_interval_minutes,
                "next_run": None,
            },
            "EarthObservation": {
                "status": "INITIALIZED",
                "last_run": None,
                "last_success": None,
                "last_error": None,
                "records_processed": 0,
                "interval_minutes": self.config.eo_interval_minutes,
                "next_run": None,
            },
            "IMD": {
                "status": "INITIALIZED",
                "last_run": None,
                "last_success": None,
                "last_error": None,
                "records_processed": 0,
                "interval_minutes": self.config.imd_interval_minutes,
                "next_run": None,
            },
        }

    @classmethod
    def get_instance(cls) -> "BackgroundIngestionWorker":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _get_or_create_data_source(self, db: Session, name: str, provider: str, source_type: str) -> DataSource:
        """Finds or registers the DataSource in PostgreSQL for audit and refresh logs."""
        ds = db.query(DataSource).filter(DataSource.name == name).first()
        if not ds:
            ds = DataSource(
                name=name,
                provider=provider,
                source_type=source_type,
                is_active=True,
                description=f"Automated ingestion pipeline for {provider} {name}",
            )
            db.add(ds)
            db.commit()
            db.refresh(ds)
        return ds

    def _create_refresh_log(self, db: Session, data_source_id: int) -> DataRefreshLog:
        log = DataRefreshLog(
            data_source_id=data_source_id,
            started_at=datetime.now(timezone.utc),
            status="STARTED",
            records_processed=0,
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    def _complete_refresh_log(
        self,
        db: Session,
        log: DataRefreshLog,
        status: str,
        records_processed: int,
        error_message: Optional[str] = None,
    ) -> None:
        log.status = status
        log.records_processed = records_processed
        log.completed_at = datetime.now(timezone.utc)
        log.error_message = error_message
        db.commit()

    async def ingest_incois(self, locations: Optional[List[MonitoredLocation]] = None) -> Dict[str, Any]:
        """Runs INCOIS ingestion across monitored coastal locations."""
        if self.locks["INCOIS"].locked():
            logger.warning("[INGESTION] INCOIS job skipped: already running")
            return {"status": "SKIPPED", "reason": "Concurrent execution locked"}

        async with self.locks["INCOIS"]:
            now = datetime.now(timezone.utc)
            self._status_tracker["INCOIS"]["last_run"] = now.isoformat()
            self._status_tracker["INCOIS"]["status"] = "RUNNING"
            logger.info("[INGESTION] INCOIS started")

            db = SessionLocal()
            target_locs = locations or self.config.locations
            total_records = 0
            location_errors = []
            provider = INCOISProvider()
            service = MarineDataService(providers={"INCOIS": provider})

            try:
                ds = self._get_or_create_data_source(db, "INCOIS RSMC Ocean Forecast", "INCOIS", "NETCDF_FORECAST")
                ref_log = self._create_refresh_log(db, ds.id)

                for loc in target_locs:
                    try:
                        res = provider.fetch_marine_data(latitude=loc.latitude, longitude=loc.longitude)
                        if res.status == ProviderStatus.HEALTHY and res.records:
                            valid_recs, _ = DataValidator.filter_and_validate_records(res.records)
                            for r in valid_recs:
                                r.freshness_status = evaluate_parameter_freshness(
                                    timestamp=datetime.fromisoformat(r.valid_time.replace("Z", "+00:00")),
                                    parameter=r.parameter,
                                    provider="INCOIS",
                                    current_time=now,
                                )
                            if valid_recs:
                                service._persist_records(db, loc.latitude, loc.longitude, valid_recs, now)
                                total_records += len(valid_recs)
                    except Exception as loc_exc:
                        location_errors.append(f"{loc.name}: {str(loc_exc)}")
                        logger.warning(f"[INGESTION] INCOIS location {loc.name} failed: {loc_exc}")

                if location_errors and total_records == 0:
                    err_msg = "; ".join(location_errors)
                    self._complete_refresh_log(db, ref_log, "FAILED", 0, err_msg)
                    self._status_tracker["INCOIS"]["status"] = "FAILED"
                    self._status_tracker["INCOIS"]["last_error"] = err_msg
                    logger.error(f"[INGESTION] INCOIS failed: {err_msg}")
                    return {"status": "FAILED", "error": err_msg}

                self._complete_refresh_log(db, ref_log, "SUCCESS", total_records)
                self._status_tracker["INCOIS"]["status"] = "SUCCESS"
                self._status_tracker["INCOIS"]["last_success"] = now.isoformat()
                self._status_tracker["INCOIS"]["records_processed"] = total_records
                self._status_tracker["INCOIS"]["last_error"] = None
                logger.info(f"[INGESTION] INCOIS completed: {total_records} records")
                return {"status": "SUCCESS", "records_processed": total_records}

            except Exception as exc:
                err_msg = str(exc)
                logger.error(f"[INGESTION] INCOIS failed: {err_msg}", exc_info=True)
                self._status_tracker["INCOIS"]["status"] = "FAILED"
                self._status_tracker["INCOIS"]["last_error"] = err_msg
                try:
                    if 'ref_log' in locals():
                        self._complete_refresh_log(db, ref_log, "FAILED", total_records, err_msg)
                except Exception:
                    pass
                return {"status": "FAILED", "error": err_msg}
            finally:
                db.close()

    async def ingest_copernicus(self, locations: Optional[List[MonitoredLocation]] = None) -> Dict[str, Any]:
        """Runs Copernicus Marine current vector ingestion."""
        if self.locks["Copernicus"].locked():
            logger.warning("[INGESTION] COPERNICUS job skipped: already running")
            return {"status": "SKIPPED", "reason": "Concurrent execution locked"}

        async with self.locks["Copernicus"]:
            now = datetime.now(timezone.utc)
            self._status_tracker["Copernicus"]["last_run"] = now.isoformat()
            self._status_tracker["Copernicus"]["status"] = "RUNNING"
            logger.info("[INGESTION] COPERNICUS started")

            db = SessionLocal()
            target_locs = locations or self.config.locations
            total_records = 0
            location_errors = []
            provider = CopernicusProvider()
            service = MarineDataService(providers={"Copernicus": provider})

            try:
                ds = self._get_or_create_data_source(db, "Copernicus Marine Physics", "Copernicus", "PHYSICAL_OCEANOGRAPHY")
                ref_log = self._create_refresh_log(db, ds.id)

                for loc in target_locs:
                    try:
                        res = provider.fetch_marine_data(latitude=loc.latitude, longitude=loc.longitude)
                        if res.status == ProviderStatus.HEALTHY and res.records:
                            valid_recs, _ = DataValidator.filter_and_validate_records(res.records)
                            for r in valid_recs:
                                r.freshness_status = evaluate_parameter_freshness(
                                    timestamp=datetime.fromisoformat(r.valid_time.replace("Z", "+00:00")),
                                    parameter=r.parameter,
                                    provider="Copernicus",
                                    current_time=now,
                                )
                            if valid_recs:
                                service._persist_records(db, loc.latitude, loc.longitude, valid_recs, now)
                                total_records += len(valid_recs)
                    except Exception as loc_exc:
                        location_errors.append(f"{loc.name}: {str(loc_exc)}")
                        logger.warning(f"[INGESTION] Copernicus location {loc.name} failed: {loc_exc}")

                if location_errors and total_records == 0:
                    err_msg = "; ".join(location_errors)
                    self._complete_refresh_log(db, ref_log, "FAILED", 0, err_msg)
                    self._status_tracker["Copernicus"]["status"] = "FAILED"
                    self._status_tracker["Copernicus"]["last_error"] = err_msg
                    logger.error(f"[INGESTION] COPERNICUS failed: {err_msg}")
                    return {"status": "FAILED", "error": err_msg}

                self._complete_refresh_log(db, ref_log, "SUCCESS", total_records)
                self._status_tracker["Copernicus"]["status"] = "SUCCESS"
                self._status_tracker["Copernicus"]["last_success"] = now.isoformat()
                self._status_tracker["Copernicus"]["records_processed"] = total_records
                self._status_tracker["Copernicus"]["last_error"] = None
                logger.info(f"[INGESTION] COPERNICUS completed: {total_records} records")
                return {"status": "SUCCESS", "records_processed": total_records}

            except Exception as exc:
                err_msg = str(exc)
                logger.error(f"[INGESTION] COPERNICUS failed: {err_msg}", exc_info=True)
                self._status_tracker["Copernicus"]["status"] = "FAILED"
                self._status_tracker["Copernicus"]["last_error"] = err_msg
                try:
                    if 'ref_log' in locals():
                        self._complete_refresh_log(db, ref_log, "FAILED", total_records, err_msg)
                except Exception:
                    pass
                return {"status": "FAILED", "error": err_msg}
            finally:
                db.close()

    async def ingest_earth_observation(self, locations: Optional[List[MonitoredLocation]] = None) -> Dict[str, Any]:
        """Runs Earth Observation (Sentinel-3 / Chlorophyll-a / SST) ingestion."""
        if self.locks["EarthObservation"].locked():
            logger.warning("[INGESTION] EO job skipped: already running")
            return {"status": "SKIPPED", "reason": "Concurrent execution locked"}

        async with self.locks["EarthObservation"]:
            now = datetime.now(timezone.utc)
            self._status_tracker["EarthObservation"]["last_run"] = now.isoformat()
            self._status_tracker["EarthObservation"]["status"] = "RUNNING"
            logger.info("[INGESTION] EO started")

            db = SessionLocal()
            target_locs = locations or self.config.locations
            total_records = 0
            location_errors = []
            from ingestion.earth_observation import EarthObservationIngestionService
            eo_service = EarthObservationIngestionService()

            try:
                ds = self._get_or_create_data_source(db, "Sentinel Ocean Colour & Thermal", "ESA_Copernicus", "SATELLITE_EO")
                ref_log = self._create_refresh_log(db, ds.id)

                for loc in target_locs:
                    try:
                        res = eo_service.ingest(db=db, latitude=loc.latitude, longitude=loc.longitude, use_cache=False)
                        if res and res.get("observation_id"):
                            total_records += 1
                    except Exception as loc_exc:
                        location_errors.append(f"{loc.name}: {str(loc_exc)}")
                        logger.warning(f"[INGESTION] EO location {loc.name} failed: {loc_exc}")

                if location_errors and total_records == 0:
                    err_msg = "; ".join(location_errors)
                    self._complete_refresh_log(db, ref_log, "FAILED", 0, err_msg)
                    self._status_tracker["EarthObservation"]["status"] = "FAILED"
                    self._status_tracker["EarthObservation"]["last_error"] = err_msg
                    logger.error(f"[INGESTION] EO failed: {err_msg}")
                    return {"status": "FAILED", "error": err_msg}

                self._complete_refresh_log(db, ref_log, "SUCCESS", total_records)
                self._status_tracker["EarthObservation"]["status"] = "SUCCESS"
                self._status_tracker["EarthObservation"]["last_success"] = now.isoformat()
                self._status_tracker["EarthObservation"]["records_processed"] = total_records
                self._status_tracker["EarthObservation"]["last_error"] = None
                logger.info(f"[INGESTION] EO completed: {total_records} records")
                return {"status": "SUCCESS", "records_processed": total_records}

            except Exception as exc:
                err_msg = str(exc)
                logger.error(f"[INGESTION] EO failed: {err_msg}", exc_info=True)
                self._status_tracker["EarthObservation"]["status"] = "FAILED"
                self._status_tracker["EarthObservation"]["last_error"] = err_msg
                try:
                    if 'ref_log' in locals():
                        self._complete_refresh_log(db, ref_log, "FAILED", total_records, err_msg)
                except Exception:
                    pass
                return {"status": "FAILED", "error": err_msg}
            finally:
                db.close()

    async def ingest_imd(self, locations: Optional[List[MonitoredLocation]] = None) -> Dict[str, Any]:
        """Runs IMD radar & coastal warnings ingestion with graceful status detection."""
        if self.locks["IMD"].locked():
            logger.warning("[INGESTION] IMD job skipped: already running")
            return {"status": "SKIPPED", "reason": "Concurrent execution locked"}

        async with self.locks["IMD"]:
            now = datetime.now(timezone.utc)
            self._status_tracker["IMD"]["last_run"] = now.isoformat()
            provider = IMDProvider()

            # Step 1: Detect configuration readiness
            if not provider.is_configured:
                msg = "IMD skipped: credentials (IMD_API_KEY) not configured"
                logger.info(f"[INGESTION] {msg}")
                self._status_tracker["IMD"]["status"] = "SKIPPED"
                self._status_tracker["IMD"]["last_error"] = msg
                return {"status": "SKIPPED", "reason": msg}

            # Step 2: Attempt real fetch & handle status
            logger.info("[INGESTION] IMD started")
            self._status_tracker["IMD"]["status"] = "RUNNING"
            db = SessionLocal()
            target_locs = locations or self.config.locations
            total_records = 0

            try:
                ds = self._get_or_create_data_source(db, "IMD Coastal Radar & Warnings", "IMD", "COASTAL_RADAR")
                ref_log = self._create_refresh_log(db, ds.id)

                for loc in target_locs:
                    res = provider.fetch_marine_data(latitude=loc.latitude, longitude=loc.longitude)
                    if res.status == ProviderStatus.AUTH_FAILURE:
                        reason = f"IMD skipped: gateway/IP authorization required ({res.error_message})"
                        logger.info(f"[INGESTION] {reason}")
                        self._complete_refresh_log(db, ref_log, "SKIPPED", 0, reason)
                        self._status_tracker["IMD"]["status"] = "SKIPPED"
                        self._status_tracker["IMD"]["last_error"] = reason
                        return {"status": "SKIPPED", "reason": reason}
                    elif res.status == ProviderStatus.HEALTHY and res.records:
                        service = MarineDataService(providers={"IMD": provider})
                        valid_recs, _ = DataValidator.filter_and_validate_records(res.records)
                        if valid_recs:
                            service._persist_records(db, loc.latitude, loc.longitude, valid_recs, now)
                            total_records += len(valid_recs)

                self._complete_refresh_log(db, ref_log, "SUCCESS", total_records)
                self._status_tracker["IMD"]["status"] = "SUCCESS"
                self._status_tracker["IMD"]["last_success"] = now.isoformat()
                self._status_tracker["IMD"]["records_processed"] = total_records
                self._status_tracker["IMD"]["last_error"] = None
                logger.info(f"[INGESTION] IMD completed: {total_records} records")
                return {"status": "SUCCESS", "records_processed": total_records}

            except Exception as exc:
                err_msg = str(exc)
                logger.error(f"[INGESTION] IMD error: {err_msg}", exc_info=True)
                self._status_tracker["IMD"]["status"] = "FAILED"
                self._status_tracker["IMD"]["last_error"] = err_msg
                try:
                    if 'ref_log' in locals():
                        self._complete_refresh_log(db, ref_log, "FAILED", total_records, err_msg)
                except Exception:
                    pass
                return {"status": "FAILED", "error": err_msg}
            finally:
                db.close()

    async def trigger_job(
        self,
        provider_name: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Safe manual trigger for testing and admin operations."""
        locs = None
        if latitude is not None and longitude is not None:
            locs = [MonitoredLocation(name="Custom Location", latitude=latitude, longitude=longitude)]

        prov_upper = provider_name.upper()
        if prov_upper == "INCOIS":
            return await self.ingest_incois(locs)
        elif prov_upper in ("COPERNICUS", "COPERNICUS_MARINE"):
            return await self.ingest_copernicus(locs)
        elif prov_upper in ("EO", "EARTH_OBSERVATION", "EARTHOBSERVATION"):
            return await self.ingest_earth_observation(locs)
        elif prov_upper == "IMD":
            return await self.ingest_imd(locs)
        else:
            return {"status": "ERROR", "message": f"Unknown provider '{provider_name}'"}

    def get_worker_status(self) -> Dict[str, Any]:
        """Returns structured worker and per-provider ingestion telemetry."""
        return {
            "worker_enabled": self.config.enabled,
            "is_running": self.is_running,
            "monitored_locations_count": len(self.config.locations),
            "providers": self._status_tracker,
        }

    async def _provider_loop(self, provider_key: str, interval_minutes: int, job_callable) -> None:
        """Background loop executing scheduled ingestion with clean exception handling."""
        while self.is_running:
            try:
                next_dt = datetime.now(timezone.utc) + timedelta(minutes=interval_minutes)
                self._status_tracker[provider_key]["next_run"] = next_dt.isoformat()
                await job_callable()
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error(f"[INGESTION] Scheduled loop error for {provider_key}: {exc}", exc_info=True)
            
            try:
                await asyncio.sleep(interval_minutes * 60)
            except asyncio.CancelledError:
                break

    def start(self) -> None:
        """Starts all scheduled provider ingestion loops if enabled."""
        if not self.config.enabled:
            logger.info("[INGESTION] Automated background ingestion worker is DISABLED by configuration.")
            return

        if self.is_running:
            logger.warning("[INGESTION] Background ingestion worker already running.")
            return

        self.is_running = True
        logger.info("[INGESTION] Starting automated background ingestion worker tasks...")

        loop = asyncio.get_event_loop()
        self.tasks = [
            loop.create_task(
                self._provider_loop("INCOIS", self.config.incois_interval_minutes, self.ingest_incois)
            ),
            loop.create_task(
                self._provider_loop("Copernicus", self.config.copernicus_interval_minutes, self.ingest_copernicus)
            ),
            loop.create_task(
                self._provider_loop("EarthObservation", self.config.eo_interval_minutes, self.ingest_earth_observation)
            ),
            loop.create_task(
                self._provider_loop("IMD", self.config.imd_interval_minutes, self.ingest_imd)
            ),
        ]
        logger.info(f"[INGESTION] Worker started with {len(self.tasks)} active scheduled provider loops.")

    async def stop(self) -> None:
        """Gracefully cancels all active provider loops and releases resources."""
        if not self.is_running:
            return

        logger.info("[INGESTION] Stopping background ingestion worker...")
        self.is_running = False
        for task in self.tasks:
            task.cancel()

        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        self.tasks.clear()
        logger.info("[INGESTION] Background ingestion worker stopped cleanly.")
