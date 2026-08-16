from app.schemas.enums import ScanStatus, SourceName, SourceStatus
from app.schemas.evidence import TrivyEvidence, TrivyFinding

_SEVERITY_FIELDS = {
    "CRITICAL": "critical",
    "HIGH": "high",
    "MEDIUM": "medium",
    "LOW": "low",
}


def parse_trivy_report(report: dict) -> TrivyEvidence:
    results = report.get("Results")
    if results is None:
        results = report.get("results")
    if results is None:
        return TrivyEvidence(
            status=SourceStatus.unknown,
            source=SourceName.trivy,
            scan_status=ScanStatus.scan_failed,
        )

    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    findings: list[TrivyFinding] = []
    for result in results:
        for vuln in result.get("Vulnerabilities") or []:
            severity = str(vuln.get("Severity") or "").upper()
            field = _SEVERITY_FIELDS.get(severity)
            if field is not None:
                counts[field] += 1
            cve = vuln.get("VulnerabilityID") or vuln.get("vulnerability_id")
            if cve:
                findings.append(
                    TrivyFinding(
                        vulnerability_id=str(cve),
                        severity=severity or "UNKNOWN",
                        package=vuln.get("PkgName") or vuln.get("package"),
                        title=vuln.get("Title") or vuln.get("title"),
                    )
                )

    total = counts["critical"] + counts["high"] + counts["medium"] + counts["low"]
    scan_status = ScanStatus.findings if total > 0 else ScanStatus.clean
    return TrivyEvidence(
        status=SourceStatus.success,
        source=SourceName.trivy,
        scan_status=scan_status,
        critical=counts["critical"],
        high=counts["high"],
        medium=counts["medium"],
        low=counts["low"],
        findings=findings or None,
    )
