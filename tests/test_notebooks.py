import pytest
import os


def test_system_model_v2_notebook_debt_market():
    notebook = "notebooks/system_model_v2/notebook_debt_market.ipynb"
    result = os.popen(f"jupyter nbconvert --to script --execute --stdout {notebook} | python3").read()
    assert "1" in result
