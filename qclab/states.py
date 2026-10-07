"""qclab.states — exact states and matrices from circuits.

A *statevector* is the exact list of complex amplitudes of a quantum state.
A *matrix* (operator) is the exact linear transformation a gate or circuit
implements. Neither of these is available from real hardware — that is why
these helpers work on the simulator.
"""

from __future__ import annotations

import numpy as np

from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator, Statevector


def _without_measurements(circuit: QuantumCircuit) -> QuantumCircuit:
    """Return a copy of ``circuit`` with final measurement instructions removed."""
    # remove_final_measurements() only strips measurements that are not followed
    # by further quantum instructions — exactly what we want here.
    return circuit.remove_final_measurements(inplace=False)


def statevector_of(circuit: QuantumCircuit) -> Statevector:
    """Compute the exact statevector of ``circuit`` (measurements ignored).

    Example
    -------
    >>> from qiskit import QuantumCircuit
    >>> qc = QuantumCircuit(1)
    >>> qc.h(0)
    >>> statevector_of(qc)
    <Statevector([0.70710678+0.j, 0.70710678+0.j], dims=(2,))>

    The result is *normalized*: the amplitudes' magnitudes squared sum to 1.
    A statevector fully characterises a pure state, which a histogram of
    measurement counts does not (two states can give identical counts but
    differ in relative phase — see the Bell states exercise).
    """
    return Statevector.from_instruction(_without_measurements(circuit))


def matrix_of(gate_or_circuit) -> Operator:
    """Return the (unitary) transformation matrix of a gate or a measurement-free circuit.

    Works for single gates (``HGate()``, ``XGate()``, ``CXGate()`` ...) and for
    whole ``QuantumCircuit`` objects (measurements, if any, are stripped).

    Example
    -------
    >>> from qiskit.circuit.library import HGate
    >>> matrix_of(HGate())
    <Operator([[0.70710678+0.j, 0.70710678+0.j],
               [0.70710678+0.j, -0.70710678+0.j]],
               input_dims=(2,), output_dims=(2,))>
    """
    if isinstance(gate_or_circuit, QuantumCircuit):
        gate_or_circuit = _without_measurements(gate_or_circuit)
    return Operator(gate_or_circuit)


def matrix_to_latex(oper, decimals: int = 3) -> str:
    """Return a LaTeX ``bmatrix`` string for an :class:`~qiskit.quantum_info.Operator`.

    Works with no optional dependencies (unlike ``qiskit.visualization.
    array_to_latex``, which requires ``sympy``). ``oper`` may be an
    :class:`~qiskit.quantum_info.Operator` or any array-like of complex numbers.

    Use it with ``IPython.display.Latex`` in a notebook::

        from qclab.states import matrix_of, matrix_to_latex
        display(Latex(matrix_to_latex(matrix_of(HGate()))))
    """
    data = oper.data if isinstance(oper, Operator) else np.asarray(oper, dtype=complex)

    def term(value: float, unit: str = "") -> str:
        r = round(float(value), decimals)
        if r == 0:
            return ""
        mag = abs(r)
        mag_s = f"{mag:.{decimals}f}".rstrip("0").rstrip(".")
        if mag_s == "":
            mag_s = "0"
        if mag == 1 and unit:
            mag_s = ""
        return ("-" if r < 0 else "") + mag_s + unit

    rows = []
    for row in data:
        cells = []
        for x in row:
            re_t = term(x.real)
            im_t = term(x.imag, unit="\\,i")
            if re_t == "" and im_t == "":
                cells.append("0")
            elif im_t == "":
                cells.append(re_t)
            elif re_t == "":
                cells.append(im_t)
            else:
                sign = "-" if im_t.startswith("-") else "+"
                im_body = im_t[1:] if im_t.startswith("-") else im_t
                cells.append(f"{re_t}{sign}{im_body}")
        rows.append(" & ".join(cells))

    body = (" \\\\ ").join(rows)
    return f"\\begin{{bmatrix}} {body} \\end{{bmatrix}}"
