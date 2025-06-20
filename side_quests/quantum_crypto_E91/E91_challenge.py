import random
from qiskit import QuantumCircuit

import encryption_algorithms as enc # contains the encryption and decryption algorithms

random.seed(91) # do not change this seed, otherwise you will get a different key

import chsh_bell_inequality_challenge as bell # contains the CHSH Bell inequality functions

EVE_PERCENTAGE_COMPROMISED = 0.7 # Percentage of Bell pairs compromised by Eve


# E91 protocol basis definitions (change here if needed)
ALICE_BASES = ['0', '45', '90']
BOB_BASES = ['45', '90', '135']

# Bases used for CHSH Bell test (subsets of ALICE_BASES and BOB_BASES)
ALICE_CHSH_BASES = ['0', '90']
BOB_CHSH_BASES = ['45', '135']

# All allowed basis pairs for CHSH test (computed automatically)
CHSH_BASIS_PAIRS = [(a, b) for a in ALICE_CHSH_BASES for b in BOB_CHSH_BASES]
print('CHSH_BASIS_PAIRS : ', CHSH_BASIS_PAIRS)


def generate_random_bases(length: int, options: list[str]) -> list[str]:
    """
    Generate a random list of measurement bases from the given options
    Args:
        length (int): The desired number of bases to generate (i.e., the length of the list).
        options (list[str]): A list of strings, where each string represents a
                             possible measurement basis (e.g., ['0', '45', '90'] for Alice,
                             or ['45', '90', '135'] for Bob).

    Returns:
        list[str]: A list of randomly selected bases, with the specified `length`.
    """
    #TODO: Student implementation goes here
    return [random.choice(options) for _ in range(length)] # gift from Algolab :p


def create_list_bell_pairs(num_pairs: int) -> list[QuantumCircuit]:
    """
    Creates a list of identical Bell pairs (the singlet state |Ψ-⟩).
    Each element in the list will be a QuantumCircuit object representing one Bell pair.

    Args:
        num_pairs (int): The number of Bell pair circuits to create.

    Returns:
        list[QuantumCircuit]: A list of `num_pairs` QuantumCircuit objects,
                              each prepared in the singlet Bell state |Ψ-⟩.
    """
    # TODO: Student implementation goes here
    # Hint: Use function from bell module
    return [bell.create_bell_pair_singlet_state() for _ in range(num_pairs)]


def measure_all_pairs(
        bell_pairs: list[QuantumCircuit],
        alice_bases: list[str],
        bob_bases: list[str]
) -> list[tuple[str, str]]:
    """
    Measures each Bell pair according to Alice's and Bob's chosen bases for that pair.

    Args:
        bell_pairs (list[QuantumCircuit]): A list of QuantumCircuit objects, where each
                                           circuit represents an entangled Bell pair.
        alice_bases (list[str]): A list of strings representing Alice's chosen measurement
                                 basis for each corresponding Bell pair in `bell_pairs`.
                                 The length of this list must be equal to `len(bell_pairs)`.
        bob_bases (list[str]): A list of strings representing Bob's chosen measurement
                               basis for each corresponding Bell pair in `bell_pairs`.
                               The length of this list must be equal to `len(bell_pairs)`.

    Returns:
        list[str]: A list str, each str is the measurement result string ('00', '01', etc.). Alice first bit, Bob second bit.
    """

    results: list[str] = []

    # TODO: Student implementation goes here
    # Hint: Use function from bell module

    for qp, ap, bp in zip(bell_pairs, alice_bases, bob_bases):
        result = bell.measure_bell_pair(qp, ap, bp)
        results.append(result)

    return results


