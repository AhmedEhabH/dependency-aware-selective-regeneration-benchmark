"""Agentless-style file-level localization adapter (M17, frozen).

This package implements the ``AGENTLESS_STYLE_ADAPTATION`` protocol frozen in
``research/competitor-agentless-r1/AGENTLESS_STYLE_ADAPTATION_PROTOCOL_FREEZE.json``.

It is a minimal, production-ready adapter for the *file-level localization
stage only* of the published Agentless system (official source inspected
read-only at the frozen commit ``5ce5888b9f149beaace393957a55ea8ee46c9f71``),
applied to the frozen MAIN_297 population and scored with the same file-level
evaluator used for RM-CSS / SIP / Agent. It is NOT an exact reproduction of
every Agentless stage.
"""
