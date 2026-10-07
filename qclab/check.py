"""qclab.check — small self-grading helpers so students can verify their work.

Two kinds of checks:

* :func:`assert_statevector`   — does the circuit really produce the *exact*
  state we want? (simulator only, because real hardware never returns states)
* :func:`assert_distribution`  — do the *measurement counts* match the expected
  probabilities? (works for both simulator and real hardware)

Both raise :class:`AssertionError` with a helpful message when the check fails,
and return ``True`` when it passes — so they can be used as plain functions too.
"""

from __future__ import annotations

import numpy as np
from qiskit import QuantumCircuit

from .states import statevector_of


def _bitstring_to_index(bits: str, n_qubits: int) -> int:
    """Convert a bit-string like "101" to its integer index (leftmost = highest qubit)."""
    return int(bits, 2)


def assert_statevector(
    circuit: QuantumCircuit,
    expected: dict[str, complex] | dict[str, float],
    tol: float = 1e-6,
    message: str = "statevector check",
) -> bool:
    """Assert that ``circuit`` produces the exact state given by ``expected``.

    ``expected`` maps bit-strings to amplitudes, e.g.
    ``{"00": 1/np.sqrt(2), "11": 1/np.sqrt(2)}``. Amplitudes that are not
    mentioned are assumed to be zero. The comparison is done on the *phase*
    too, so ``{"00": 1/np.sqrt(2), "11": -1/np.sqrt(2)}`` (Φ⁻) is NOT equal to
    ``{"00": 1/np.sqrt(2), "11": 1/np.sqrt(2)}`` (Φ⁺), even though their
    measurement distributions are identical.
    """
    sv = statevector_of(circuit)
    n = sv.num_qubits
    amps = np.asarray(sv.data, dtype=complex)
    expected_amps = np.zeros(len(amps), dtype=complex)
    for bits, amp in expected.items():
        expected_amps[_bitstring_to_index(bits, n)] = amp

    # Normalize the expected vector (in case students forget the 1/sqrt(2)).
    norm = np.linalg.norm(expected_amps)
    if norm < tol:
        raise ValueError("The expected state has no non-zero amplitudes.")
    expected_amps = expected_amps / norm

    # State fidelity: |<expected|actual>|² — insensitive to global phase,
    # which is physically meaningless, but sensitive to *relative* phase.
    fidelity = float(np.abs(np.vdot(expected_amps, amps)) ** 2)
    if fidelity < 1 - tol:
        got = {
            f"|{format(i, f'0{n}b')}⟩": f"{amps[i]:.3f}"
            for i in range(len(amps))
            if abs(amps[i]) > tol
        }
        raise AssertionError(
            f"{message}: state fidelity {fidelity:.6f} < 1-{tol:.0e}.\n"
            f"Your circuit produced: {got}\n"
            f"Expected: {expected}"
        )
    return True


def assert_distribution(
    counts: dict[str, int],
    expected_probs: dict[str, float],
    tol: float = 0.05,
    message: str = "distribution check",
) -> bool:
    """Assert that measurement ``counts`` match the expected probabilities.

    ``expected_probs`` maps bit-strings to probabilities, e.g.
    ``{"000": 0.5, "111": 0.5}``. Probabilities that are not mentioned are
    assumed to be 0.

    ``tol`` is a *looser* tolerance than for statevectors on purpose: even the
    simulator has a finite number of shots (statistical fluctuation), and real
    hardware adds noise on top. A 5% tolerance is a reasonable default.
    """
    total = sum(counts.values())
    probs = {bits: c / total for bits, c in counts.items()}

    max_dev = 0.0
    worst = None
    all_bits = set(probs) | set(expected_probs)
    for bits in sorted(all_bits):
        p = probs.get(bits, 0.0)
        e = expected_probs.get(bits, 0.0)
        dev = abs(p - e)
        if dev > max_dev:
            max_dev, worst = dev, (bits, p, e)

    if max_dev > tol:
        got = {f"|{b}⟩": f"{p:.3f}" for b, p in sorted(probs.items()) if p > 1e-4}
        exp = {f"|{b}⟩": f"{p:.3f}" for b, p in sorted(expected_probs.items())}
        raise AssertionError(
            f"{message}: distribution deviates by {max_dev:.3f} > tol {tol}.\n"
            f"Measured: {got}\n"
            f"Expected: {exp}\n"
            f"Most deviating outcome: {worst}"
        )
    return True