def extract_e91_key_and_bell_test_data(
        results: list[str],
        alice_bases: list[str],
        bob_bases: list[str],
        chsh_basis_pairs: list[tuple[str, str]] = CHSH_BASIS_PAIRS
) -> dict:
    """
    Sift the measurement results according to the E91 protocol rules:
      - Keep for key generation only if Alice and Bob used the same basis and that basis is 45° or 90° (i.e., (45,45) or (90,90)).
      - Keep for Bell (CHSH) test only if Alice and Bob used specific pairs of different bases: (0,90), (0,135), (45,90), (45,135).
      - Discard all other combinations.

    Args:
        results (list[str]): List of measurement results (e.g., '01', '10', ...),
                             where the first bit is Alice's outcome and the second is Bob's.
        alice_bases (list[str]): List of Alice's chosen bases for each pair.
        bob_bases (list[str]): List of Bob's chosen bases for each pair.

    Returns:
        dict: {
            'key_results': list[str],         # Results for key generation (bases (45,45) or (90,90))

            'chsh_results': list[str],        # Results for CHSH Bell test
            'chsh_alice_bases': list[str],    # Alice's bases for CHSH test
            'chsh_bob_bases': list[str],      # Bob's bases for CHSH test
        }
    """

    key_results: list[str] = []

    chsh_results: list[str] = []
    chsh_alice_bases: list[str] = []
    chsh_bob_bases: list[str] = []

    # TODO: Student implementation goes here
    for res, ab, bb in zip(results, alice_bases, bob_bases):
        if ab == bb and ab in ['45', '90']:
            key_results.append(res)
        elif (ab, bb) in chsh_basis_pairs:
            chsh_results.append(res)
            chsh_alice_bases.append(ab)
            chsh_bob_bases.append(bb)


    return {
        'key_results': key_results,
        'chsh_results': chsh_results,
        'chsh_alice_bases': chsh_alice_bases,
        'chsh_bob_bases': chsh_bob_bases,
    }


# ----------------------------------------

def check_for_eavesdropping(
        chsh_results: list[str],
        chsh_alice_bases: list[str],
        chsh_bob_bases: list[str]
) -> dict:
    """
    Check for eavesdropping using the Bell (CHSH) inequality test.

    Args:
        chsh_results (list[str]): Measurement results for CHSH test pairs (e.g., '01', '10', ...).
        chsh_alice_bases (list[str]): Alice's bases for CHSH test pairs.
        chsh_bob_bases (list[str]): Bob's bases for CHSH test pairs.

    Returns:
        dict: {
            'chsh_value': float,   # The calculated CHSH S-parameter
            'is_secure': bool      # True if Bell inequality is violated (|S| > 2), False otherwise
        }
    """
    # TODO: Student implementation goes here
    # Hint: Use function from bell module
    #IMPORTANT ICI PAS LE BON NOM DE FONCTION
    measurements = bell.organize_measurements_by_basis(chsh_results, chsh_alice_bases,chsh_bob_bases)
    correlations = bell.calculate_correlations(measurements)

    bell_chsh_value = bell.calculate_chsh_value(correlations)
    is_secure = abs(bell_chsh_value) >2


    return {
        'chsh_value': bell_chsh_value,
        'is_secure': is_secure
    }


