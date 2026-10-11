import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

def test_nz_data_residency_check():
    """
    Test: Can we prove where the data authority comes from?
    Pass = Mana source contains NZ/iwi terms as whole words.
    Limitation: This checks the declared record, not physical data location or iwi mandate.
    """
    trace_path = REPO_ROOT / "examples" / "signed_trace.json"
    with open(trace_path, 'r') as f:
        trace = json.load(f)

    assert isinstance(trace, dict), f"Root trace must be JSON object, got {type(trace).__name__}"

    assert "policy_bundle" in trace, "No policy bundle found"
    policy = trace["policy_bundle"]
    assert isinstance(policy, dict), f"policy_bundle must be object, got {type(policy).__name__}"

    assert "mana_source" in policy, "Mana source not declared"
    mana = policy["mana_source"]
    assert isinstance(mana, str), f"Mana source must be string, got {type(mana).__name__}"
    assert mana.strip()!= "", "Mana source is empty string"

    # FIXED: Full list with word boundaries so 'nz' doesn't match 'bronze'
    nz_terms = [
        r'\biwi\b', r'\bhapū\b', r'\bwhānau\b', r'\brūnanga\b',
        r'\baotearoa\b', r'\bnew zealand\b', r'\bte tiriti\b'
    ]
    mana_normalized = mana.casefold()
    assert any(re.search(term, mana_normalized) for term in nz_terms), \
        f"Mana source '{mana}' does not contain recognized NZ/iwi terms"

def test_te_tiriti_kaitiaki_named():
    """
    Test: Is there a Kaitiaki? Te Tiriti Article 2 requires protection of taonga.
    Data is taonga. Must have a named guardian.
    Limitation: This checks a name is recorded, not cryptographic proof of mandate.
    """
    trace_path = REPO_ROOT / "examples" / "signed_trace.json"
    with open(trace_path, 'r') as f:
        trace = json.load(f)

    assert isinstance(trace, dict), f"Root trace must be JSON object, got {type(trace).__name__}"

    assert "kaitiaki_attestation" in trace, "No Kaitiaki — fails Te Tiriti Article 2"
    kaitiaki = trace["kaitiaki_attestation"]
    assert isinstance(kaitiaki, dict), f"kaitiaki_attestation must be object, got {type(kaitiaki).__name__}"

    assert "kaitiaki_name" in kaitiaki, "Kaitiaki not named"
    name = kaitiaki["kaitiaki_name"]
    assert isinstance(name, str), f"Kaitiaki name must be string, got {type(name).__name__}"
    assert name.strip()!= "", "Kaitiaki name empty"

def test_policy_record_check():
    """
    Test: Preliminary policy record check.
    Verifies: policy ID exists + ratification recorded.
    NOTE: This is NOT legal compliance determination under Privacy Act 2020.
    Limitation: Checks fields exist, not that policy PDF/evidence is linked.
    """
    trace_path = REPO_ROOT / "examples" / "signed_trace.json"
    with open(trace_path, 'r') as f:
        trace = json.load(f)

    assert isinstance(trace, dict), f"Root trace must be JSON object, got {type(trace).__name__}"

    assert "policy_bundle" in trace, "No policy — no purpose declared"
    policy = trace["policy_bundle"]
    assert isinstance(policy, dict), f"policy_bundle must be object, got {type(policy).__name__}"

    assert "policy_id" in policy, "Purpose not declared"
    policy_id = policy["policy_id"]
    assert isinstance(policy_id, str) and policy_id.strip()!= "", "Policy ID invalid"

    assert "ratified_by" in policy, "No ratifier — fails accountability record"
    ratifier = policy["ratified_by"]
    assert isinstance(ratifier, str) and ratifier.strip()!= "", "Ratifier invalid"
