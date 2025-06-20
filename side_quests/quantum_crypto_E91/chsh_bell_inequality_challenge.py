import random
import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit import transpile
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

# ------------------------------------------------------------------------------------
# CHSH Bell inequality
# For detailed explanation, see: chsh_bell_inequality_understanding.md
# chsh_bell_inequality_understanding.py : Understanding the CHSH Bell Inequality: Intuition, Steps, and Examples
#
# === CHSH Bell Inequality: Key Points Résumé ===
#
# - The CHSH Bell inequality tests if two systems (e.g., qubits) are quantum entangled.
# - In classical physics (local hidden variables), the CHSH value |S| can never exceed 2.
# - Quantum entangled states can reach up to |S| = 2√2 ≈ 2.828, violating the classical bound.
# - The test uses four combinations of measurement bases for Alice and Bob.
#
# - **Correlation for each basis pair (a, b):**
#       E(a, b) = [count(00) + count(11) - count(01) - count(10)] / total
#   where total = count(00) + count(11) + count(01) + count(10)
#
# - **CHSH value (S):**
#       S = E(a1, b1) - E(a1, b2) + E(a2, b1) + E(a2, b2)
#   (with a1, a2 = Alice's bases; b1, b2 = Bob's bases)
#
# - If |S| > 2, the results cannot be explained by any classical (local) model: this is proof of quantum entanglement.
# - This principle is the foundation of quantum cryptography protocols like E91.
# ------------------------------------------------------------------------------------


# Constants for optimal Bell test bases
ALICE_BELL_BASES = ['0', '90']  # 0° and 90° 
BOB_BELL_BASES = ['45', '135']  # 45° and 135°
BELL_INEQUALITY_THRESHOLD = 2.0  # Classical limit

EVE_PERCENTAGE_COMPROMISED = 0.7  # Percentage of Bell pairs compromised by Eve

# Note: if there is no Eve, the Bell test should yield a value of 2√2 ≈ 2.82843
# If there is Eve that compromises a certain percentage of Bell pairs,
# the bell test yield will be lower than 2√2.
# In fact the value decrease linearly with increasing Eve's percentage.

# Note: Due to statistical fluctuations with finite sampling,
# measured CHSH values may occasionally slightly exceed the theoretical
# maximum of 2√2 ≈ 2.82843. This is expected behavior and doesn't
# indicate an error in the simulation.
# --------------------------------------------------------
# Measurement basis. Options:
#                 '0'   - Z-basis (0°)
#                 '90'  - X-basis (90°)
#                 '45'  - 45° basis
#                 '135' - 135° basis


# --------------------------------------------------------
# === Global Seed and Simulator Initialization ===
# For reproducibility, set a global seed for random number generation
# --------------------------------------------------------

GLOBAL_SEED = 91  # You can choose any integer
random.seed(GLOBAL_SEED)
np.random.seed(GLOBAL_SEED)

# seeded_aer_simulator = AerSimulator(seed_simulator=GLOBAL_SEED) # this is dosn't work, it give same result for all shots

# seed problem: https://github.com/Qiskit/qiskit-aer/issues/1916

# Initialize AerSimulator without an instance-level seed.
# We will provide a seed manually to each .run() call.
aer_simulator = AerSimulator()

# Global counter for manually seeding each simulator run.
# This ensures that each 1-shot simulation gets a unique seed from a reproducible sequence,
# promoting statistical variation across runs. Initialize with GLOBAL_SEED
# to tie all run sequences to the main seed.
MANUAL_SIMULATOR_SEED_COUNTER = GLOBAL_SEED


# --- End of Global Seed and Simulator Initialization ---


# --------------------------------------------------------
# === HELPER FUNCTIONS ===
# --------------------------------------------------------

def run_circuit(circ: QuantumCircuit, shots=1) -> dict:
    """
    Run a quantum circuit on the AerSimulator and return the counts
    @param circ: QuantumCircuit to run
    @param shots: Number of shots to run the circuit
    @return: dictionary of measurement results and their counts
    """

    # ---------------------------------
    # This part to ensure that each run_circuit call has a unique seed
    # Since the basic set seed in AerSimulator doesn't work correctly, in this senario
    global MANUAL_SIMULATOR_SEED_COUNTER  # Global variable to keep track of the seed counter
    global aer_simulator  # Global aer_simulator instance

    current_run_seed = MANUAL_SIMULATOR_SEED_COUNTER
    MANUAL_SIMULATOR_SEED_COUNTER += 1  # Increment for the next call to run_circuit
    # ---------------------------------

    circ = transpile(circ, aer_simulator)
    result = aer_simulator.run(circ, shots=shots, seed_simulator=current_run_seed).result()

    return result.get_counts(circ)  # get the counts of the circuit


