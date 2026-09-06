"""Test suite for the Nat Def toolchain.

``unittest`` from the standard library, not pytest: this toolchain has no third-party
dependencies by design, and its tests should not introduce one either. A scheduled run on a
bare machine can execute ``python3 -m unittest discover -s tests`` with nothing installed.
"""
