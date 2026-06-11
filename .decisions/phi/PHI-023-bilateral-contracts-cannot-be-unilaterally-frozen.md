<!-- ORACLE ARTIFACT — canonical copy in the Hindsight repo. Cross-project philosophy. Do not treat as a rule of the source project. -->

## PHI-023 — Bilateral contracts cannot be unilaterally frozen; gate dependent PRs on counterparty acknowledgment + pre-computed test vectors

**Date:** 2026-05-19
**Domain:** architecture
**Source Project:** mini-fax (feature 001-device-firmware bilateral contract with feature 002-message-worker)
**Source:** Plan-gate /speckit.review identified that `specs/001-device-firmware/contracts/device-worker.md` was authoring wire format, HMAC canonicalization, and response shapes that feature 002 (Worker side) had not yet spec'd or agreed to. The visible symptom was the empty test vector field; the deeper defect was the unilateral freeze of a bilateral artifact.

### Philosophy
When implementation A and implementation B must produce byte-identical output (or otherwise interoperate with no recovery margin), A cannot finalize the contract before B exists. Gate any PR that operationalizes the contract on (1) a counterparty acknowledgment artifact — at minimum a stub spec on the trailing side with an explicit `## Inherited contract` section — AND (2) pre-computed test vectors that BOTH sides can independently reproduce against the same inputs. The contract is not frozen until two independent producers agree byte-for-byte on a canonical example.

### Why I Hold This
A single byte of disagreement on a security-critical or recovery-impaired boundary is catastrophic. The mini-fax HMAC canonicalization could have diverged silently between ArduinoJson v7 on ESP32 and V8's JSON.stringify on Cloudflare Workers, bricking all 4 devices with no OTA recovery path (ADR-003). Two independent implementations of the contract producing the same expected hex against the same canonical body is the cheapest assurance that the boundary is real, not a wishful "we'll figure it out when 002 ships." The cost of pre-computing the test vector (one openssl invocation) is orders of magnitude lower than the cost of debugging a byte mismatch on physical hardware.

### Where It Applies
- HMAC / signature protocols between two independent implementations (firmware ↔ server, mobile client ↔ backend, browser extension ↔ server)
- Wire-format contracts where one team specs faster than the other (API providers writing OpenAPI before any consumer exists; gRPC schema designed in isolation)
- Content-addressed storage / deterministic builds where byte-equality across reproducers is the entire correctness property
- Federated systems where one node's implementation becomes "the reference" by accident of shipping first
- Migration boundaries where v1 freezes serialization that v2 must accept (and v1 can't be field-updated)

### Known Tensions
- Pre-computing vectors requires SOME implementation to exist; if both sides truly are vapor at design time, the vector itself is the chicken-or-egg problem. Mitigation: a third-party tool (openssl, a reference Python script) acts as the neutral arbiter.
- "Stub spec on the trailing side" adds ceremony when the trailing side has only one author who is also the leading side's author. The acknowledgment is partly self-talk — but the artifact still matters as a contract-freeze trigger for future readers.
- For very simple contracts (one field, well-known encoding), the ceremony is overkill. The principle applies most when canonicalization, ordering, or escape semantics could plausibly differ between implementations.

### Open to Revision When
- Both implementations live in the same repo under unified test infrastructure that exercises the contract as a side effect of normal CI — making byte-divergence impossible to ship.
- The contract format guarantees byte-equality at the serializer layer (e.g., a canonical form so strict that no implementation could disagree — protobuf binary encoding has elements of this, though field-order quirks remain).
- A reference implementation in a neutral language ships with the contract document and both sides verify against it as a gate.