# --------------------------------------------------------
# === BELL STATE GENERATION ===
# --------------------------------------------------------

def create_bell_pair_singlet_state() -> QuantumCircuit:
    """
    Create the Bell singlet state |Ψ-⟩ = (|01⟩ - |10⟩)/√2, which is used in the original E91 protocol.

    Returns:
        QuantumCircuit: A quantum circuit with two qubits prepared in the singlet Bell state.
    """

    # TODO: Student implementation goes here
    qc = QuantumCircuit(2, 2)
    qc.x(0)
    qc.h(0)
    qc.cx(0, 1)
    qc.z(1)
    return qc


def create_classical_random_state() -> QuantumCircuit:
    """
    Create a random classical (separable/non-entangled) product state for two qubits.

    This function should prepare each qubit independently in a random quantum state
    (which can be a superposition). The key is that the state of qubit 0 is
    prepared without any correlation to the state of qubit 1, and vice-versa,
    ensuring the overall two-qubit state is separable.

    Returns:
        QuantumCircuit: A quantum circuit with two qubits prepared in a random
                        classical (separable) state.
    """
    # TODO: Student implementation goes here
    qc = QuantumCircuit(2, 2)
    if random.choice([True, False]):
        qc.x(0)
    if random.choice([True, False]):
        qc.x(1)
    return qc


def create_eavesdropped_state(bell_qc: QuantumCircuit = None) -> QuantumCircuit:
    """
    Simulate Eve's intervention on a Bell pair, resulting in a non-entangled (classical) state.

    Args:
        bell_qc: QuantumCircuit containing a Bell pair (entangled state).

    Returns:
        QuantumCircuit: A new circuit representing the state after Eve's measurement and re-preparation.
        - Eve measures both qubits in the Z basis (destroying entanglement).
        - She then recreates a product state matching her measurement outcome.
        - The output circuit is always a classical (separable) state, not entangled.

    This function is used to model eavesdropping in the E91 protocol, showing how Eve's measurement destroys quantum correlations.
    """
    # TODO: Student implementation goes here
    qc = QuantumCircuit(2, 2)
    if random.choice([True, False]):
        qc.x(0)
    if random.choice([True, False]):
        qc.x(1)
    return qc


# --------------------------------------------------------
# === MEASUREMENT FUNCTIONS ===
# --------------------------------------------------------
def apply_basis_transformation(circuit: QuantumCircuit, qubit_index: int, basis: str) -> QuantumCircuit:
    """
    Apply a measurement basis transformation to a qubit.

    For the CHSH inequality, measurements are often performed in bases defined by
    angles in the X-Z plane of the Bloch sphere. We use Ry rotations for these
    transformations. An Ry(θ) gate rotates the qubit state around the Y-axis of
    the Bloch sphere by an angle θ.
    - To measure in a basis that is rotated by an angle 'angle_degrees' from the
      Z-axis towards the X-axis, we apply Ry(-angle_radians) to the qubit.
      This effectively rotates the qubit's state vector such that the desired
      measurement axis becomes the new Z-axis.

    Args:
        circuit: The quantum circuit to transform (input circuit).
        qubit_index: Index of the qubit to transform (0 or 1).
        basis: Measurement basis. Options:
            '0'   - Z-basis (0°)
            '90'  - X-basis (90°)
            '45'  - 45° basis
            '135' - 135° basis

    Returns:
        QuantumCircuit: A copy of the input circuit with the appropriate basis transformation applied
                        to the specified qubit. This prepares the qubit for measurement in the chosen basis.

    """

    # TODO: Student implementation goes here
    angle_map = {'0': 0, '45': np.pi / 4, '90': np.pi / 2, '135': 3 * np.pi / 4}
    circuit.ry(-angle_map[basis], qubit_index)
    return circuit


def measure_bell_pair(
        circuit: QuantumCircuit,
        alice_basis: str,
        bob_basis: str
) -> str:
    """
    Measure a Bell pair with Alice and Bob using specified bases.

    This simulates measuring an entangled pair with both qubits in a single circuit.
    For Bell tests, each Bell pair should be measured only once (shots=1).

    Args:
        circuit: Bell pair circuit to measure.
        alice_basis: Alice's measurement basis ('0', '45', '90').
        bob_basis: Bob's measurement basis ('45', '90', '135').

    Returns:
        str: The measurement result string ('00', '01', etc.). Number of shots to use (shot=1).
    """
    # TODO: Student implementation goes here
    qc = circuit.copy()
    apply_basis_transformation(qc, 0, alice_basis)
    apply_basis_transformation(qc, 1, bob_basis)
    qc.measure([0, 1], [0, 1])
    counts = run_circuit(qc)
    return list(counts.keys())[0]


