<!-- ORACLE ARTIFACT — canonical copy in the oracle bank; this file is a browse mirror in the Hindsight repo. Observed evidence, not a held philosophy. -->

**Status:** active

OBS-008: Test artifacts must be locally detectable

Test artifacts (planted issues, red-team scenarios, adversarial fixtures) must be locally detectable — discoverable by reading within a small, contiguous section of the artifact without requiring multi-hop traversal across the document or dependency chain. Planted issues that require tracing N→M→X→Y chains are below the detection horizon for any reviewer panel regardless of rigor, and produce benchmark data that reflects fixture design failure rather than panel capability.

Source: Claude-Root benchmark calibration — ARCH-3 was missed at all rigor levels including FULL across 18 runs. Every panel caught downstream symptoms (health-check timing, rate-limiter deferral) but none traced back to the root cause (Redis setup in wrong phase), because doing so required reading across 3 phases and constructing a dependency chain mentally.
