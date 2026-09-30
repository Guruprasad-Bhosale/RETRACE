"""Benchmark Corpus Modules."""

from benchmarks.corpus.commerce_lab import load_commerce_lab_suite
from benchmarks.corpus.synthetic import load_synthetic_suite

__all__ = ["load_commerce_lab_suite", "load_synthetic_suite"]