# --------------------------------------------------------
# === BELL TEST FUNCTIONS ===
# --------------------------------------------------------

def run_bell_test_measurements(
        list_bell_pairs,
        list_alice_bases=ALICE_BELL_BASES,
        list_bob_bases=BOB_BELL_BASES
):
    """
    Run measurements on Bell pairs using the standard CHSH test bases.

    For each Bell pair, randomly choose Alice's and Bob's measurement bases,
    measure the qubits, and store the results and bases used for later analysis.

    Args:
        list_bell_pairs: List of quantum circuits containing Bell pairs.
        list_alice_bases: List of possible measurement bases for Alice.
        list_bob_bases: List of possible measurement bases for Bob.

    Returns:
        Tuple of three lists:
            - list_measurements_results: List of measurement results as bitstrings (e.g., '00', '01', etc.).
            - list_chosen_bases_alice: List of Alice's bases used for each measurement.
            - list_chosen_bases_bob: List of Bob's bases used for each measurement.
    """
    # TODO: Student implementation goes here
    results = []
    bases_alice = []
    bases_bob = []
    for qc in list_bell_pairs:
        ab = random.choice(list_alice_bases)
        bb = random.choice(list_bob_bases)
        res = measure_bell_pair(qc, ab, bb)
        results.append(res)
        bases_alice.append(ab)
        bases_bob.append(bb)
    return results, bases_alice, bases_bob


def organize_measurements_by_basis(
        list_measurements_results: list[str],
        list_chosen_bases_alice: list[str],
        list_chosen_bases_bob: list[str]
) -> dict[tuple[str, str], dict[str, int]]:
    """
    Organize pre-measured results by basis pairs for Bell test analysis.

    Args:
        list_measurements_results: List of measurement results as bitstrings (e.g., ['00', '01', '10', ...]).
        list_chosen_bases_alice: List of basis choices for Alice (e.g., ['0', '90', ...]), same length as results.
        list_chosen_bases_bob: List of basis choices for Bob (e.g., ['45', '135', ...]), same length as results.

    Returns:
        A nested dictionary of the form:
            {
                (alice_basis, bob_basis): {
                    '00': count,  # Number of times Alice got 0 and Bob got 0 for this basis pair
                    '01': count,  # Number of times Alice got 0 and Bob got 1
                    '10': count,  # Number of times Alice got 1 and Bob got 0
                    '11': count   # Number of times Alice got 1 and Bob got 1
                },
                ...
            }
        This structure allows you to easily look up, for each basis pair, how many times each outcome occurred.
        It is essential for computing the correlation E(a, b) for each basis pair in the CHSH test.
    """
    # TODO: Student implementation goes here
    data = {}
    for res, ab, bb in zip(list_measurements_results, list_chosen_bases_alice, list_chosen_bases_bob):
        key = (ab, bb)
        if key not in data:
            data[key] = {'00': 0, '01': 0, '10': 0, '11': 0}
        data[key][res] += 1
    return data


def calculate_correlations(
        measurements: dict[tuple[str, str], dict[str, int]]
) -> dict[tuple[str, str], float]:
    """
    Calculate the correlation E(a, b) for each basis pair from measurement results.
    The correlation is defined as:
        E(a, b) = [count(00) + count(11) - count(01) - count(10)] / total

    where total = count(00) + count(11) + count(01) + count(10)
    It is the same as : E(a,b) = P(same) - P(different) = P(00) + P(11) - P(01) - P(10)

    Args:
        measurements: Dictionary with basis pairs as keys and result counts as values.
            Example:
                {
                    ('0', '45'): {'00': 120, '01': 130, '10': 110, '11': 140},
                    ...
                }

    Returns:
        Dictionary mapping (alice_basis, bob_basis) to correlation value E(a, b).
            Example:
                {('0', '45'): 0.12, ...}
    """
    # TODO: Student implementation goes here
    correlations = {}
    for key, counts in measurements.items():
        total = sum(counts.values())
        if total == 0:
            correlations[key] = 0.0
            continue
        e = (counts.get('00', 0) + counts.get('11', 0) - counts.get('01', 0) - counts.get('10', 0)) / total
        correlations[key] = e
    return correlations