def run_e91_protocol(
        num_pairs: int = 2000,
        eavesdropping: bool = False
) -> str | None:
    """
    Runs the complete E91 quantum key distribution protocol and returns the generated key if secure.

    Args:
        num_pairs (int): Number of entangled Bell pairs to generate and distribute. Default is 2000.
        eavesdropping (bool): If True, simulates eavesdropping on a percentage of Bell pairs.

    Returns:
        str | None: The generated shared secret key as a string of '0's and '1's if the
                    protocol is successful and secure. Returns None if the security check
                    fails or if no key bits are generated.

    Steps:
        1. Generate Bell pairs.
        2. Optionally simulate eavesdropping by compromising a percentage of pairs.
        3. Randomly assign measurement bases to Alice and Bob.
        4. Measure all pairs and record results.
        5. Sift results into key generation and CHSH Bell test data.
        6. Perform the CHSH test to check for eavesdropping.
        7. If secure, extract and return the shared key.
    """
    # TODO: Student implementation goes here

    print(f"Generate Bell pairs...")

    # Create a list of identical Bell pairs
    bell_pairs = create_list_bell_pairs(num_pairs)

    print(f"Number of Bell pairs: len(bell_pairs) : {len(bell_pairs)}")

    # Simulate eavesdropping if requested
    if eavesdropping:
        print(f"Simulate Eavesdropping: ")

        # nb of pairs compromised
        compromised_count = int(EVE_PERCENTAGE_COMPROMISED*num_pairs)  # change this

        bell_pairs = [bell.create_eavesdropped_state(qc) if i < compromised_count else qc for i, qc in enumerate(bell_pairs)]  # change this

        print(f"Compromised pairs: {compromised_count} out of {num_pairs}")
        print(f"Number of Bell pairs after eavesdropping: {len(bell_pairs)}")

    # Generate random bases for Alice and Bob : Set available bases using angle notation consistently
    alice_bases = generate_random_bases(num_pairs, ALICE_BASES)
    bob_bases = generate_random_bases(num_pairs, BOB_BASES)

    # TODO ...

    results = measure_all_pairs(bell_pairs, alice_bases, bob_bases)

    sifted = extract_e91_key_and_bell_test_data(results, alice_bases, bob_bases)

    security = check_for_eavesdropping(sifted['chsh_results'],sifted['chsh_alice_bases'],sifted['chsh_bob_bases'])

    print(f"CHSH test value: {security['chsh_value']:.3f}")
    print(f"Secure channel: {security['is_secure']}")

    if security['is_secure'] and sifted['key_results']:
        key = ''.join([r[0] for r in sifted['key_results']])
        print(f"Shared key generated: {key}")
        return key
    else:
        return None


def decrypt_and_print_messages(key: str, filename: str = "encrypted_messages.txt"):
    """
    Read encrypted messages from a file, decrypt them using XOR with the given key, and print.

    Args:
        key (str): The key to use for XOR decryption.
        filename (str): The file to read encrypted messages from.
    """
    print("\nDecrypting all messages from", filename)

    # TODO: Student implementation goes here
    # Hint: Use enc.decrypt_xor_repeating_key from encryption_algorithms.py
    with open(filename, "r") as file:
        encrypted_lines = file.readlines()

    for i, ligne in enumerate(encrypted_lines):
        ligne = ligne.strip()
        if not ligne:
            continue
        decrypted = enc.decrypt_xor_repeating_key(ligne.split(": ")[1], key)
        print(f"Message {i + 1}: {decrypted}")

def main():
    # Run the E91 protocol
    key = run_e91_protocol(num_pairs=2000, eavesdropping=True)

    if key:
        # Example usage: encrypt a message with the key
        message = '"What I cannot create, I do not understand." Richard Feynman.'
        print("\nOriginal message:", message)

        print("\nXOR encryption:")
        encrypted = enc.encrypt_xor_repeating_key(message, key)
        print("Encrypted:", encrypted)
        decrypted = enc.decrypt_xor_repeating_key(encrypted, key)
        print("Decrypted:", decrypted)

        print("\nCaesar cipher encryption:")
        encrypted = enc.encrypt_caesar_cipher(message, key)
        print("Encrypted:", encrypted)
        decrypted = enc.decrypt_caesar_cipher(encrypted, key)
        print("Decrypted:", decrypted)

        # For your challenge: must generate the correct key using the E91 protocol to decrypt the messages. Without the key, decryption is not feasible.
        print("\nDecrypting messages from file...")
        # TODO: change the path to the encrypted file as needed
        path_to_encrypted_file = R"encrypted_messages.txt"
        decrypt_and_print_messages(key, filename=path_to_encrypted_file)

    else:
        print("\nKey generation failed. Encryption cannot proceed.")


if __name__ == "__main__":
    main()
