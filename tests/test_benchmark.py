import time

import python_config
from python_config import document


def test_benchmark_document_load(huge_conf_path):
    start = time.perf_counter()
    doc = document.load(huge_conf_path)
    elapsed = time.perf_counter() - start

    assert len(doc["MEGASTRUCT"]["sub1"]) == 3000
    assert len(doc["MEGASTRUCT"]["sub2"]["sub2-sub1"]["somethings"]) == 12000
    assert doc["VAR200"] == "val200"

    print("document.load: {:.3f}s".format(elapsed))


def test_benchmark_simple_load(huge_conf_path):
    start = time.perf_counter()
    config = python_config.load(huge_conf_path)
    elapsed = time.perf_counter() - start

    assert len(config["megastruct"]["sub1"]) == 3000
    assert len(config["megastruct"]["sub2"]["sub2-sub1"]["somethings"]) == 12000
    assert config["var200"] == "val200"

    print("python_config.load: {:.3f}s".format(elapsed))
