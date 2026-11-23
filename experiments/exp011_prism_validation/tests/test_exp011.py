import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/"experiments"/"exp011_prism_validation"/"scripts"))
from run_exp011 import inchikey, name_key


def test_structure_matching_accepts_equivalent_smiles():
    assert inchikey("CCO") == inchikey("OCC")


def test_prism_comma_list_smiles_uses_valid_consistent_structure():
    assert inchikey("invalid, CCO, OCC") == inchikey("CCO")
    assert inchikey("invalid, not_a_smiles") is None


def test_name_normalization_is_auxiliary_only():
    assert name_key("4-Hydroxy tamoxifen") == name_key("4 hydroxy-tamoxifen")
