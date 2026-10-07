# Quantum Computing Lab — Beginner Course

A beginner-friendly quantum-computing course built with **Python + Qiskit**.
Everything runs on a **local simulator** (free, unlimited). One optional exercise
runs a circuit on a **real IBM Quantum computer** — no credit card required.

The course covers, in one student notebook plus one teacher notebook:

1. One qubit in perfect superposition — circuit + measurement results.
2. The four **Bell states** — circuits + measurement results + the *internal*
   states, showing that measurement outcomes do **not** distinguish all states
   but the internal state does.
3. The **transformation matrix** of every gate used (H, X, CX, and the full circuit).
4. Five **3-qubit** states with exact measurement distributions (including a GHZ state).
5. *(Bonus)* Running a circuit on **real IBM Quantum hardware**.

## Files

| Path | What it is |
|------|------------|
| `exercises_student.ipynb` | The student workbook: theory, exercises, self-checks, visuals, bonus. |
| `solutions_teacher.ipynb` | The teacher's copy: every exercise solved, expected outputs, teaching notes. |
| `qclab/` | Small helper package used by both notebooks (runner, states, viz, checks). |
| `pyproject.toml` | Project + dependency definition. |
| `.env.example` | Template for the (optional) IBM Quantum API token. |

## Prerequisites

- Python **3.11–3.13**
- [uv](https://docs.astral.sh/uv/) for environment management (not pip)
- VS Code with the Jupyter / IPython extension (or any Jupyter IDE)

## Setup

```bash
# 1. Create the virtual environment and install dependencies in one step:
uv sync
```

`uv sync` reads `pyproject.toml` and creates `.venv/` with `qiskit`, `qiskit-aer`,
`qiskit-ibm-runtime`, `matplotlib`, `pylatexenc`, `python-dotenv` and `numpy`.

> If you ever need to add a package by hand, use uv (never pip):
> `uv pip install --python .venv/bin/python <package>`

## Run the notebooks

1. Open the folder in VS Code.
2. Open `exercises_student.ipynb`.
3. Pick the **`.venv`** interpreter / kernel (top-right of the notebook:
   *Change Kernel → Select Interpreter → `.venv/bin/python`*).
4. **Run All Cells** (top-to-bottom). The IBM bonus cell at the very end will
   print a friendly skip message if you haven't added a token — that's fine.

The teacher notebook (`solutions_teacher.ipynb`) works the same way and contains
the completed answers for every exercise.

## How the course works

- **Self-checks.** Most exercises end with a check cell that calls
  `qclab.check.assert_statevector` (exact state) and/or
  `qclab.check.assert_distribution` (measurement counts). When you get it right it
  prints `✅`; when you don't, it tells you exactly what's off.
- **Simulator first, hardware optional.** Real quantum hardware only returns
  *measurement counts* — it can never return the statevector or a gate matrix.
  So the "internal state" and "transformation matrix" parts are simulator-only by
  design, and the real-hardware part is a clearly-labelled bonus.

## (Optional) Connect a real IBM Quantum computer

Only needed for the **bonus** exercise.

1. Create a free IBM Quantum (Cloud) account at
   <https://www.ibm.com/quantum> (no credit card).
2. In the **Quantum Platform → Resource List → Add API token**, copy your API token.
3. Copy the token template and paste your token:

   ```bash
   cp .env.example .env
   # then edit .env:  QISKIT_IBM_TOKEN=your_token_here
   ```

4. Re-run the bonus cell in the student notebook. `qclab.runner.run_on_ibm`
   automatically picks a free, least-busy backend with enough qubits and waits for
   the result.

> **Use the free tier wisely.** The free tier grants roughly **10 minutes of
> hardware execution per month per account**. Keep shots modest (1024 is plenty)
> and run only the circuits you really want — for a class, use one shared token and
> run at most one circuit per exercise. Expect noisy counts (e.g. a Bell state
> coming out ≈48–52% rather than exactly 50/50) — that's the machine being real.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `ModuleNotFoundError: qclab` | Make sure the notebook kernel is `.venv` and you're running from the project root. `qclab` is a local package in the working directory. |
| `QISKIT_IBM_TOKEN` not found | Expected when you haven't set it up — only the bonus exercise needs it. Everything else works without it. |
| Circuit drawing looks wrong / missing | Ensure `pylatexenc` is installed (it is, via `uv sync`). |
| Counts are "off" from 50/50 | Normal — finite shots add statistical noise, and real hardware adds physical noise. |

## Qubit-ordering convention

Throughout the course we use **Qiskit's standard**: in a bit-string like `"101"`,
the **leftmost character is the highest-numbered qubit**.

```
|q2 q1 q0>   →   "101" means q2=1, q1=0, q0=1
```

In circuit drawings, qubit `0` is drawn on the **bottom** line and higher qubits
above it.
