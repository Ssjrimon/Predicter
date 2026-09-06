# Founding source documents

These three government documents are the baseline this whole operation was built to track
against (see the project's original brief: "documents provided from the gvt"). They are tracked
in `intel-ledger.json` under `sources[]` (ids `NSS`, `NDS`, `ATA25`/`ATA26`) and `source_urls{}`
(`NSS`, `NDS`, `ATA`, `ATA26`), not duplicated here as files — this document exists so the three
canonical links survive the migration even if someone never opens the ledger JSON directly.

| Document | Publisher | URL |
|---|---|---|
| 2025 National Security Strategy | The White House | <https://www.whitehouse.gov/wp-content/uploads/2025/12/2025-National-Security-Strategy.pdf> |
| 2026 National Defense Strategy | Department of Defense | <https://media.defense.gov/2026/Jan/23/2003864773/-1/-1/0/2026-NATIONAL-DEFENSE-STRATEGY.PDF> |
| Annual Threat Assessment (2025, superseded by the 2026 edition inside the ledger) | Office of the Director of National Intelligence | <https://archive.dni.gov/files/ODNI/documents/assessments/ATA-2025-Unclassified-Report.pdf> |

These came from three separate single-URL docs in the original claude.ai Project ("Nat sec
strt", "Nat def strt", "Odni") that held nothing but these links — carried here verbatim during
the 6 Sep 2026 Claude Code migration. See `MIGRATION-NOTES.md`.