def calculate_chsh_value(
        correlations: dict[tuple[str, str], float],
        alice_bases: list[str] = ALICE_BELL_BASES,
        bob_bases: list[str] = BOB_BELL_BASES
) -> float:
    """
    Calculate the CHSH Bell parameter S from correlation values.

    The CHSH value is calculated as:
        S = E(a1, b1) - E(a1, b2) + E(a2, b1) + E(a2, b2)

    Args:
        correlations: Dictionary mapping (alice_basis, bob_basis) to correlation value E(a, b).
        alice_bases: List of Alice's two measurement bases (default: ['0', '90']).
        bob_bases: List of Bob's two measurement bases (default: ['45', '135']).

    Returns:
        float: The calculated CHSH Bell parameter S (absolute value).
    """
    # TODO: Student implementation goes here
    a1, a2 = alice_bases
    b1, b2 = bob_bases
    s = (correlations.get((a1, b1), 0) - correlations.get((a1, b2), 0) + correlations.get((a2, b1),
                                                                                          0) + correlations.get(
        (a2, b2), 0))
    return abs(s)


def check_bell_inequality(chsh_value: float) -> bool:
    """
    Check if the CHSH value violates the Bell inequality.

    Args:
        chsh_value: The calculated CHSH Bell parameter.

    Returns:
        bool: True if the Bell inequality is violated (i.e., quantum entanglement detected), False otherwise.
    """
    # TODO: Student implementation goes here
    return abs(chsh_value) > BELL_INEQUALITY_THRESHOLD


# --------------------------------------------------------
# === DEMONSTRATION FUNCTION ===
# --------------------------------------------------------

def run_bell_test(
        list_circuits: list[QuantumCircuit],
        name: str,
        alice_bases=ALICE_BELL_BASES,
        bob_bases=BOB_BELL_BASES
):
    """
    Run a complete Bell test on the provided circuits and print results.

    Args:
        circuits: List of quantum circuits (Bell pairs or classical states).
        name: Name for this test (used in printout and plot title).
        alice_bases: List of measurement bases for Alice.
        bob_bases: List of measurement bases for Bob.

    Returns:
        float: The calculated CHSH value for this test.
    """

    print(f"\nTest: {name}")

    results_list, alice_bases_list, bob_bases_list = run_bell_test_measurements(
        list_circuits, list_alice_bases=alice_bases, list_bob_bases=bob_bases)

    bell_results = organize_measurements_by_basis(results_list, alice_bases_list, bob_bases_list)

    correlations = calculate_correlations(bell_results)

    bell_chsh = calculate_chsh_value(correlations=correlations)

    print(f"CHSH value: {bell_chsh:.4f}")

    verdict = 'Quantum entanglement detected!' if check_bell_inequality(bell_chsh) else 'No quantum correlations'

    print(f"Verdict: {verdict}")

    # Visualization
    visualize_bell_test_results(correlations, bell_chsh, title=f"Bell Test Results: {name}")
    plt.savefig(f"bell_state_results_{name}.png")
    plt.show()

    return bell_chsh


def demonstrate_bell_inequality():
    """
    Demonstrate the Bell inequality test with detailed explanation and test cases.

    Note: we experiment with 1000 Bell pairs for statistical significance. This may take a while to run.
    So for testing purposes, you can reduce the number of Bell pairs to 10 or 100.
    After that, you must reuse 1000 Bell pairs for the final demonstration.
    """
    print("=== CHSH Bell Inequality Demo ===")
    print("Classical: |S| ≤ 2   |   Quantum: |S| can reach 2√2 ≈ 2.82")
    print("---------------------------------------------------------")
    print("Running Bell test with different states...\n")
    # --------------------------------------------------------
    # TODO: Student implementation goes here
    # TODO: only create the list of circuits, the rest is already implemented

    # Test 1: Ideal entangled Bell state
    print("Test 1: Ideal Bell state |Ψ-⟩ = (|01⟩ - |10⟩)/√2  - Singlet state used in original E91")
    list_bell_circuits = [create_bell_pair_singlet_state() for _ in range(1000)]  # TODO

    run_bell_test(list_bell_circuits, "Ideal Bell state")

    # --------------------------------------------------------
    # Test 2: Classical (non-entangled) state
    print("\nTest 2: Classical state (no entanglement)")
    list_classical_circuits = [create_classical_random_state() for _ in range(1000)]  # TODO

    run_bell_test(list_classical_circuits, "Classical state")

    # --------------------------------------------------------
    # Test 3: Entangled state with eavesdropping
    print("\nTest 3: Entangled state with eavesdropping")
    print(f"Eve compromises {EVE_PERCENTAGE_COMPROMISED * 100}% of Bell pairs, reducing the Bell parameter.")

    list_eve_circuits = [create_eavesdropped_state() for _ in range(1000)]  # TODO

    run_bell_test(list_eve_circuits, "Eavesdropped state")


