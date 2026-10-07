"""qclab.runner — run circuits and get measurement counts.

Two backends are available:

* :func:`simulate`  — local, free, unlimited (qiskit-aer).
* :func:`run_on_ibm` — real IBM Quantum hardware (needs a token, see README).

Both return the same thing: a dict mapping bit-strings to counts, e.g.
``{"00": 512, "11": 512}``.
"""

from __future__ import annotations

import os

from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator


def _counts_from_pub_result(pub_result) -> dict[str, int]:
    """Turn one circuit's (pub) result into a ``{bitstring: count}`` dict.

    The primitives interface stores each circuit's output in a ``DataBin`` —
    a small mapping of named arrays — rather than as a plain counts dict. For
    a circuit that ends with ``measure`` the shots are kept in a ``BitArray``
    (the classical measurement register); ``get_counts()`` on that array gives
    the familiar ``{bitstring: shots}`` dictionary, e.g.
    ``{'00': 510, '11': 512}``.
    """
    data = pub_result.data
    # ``data`` is a DataBin. Its (single) array is the shots BitArray, so we
    # take it from ``values()`` rather than relying on the register's name.
    bit_array = next(iter(data.values()))
    return dict(bit_array.get_counts())


def simulate(circuit: QuantumCircuit, shots: int = 1024) -> dict[str, int]:
    """Run ``circuit`` on the local simulator and return measurement counts.

    The circuit MUST end with measurements (one classical bit per qubit that
    is measured). For the exact statevector, use ``qclab.states.statevector_of``
    instead — a measurement destroys the superposition, so counts alone do not
    fully characterise the state.
    """
    backend = AerSimulator()
    result = backend.run(circuit, shots=shots).result()
    return result.get_counts()


def _load_token() -> str | None:
    """Load QISKIT_IBM_TOKEN from the environment or the project's .env file."""
    token = os.environ.get("QISKIT_IBM_TOKEN")
    if token:
        return token
    # Fall back to a .env file in the current working directory (course convention).
    try:
        from dotenv import load_dotenv

        load_dotenv()
        return os.environ.get("QISKIT_IBM_TOKEN")
    except ImportError:
        return None


def _pick_backend(num_qubits: int):
    """Pick a real IBM backend with enough qubits that is currently running.

    We ask the service for the *least-busy* online backend, but shared
    free-tier hardware comes and goes: in the moments between runs every
    machine can briefly be out for maintenance or queue churn, and ``least_busy``
    then raises ``QiskitBackendNotFoundError`` ("No backend matches the
    criteria"). To keep the optional hardware run forgiving, if ``least_busy``
    finds nothing we fall back to scanning the backend list ourselves for any
    *operational* machine with enough qubits (fewest queued jobs first).
    """
    from qiskit_ibm_runtime import QiskitRuntimeService

    token = _load_token()
    if not token:
        raise RuntimeError(
            "No QISKIT_IBM_TOKEN found. Set it in the environment or in a "
            "'.env' file (see .env.example and README.md) to run on real "
            "hardware. Everything else in this course works without a token."
        )
    service = QiskitRuntimeService(token=token)

    # Preferred: let the service pick the least-busy online backend.
    try:
        return service.least_busy(min_num_qubits=num_qubits)
    except Exception:
        pass  # nothing "online" right now — fall back to the full list below

    # Fallback: any operational backend with enough qubits. ``least_busy`` uses a
    # stricter "online" check, so this survives the brief gaps where it matches
    # nothing but a machine is still usable.
    candidates = [
        b
        for b in service.backends()
        if b.num_qubits >= num_qubits and b.status().operational
    ]
    if not candidates:
        raise RuntimeError(
            f"No IBM hardware is currently available for this circuit "
            f"({num_qubits} qubits). Shared free-tier hardware is flaky — "
            "wait a few minutes and run the cell again."
        )
    queued = lambda b: getattr(b.status(), "pending_jobs", 0) or 0
    return min(candidates, key=queued)


def run_on_ibm(circuit: QuantumCircuit, shots: int = 1024, backend=None) -> dict[str, int]:
    """Run ``circuit`` on a real IBM Quantum computer and return measurement counts.

    Parameters
    ----------
    circuit:
        A measurement-ready circuit (must end with ``measure``).
    shots:
        Number of times the circuit is repeated on the hardware.
    backend:
        Optional backend name / object. When ``None`` the least-busy operational
        IBM backend that has enough qubits is used automatically.

    Notes
    -----
    Real hardware is shared and rate-limited (free tier: a monthly execution
    budget per account). Use it sparingly — e.g. one circuit per exercise —
    and expect counts that are *close to*, not identical to, the simulator:
    real gates have small errors.
    """
    from qiskit_ibm_runtime import SamplerV2
    from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

    if backend is None:
        backend = _pick_backend(num_qubits=circuit.num_qubits)
    print(f"Running on real hardware: {backend.name} (qubits: {backend.num_qubits})")

    # The primitives interface does NOT transpile for you (the old backend.run()
    # did). We must rewrite the circuit into the backend's native gates and
    # connectivity before submitting. This maps the logical qubits onto real
    # ones; the classical bits are unchanged, so the returned counts still use
    # the original bit-strings.
    transpiled = generate_preset_pass_manager(optimization_level=2, backend=backend).run(circuit)

    # ``backend.run()`` was removed from qiskit_ibm_runtime — real hardware is now
    # reached through the *primitives* interface. SamplerV2 runs the circuit
    # ``shots`` times and hands back measurement counts. The backend is the first
    # (``mode``) positional argument of the constructor.
    sampler = SamplerV2(backend)
    # The first argument of run() is the list of circuits (``pubs``).
    job = sampler.run([transpiled], shots=shots)
    print(f"Job {job.job_id()} submitted — waiting for result (this can take a few minutes)...")
    result = job.result()

    # ``result`` is a ``PrimitiveResult`` — a sequence, one entry per circuit
    # submitted. We sent a single circuit, so index the first (only) entry to
    # get its pub result, which carries the measurement data.
    return _counts_from_pub_result(result[0])
