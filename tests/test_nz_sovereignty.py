import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

def test_nz_data_residency_check():
    """
    Test: Can we prove where the data authority comes from?
    Pass = Mana source is named. Must be NZ or iwi entity for Aotearoa use.
    """
    trace_path = REPO_ROOT / "examples" / "signed_trace.json"
    with open(trace_path, 'r') as f:
        trace = json.load(f)
    
    # Check 1: Mana source exists
    assert "policy_bundle" in trace, "No policy bundle found"
    assert "mana_source" in trace["policy_bundle"], "Mana source not declared"
    
    # Check 2: Mana source is NZ-based or iwi
    mana = trace["policy_bundle"]["mana_source"].lower()
    nz_sources = ["iwi", "rūnanga", "hapū", "new zealand", "aotearoa", "nz"]
    assert any(source in mana for source in nz_sources), f"Mana source '{mana}' not NZ-based"

def test_te_tiriti_kaitiaki_named():
    """
    Test: Is there a Kaitiaki? Te Tiriti Article 2 requires protection of taonga.
    Data is taonga. Must have a named guardian.
    """
    trace_path = REPO_ROOT / "examples" / "signed_trace.json"
    with open(trace_path, 'r') as f:
        trace = json.load(f)
    
    assert "kaitiaki_attestation" in trace, "No Kaitiaki — fails Te Tiriti Article 2"
    assert "kaitiaki_name" in trace["kaitiaki_attestation"], "Kaitiaki not named"
    assert trace["kaitiaki_attestation"]["kaitiaki_name"]!= "", "Kaitiaki name empty"

def test_privacy_act_2020_alignment():
    """
    Test: Basic NZ Privacy Act 2020 check.
    Must show: purpose declared + accountability traceable.
    """
    trace_path = REPO_ROOT / "examples" / "signed_trace.json"
    with open(trace_path, 'r') as f:
        trace = json.load(f)
    
    # Principle 1: Purpose must be declared
    assert "policy_bundle" in trace, "No policy — no purpose declared"
    assert "policy_id" in trace["policy_bundle"], "Purpose not declared"
    
    # Principle 3: Collection transparency — who signed off?
    assert "ratified_by" in trace["policy_bundle"], "No ratifier — fails Principle 3"