# --------------------------------------------------------
# --------------------------------------------------------
# Visualization
def visualize_bell_test_results(correlations, chsh_value, title="Bell Test Results"):
    """
    Create visualizations of Bell test results including:
    - Correlation values heatmap
    - CHSH value compared to classical/quantum limits

    Args:
        correlations: Dictionary mapping (alice_basis, bob_basis) to correlation value E(a, b).
        chsh_value: The calculated CHSH Bell parameter S.
        title: Title for the visualization.
    """
    # Create figure with 2 subplots
    fig = plt.figure(figsize=(12, 5))

    # 1. Correlation Heatmap
    ax1 = fig.add_subplot(121)

    # Prepare data for heatmap
    alice_bases = sorted(set(b[0] for b in correlations.keys()))
    bob_bases = sorted(set(b[1] for b in correlations.keys()))
    corr_matrix = np.zeros((len(alice_bases), len(bob_bases)))

    # Fill matrix
    for i, a_base in enumerate(alice_bases):
        for j, b_base in enumerate(bob_bases):
            if (a_base, b_base) in correlations:
                corr_matrix[i, j] = correlations[(a_base, b_base)]

    # Create custom colormap from red to blue through white
    colors = [(0.8, 0.2, 0.2), (1, 1, 1), (0.2, 0.2, 0.8)]  # red, white, blue
    cmap = LinearSegmentedColormap.from_list('rwb', colors, N=100)

    # Plot heatmap
    im = ax1.imshow(corr_matrix, cmap=cmap, vmin=-1, vmax=1)
    ax1.set_title('Correlation Values E(a,b)', fontsize=12, fontweight='bold')
    ax1.set_xticks(np.arange(len(bob_bases)))
    ax1.set_yticks(np.arange(len(alice_bases)))
    ax1.set_xticklabels([f"{b}°" for b in bob_bases])
    ax1.set_yticklabels([f"{a}°" for a in alice_bases])
    ax1.set_xlabel("Bob's Measurement Angle", fontsize=10)
    ax1.set_ylabel("Alice's Measurement Angle", fontsize=10)

    # Add correlation values as text
    for i in range(len(alice_bases)):
        for j in range(len(bob_bases)):
            ax1.text(j, i, f"{corr_matrix[i, j]:.2f}", ha="center", va="center",
                     color="black" if abs(corr_matrix[i, j]) < 0.5 else "white")

    # Add colorbar
    cbar = fig.colorbar(im, ax=ax1)
    cbar.set_label('Correlation E(a,b)')

    # 2. CHSH Value Bar Chart
    ax2 = fig.add_subplot(122)

    # CHSH constants
    classical_limit = 2.0
    quantum_limit = 2 * np.sqrt(2)  # 2√2 ≈ 2.82

    # Create bar chart
    bars = ax2.bar([0], [chsh_value], width=0.4, color='purple', alpha=0.7)
    ax2.set_title('CHSH Value vs Limits', fontsize=12, fontweight='bold')
    ax2.set_xlim(-0.5, 0.5)
    ax2.set_ylim(0, 3.0)
    ax2.set_xticks([0])
    ax2.set_xticklabels(['CHSH Value'])

    # Add horizontal lines for limits
    ax2.axhline(y=classical_limit, color='r', linestyle='-', label='Classical Limit (2.0)')
    ax2.axhline(y=quantum_limit, color='b', linestyle='--', label='Quantum Limit (2√2 ≈ 2.82)')

    # Add value annotation (move it up slightly)
    ax2.text(0, chsh_value + 0.15, f"{chsh_value:.3f}", ha='center', fontsize=12)

    # Add verdict text (position it more carefully)
    if chsh_value > classical_limit:
        verdict = "Entanglement Detected!"
        color = 'green'
        # Position above the bar if it's high, below if it's low
        y_pos = min(chsh_value - 0.3, 1.5) if chsh_value > 1.0 else 0.5
    else:
        verdict = "No Quantum Correlations"
        color = 'red'
        y_pos = 0.5  # Position below the bar

    ax2.text(0, y_pos, verdict, ha='center', fontsize=14, color=color, fontweight='bold')

    # Add legend in a better position (upper left corner)
    ax2.legend(loc='upper left')

    # Main title and spacing
    plt.suptitle(title, fontsize=16, fontweight='bold')
    plt.tight_layout(rect=[0, 0, 1, 0.95])

    return fig


# ------ Main function -----------------------------------
def main():
    # Test both standard Bell inequality demo and comparison of measurement methods
    demonstrate_bell_inequality()


if __name__ == "__main__":
    main()