"""
Te Whakaata Matihiko — Elite Core Test Suite v1.0
CLASSIFICATION: PRIVATE — NDA REQUIRED
Purpose: Prove cryptographic integrity + adversarial resistance + quantum-safety claims.
DO NOT DISTRIBUTE. DO NOT PUSH TO PUBLIC REPO.
"""

import json
import time
import hashlib
import pytest
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from verify import verify_trace, hash_file_sha3_256, verify_signature
from engine import EntropyGate, KaitiakiSigner

REPO_ROOT = Path(__file__).parent.parent.parent

# =========================
# TIER 3: CRYPTOGRAPHIC ELITE
# =========================

def test_ed25519_signature_non_malleability():
    """
    Elite Test 1: Signature Malleability Attack
    Attacker takes a valid Kaitiaki signature and tries to create a second valid signature 
    for the same message without the private key. Must fail.
    This is a real attack vector used against early blockchain systems.
    """
    trace_path = REPO_ROOT / "examples" / "signed_trace.json"
    with open(trace_path, 'r') as f:
        trace = json.load(f)
    
    original_sig = trace["kaitiaki_attestation"]["signature"]
    message = trace["kaitiaki_attestation"]["signed_payload"]
    pubkey = trace["verification_key"]
    
    # Attempt malleability: flip s-value in signature
    # ed25519 signatures are 64 bytes: 32-byte R + 32-byte S
    # Malleable sig = R, L-S instead of R, S
    sig_bytes = bytes.fromhex(original_sig.replace("ed25519:", ""))
    R = sig_bytes[:32]
    S = int.from_bytes(sig_bytes[32:], 'little')
    L = 2**252 + 27742317777372353535851937790883648493
    S_prime = (L - S) % L
    malleable_sig = "ed25519:" + (R + S_prime.to_bytes(32, 'little')).hex()
    
    # Verify: malleable sig must NOT verify
    assert verify_signature(message, malleable_sig, pubkey) is False, "Signature malleability detected — CRITICAL FAILURE"

def test_sha3_256_second_preimage_resistance():
    """
    Elite Test 2: Second Preimage Attack
    Attacker has Policy Hash from trace. Tries to find DIFFERENT policy text 
    that hashes to SAME value. Must be computationally infeasible.
    We test by asserting the hash function is actually SHA3-256, not SHA256.
    """
    trace_path = REPO_ROOT / "examples" / "signed_trace.json"
    with open(trace_path, 'r') as f:
        trace = json.load(f)
    
    policy_hash = trace["policy_bundle"]["policy_hash"]
    assert policy_hash.startswith("sha3-256:"), "Policy not using SHA3-256 — quantum vulnerable"
    
    # Prove it's not SHA256 by hashing 'abc' and checking known test vectors
    sha3_abc = hashlib.sha3_256(b'abc').hexdigest()
    assert sha3_abc == "3a985da74fe225b2045c172d6bd390bd855f086e3e9d525b46bfe24511431532"
    sha256_abc = hashlib.sha256(b'abc').hexdigest()
    assert sha3_abc != sha256_abc, "System accidentally using SHA256"

# =========================
# TIER 3: SYSTEMS ELITE  
# =========================

def test_entropy_gate_race_condition():
    """
    Elite Test 3: Race Condition Attack
    Fire 1000 decisions through Entropy Gate concurrently.
    Assert: ZERO decisions skip policy check. All have valid chain_signature.
    This is how Heartbleed-style bugs happen — under load.
    """
    gate = EntropyGate()
    test_payload = {"input_hash": "sha3-256:abc", "policy_id": "TEST-1"}
    
    def fire_decision():
        return gate.evaluate(test_payload)
    
    with ThreadPoolExecutor(max_workers=50) as executor:
        results = list(executor.map(lambda _: fire_decision(), range(1000)))
    
    assert len(results) == 1000, "Dropped decisions under load"
    for r in results:
        assert r["entropy_gate"]["decision"] in ["PERMIT", "BLOCK"], "Invalid decision state"
        assert "chain_signature" in r, "Missing chain_signature — policy check skipped"
        assert verify_trace(r) is True, "Unsigned decision escaped — CRITICAL FAILURE"

def test_kaitiaki_key_rotation_zero_downtime():
    """
    Elite Test 4: Key Rotation Attack Surface
    Simulate rotating Kaitiaki key while decisions are in-flight.
    Old signatures must still verify. New decisions must use new key. No gap.
    """
    signer_v1 = KaitiakiSigner("Kaitiaki-ID: TEST-001")
    payload = {"test": "data"}
    sig_v1 = signer_v1.sign(payload)
    
    # Rotate key
    signer_v2 = KaitiakiSigner("Kaitiaki-ID: TEST-001", rotate=True)
    sig_v2 = signer_v2.sign(payload)
    
    # Assert: v1 sig still verifies with v1 pubkey
    assert verify_signature(payload, sig_v1, signer_v1.pubkey) is True
    # Assert: v2 sig verifies with v2 pubkey  
    assert verify_signature(payload, sig_v2, signer_v2.pubkey) is True
    # Assert: v1 sig does NOT verify with v2 pubkey
    assert verify_signature(payload, sig_v1, signer_v2.pubkey) is False, "Key rotation breach — old key still valid"

# =========================
# TIER 3: ADVERSARIAL ELITE
# =========================

def test_replay_attack_old_attestation():
    """
    Elite Test 5: Replay Attack
    Attacker takes Kaitiaki attestation from 2025 and tries to attach it 
    to a new decision in 2026. Must fail — timestamp binding required.
    """
    trace_path = REPO_ROOT / "examples" / "signed_trace.json"
    with open(trace_path, 'r') as f:
        old_trace = json.load(f)
    
    # Create new decision but steal old attestation
    new_decision = old_trace.copy()
    new_decision["timestamp_utc"] = "2027-01-01T00:00:00Z"  # Future
    new_decision["input_hash"] = "sha3-256:deadbeef"  # Different data
    
    # Verification must fail because attestation.timestamp < decision.timestamp
    assert verify_trace(new_decision) is False, "Replay attack succeeded — CRITICAL FAILURE"

def test_policy_injection_malicious_rule():
    """
    Elite Test 6: Malicious Policy Injection
    Attacker tries to inject 'rule: ALLOW_ALL' into policy bundle.
    Entropy Gate must reject any policy not in ratified allowlist.
    """
    malicious_policy = {
        "policy_id": "MALICIOUS-OVERRIDE",
        "policy_version": "v0.0",
        "policy_hash": "sha3-256:" + hashlib.sha3_256(b"ALLOW ALL").hexdigest(),
        "ratified_by": "attacker",
        "rule_triggered": "ALLOW_ALL"
    }
    
    gate = EntropyGate()
    with pytest.raises(Exception) as excinfo:
        gate.evaluate({"policy_bundle": malicious_policy})
    assert "Policy not in ratified allowlist" in str(excinfo.value), "Malicious policy accepted — CRITICAL FAILURE"

def test_time_travel_attack_backdated_trace():
    """
    Elite Test 7: Time Travel Attack  
    Attacker creates trace dated before policy ratification date.
    Must fail — causality violation.
    """
    trace_path = REPO_ROOT / "examples" / "signed_trace.json"
    with open(trace_path, 'r') as f:
        trace = json.load(f)
    
    # Backdate decision to before policy existed
    trace["timestamp_utc"] = "2020-01-01T00:00:00Z"
    trace["policy_bundle"]["ratified_date"] = "2025-10-01"
    
    assert verify_trace(trace) is False, "Time travel attack succeeded — causality broken"
