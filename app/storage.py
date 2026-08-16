from datetime import datetime

from app.db import (
    Base,
    ReleaseApprovalRow,
    ReleaseEvidenceRow,
    make_engine,
    make_session_factory,
)
from app.schemas.assessment import Approval
from app.schemas.enums import ApprovalDecision, ApprovalState
from app.schemas.evidence import ReleaseEvidence


class EvidenceStore:
    """Memory by default. PostgreSQL when DATABASE_URL is configured."""

    def __init__(self) -> None:
        self.backend = "memory"
        self._memory: dict[str, dict] = {}
        self._approvals: dict[str, Approval] = {}
        self._session_factory = None

    def reset_memory(self) -> None:
        self._memory = {}
        self._approvals = {}

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
            created = evidence.release_id not in self._memory
            self._memory[evidence.release_id] = payload
        return evidence, created

    def get(self, release_id: str) -> ReleaseEvidence | None:
        if self.backend == "postgres":
            payload = self._get_postgres(release_id)
        else:
            payload = self._memory.get(release_id)
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


store = EvidenceStore()


def get_store() -> EvidenceStore:
    return store
