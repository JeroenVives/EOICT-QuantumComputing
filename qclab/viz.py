"""qclab.viz — pretty visuals for circuits, counts and statevectors.

Every function returns a matplotlib ``Figure`` so notebooks can display it
with ``plt.show()`` or ``display(...)``.
"""

from __future__ import annotations

import numpy as np

import matplotlib.pyplot as plt
from matplotlib.colors import hsv_to_rgb
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from qiskit.visualization import plot_histogram

from .states import statevector_of


def draw_circuit(circuit: QuantumCircuit, title: str | None = None) -> plt.Figure:
    """Draw a circuit as a matplotlib figure (better looking than text art)."""
    fig = circuit.draw("mpl")
    fig.set_size_inches((max(5, circuit.size() * 0.6), max(2, circuit.num_qubits * 0.8 + 1)))
    if title:
        fig.suptitle(title, y=1.02)
    return fig


def plot_counts(counts: dict[str, int], title: str = "Measurement results", figsize: tuple = (8, 4)) -> plt.Figure:
    """Plot a histogram of measurement counts (bit-string -> number of shots).

    Bit-string convention: the leftmost character is the *highest*-numbered
    qubit. E.g. for 2 qubits, the string "10" means qubit 1 = 1 and qubit 0 = 0,
    i.e. the state |10⟩.
    """
    return plot_histogram(counts, title=title, figsize=figsize)


def plot_statevector(state, title: str = "Statevector", figsize: tuple = (8, 4)) -> plt.Figure:
    """Bar plot of a statevector: probability per basis state, coloured by phase.

    Parameters
    ----------
    state:
        A ``Statevector`` or a ``QuantumCircuit`` (measurements ignored).
    """
    sv: Statevector = state if isinstance(state, Statevector) else statevector_of(state)
    amps = np.asarray(sv.data, dtype=complex)
    probs = np.abs(amps) ** 2
    n_qubits = int(np.log2(len(amps)))
    labels = [format(i, f"0{n_qubits}b") for i in range(len(amps))]  # leftmost bit = highest qubit
    phases = np.angle(amps)
    colors = [hsv_to_rgb((ph / (2 * np.pi) + 0.5, 0.75, 1.0)) for ph in phases]

    fig, ax = plt.subplots(figsize=figsize)
    bars = ax.bar(range(len(amps)), probs, color=colors, edgecolor="black", linewidth=0.5)
    ax.set_xlabel("Basis state (leftmost bit = highest-numbered qubit)")
    ax.set_ylabel("Probability  |amplitude|²")
    ax.set_title(title)
    ax.set_xticks(range(len(amps)))
    ax.set_xticklabels([f"|{lb}⟩" for lb in labels], rotation=45)
    ax.set_ylim(0, 1.08)

    # Annotate non-zero bars with their probability (and phase, since colour alone
    # is hard to read) — but keep the plot clean for large state spaces.
    show_all = len(amps) <= 8
    for i, (p, a) in enumerate(zip(probs, amps)):
        if p > 1e-12 and (show_all or p > 0.05):
            phase_deg = np.degrees(np.angle(a))
            ax.text(i, p + 0.02, f"{p:.2f} (φ={phase_deg:.0f}°)", ha="center", va="bottom", fontsize=8)
    return fig
