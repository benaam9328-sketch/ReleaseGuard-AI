from datetime import datetime

from sqlalchemy import select

from app.db import (
    Base,
    DeliveryEventRow,
    ReleaseApprovalRow,
    ReleaseEvidenceRow,
    make_engine,
    make_session_factory,
)
from app.schemas.assessment import Approval
from app.schemas.enums import ApprovalDecision, ApprovalState
from app.schemas.events import DeliveryEvent
from app.schemas.evidence import ReleaseEvidence


class EvidenceStore:
    """Keeps everything in memory unless DATABASE_URL points at Postgres."""

    def __init__(self) -> None:
        self.backend = "memory"
        self._evidence: dict[str, dict] = {}
        self._approvals: dict[str, Approval] = {}
        self._events: dict[str, dict] = {}
        self._session_factory = None

    def reset_memory(self) -> None:
        self._evidence = {}
        self._approvals = {}
        self._events = {}

    def configure_postgres(self, database_url: str) -> None:
        engine = make_engine(database_url)
        Base.metadata.create_all(engine)
        self._session_factory = make_session_factory(engine)
        self.backend = "postgres"

    def save(self, evidence: ReleaseEvidence) -> tuple[ReleaseEvidence, bool]:
        payload = evidence.model_dump(mode="json")
        if self.backend == "postgres":
            created = self._save_postgres(
                evidence.release_id, payload, evidence.created_at
            )
        else:
            created = evidence.release_id not in self._evidence
            self._evidence[evidence.release_id] = payload
        return evidence, created

    def get(self, release_id: str) -> ReleaseEvidence | None:
        if self.backend == "postgres":
            payload = self._get_postgres(release_id)
        else:
            payload = self._evidence.get(release_id)
        if payload is None:
            return None
        return ReleaseEvidence.model_validate(payload)

    def save_approval(self, release_id: str, approval: Approval) -> None:
        if self.backend == "postgres":
            self._save_approval_postgres(release_id, approval)
            return
        self._approvals[release_id] = approval

    def get_approval(self, release_id: str) -> Approval | None:
        if self.backend == "postgres":
            return self._get_approval_postgres(release_id)
        return self._approvals.get(release_id)

    def save_event(self, event: DeliveryEvent) -> DeliveryEvent:
        payload = event.model_dump(mode="json")
        if self.backend == "postgres":
            self._save_event_postgres(event.event_id, payload, event.timestamp)
        else:
            self._events[event.event_id] = payload
        return event

    def list_events(self) -> list[DeliveryEvent]:
        if self.backend == "postgres":
            payloads = self._list_events_postgres()
        else:
            payloads = list(self._events.values())
        return [DeliveryEvent.model_validate(item) for item in payloads]

    def list_evidence(self) -> list[ReleaseEvidence]:
        if self.backend == "postgres":
            payloads = self._list_evidence_postgres()
        else:
            payloads = list(self._evidence.values())
        return [ReleaseEvidence.model_validate(item) for item in payloads]

    def _save_postgres(
        self, release_id: str, payload: dict, created_at: datetime
    ) -> bool:
        with self._session_factory() as session:
            row = session.get(ReleaseEvidenceRow, release_id)
            created = row is None
            if row is None:
                session.add(
                    ReleaseEvidenceRow(
                        release_id=release_id,
                        payload=payload,
                        created_at=created_at,
                    )
                )
            else:
                row.payload = payload
                row.created_at = created_at
            session.commit()
            return created

    def _get_postgres(self, release_id: str) -> dict | None:
        with self._session_factory() as session:
            row = session.get(ReleaseEvidenceRow, release_id)
            if row is None:
                return None
            return row.payload

    def _save_approval_postgres(self, release_id: str, approval: Approval) -> None:
        with self._session_factory() as session:
            row = session.get(ReleaseApprovalRow, release_id)
            if row is None:
                session.add(
                    ReleaseApprovalRow(
                        release_id=release_id,
                        decision=approval.decision.value,
                        decided_at=approval.decided_at,
                    )
                )
            else:
                row.decision = approval.decision.value
                row.decided_at = approval.decided_at
            session.commit()

    def _get_approval_postgres(self, release_id: str) -> Approval | None:
        with self._session_factory() as session:
            row = session.get(ReleaseApprovalRow, release_id)
            if row is None:
                return None
            decision = ApprovalDecision(row.decision)
            if decision == ApprovalDecision.approve:
                state = ApprovalState.approved
            else:
                state = ApprovalState.rejected
            return Approval(
                state=state,
                decision=decision,
                decided_at=row.decided_at,
            )

    def _save_event_postgres(
        self, event_id: str, payload: dict, timestamp: datetime
    ) -> None:
        with self._session_factory() as session:
            row = session.get(DeliveryEventRow, event_id)
            if row is None:
                session.add(
                    DeliveryEventRow(
                        event_id=event_id,
                        payload=payload,
                        timestamp=timestamp,
                    )
                )
            else:
                row.payload = payload
                row.timestamp = timestamp
            session.commit()

    def _list_events_postgres(self) -> list[dict]:
        with self._session_factory() as session:
            rows = session.scalars(select(DeliveryEventRow)).all()
            return [row.payload for row in rows]

    def _list_evidence_postgres(self) -> list[dict]:
        with self._session_factory() as session:
            rows = session.scalars(select(ReleaseEvidenceRow)).all()
            return [row.payload for row in rows]


store = EvidenceStore()


def get_store() -> EvidenceStore:
    return store
