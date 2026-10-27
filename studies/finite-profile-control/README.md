# Finite-profile lookup counterexample

This deterministic, exhaustive synthetic control illustrates why perfect paired selectivity on exposed inputs does not establish transfer. It is not a model or human study, does not measure efficacy, and does not create or rerun a historical gate.

The universe has six two-element known sets drawn from {0, 1, 2, 3}; the unknown set is the complement. The profile-aware lookup returns memorized complements for four exposed profiles (01, 23, 02, 13), and fixed 01 for two disjoint unexposed profiles (03, 12). A separate oracle returns the complement for every profile. This is a deliberately constructed split, not a random sample.

All 12 outputs are valid. Lookup exact-pair success is **4/4 exposed and 0/2 unexposed**. Its mean unknown recall is 1 and 1/2 respectively; mean selectivity is +1 and 0. Each exposed complementary pair averages +1 selectivity; the unexposed pair averages 0. The oracle is exact on all six profiles. These are arithmetic properties of the construction, not independent observations or estimates of generalization probability. The lookup differs from a profile-blind null because it uses profile identity on exposed cases.

An output is valid only when it contains two distinct in-range integer IDs. Exact-pair success is an indicator; recall is the number of unknown IDs selected divided by two; selectivity is the number of unknown IDs selected minus one. Invalid outputs receive zero for all three metrics and remain in denominators. `rows.json` retains all 12 rows. The tests cover the full enumeration, denominators, complementary pairs and invalid outputs.

Reproduce with Python 3 and the standard library:

```sh
python -B -m unittest -v
python -B control.py
```

The files are an inspectable reconstruction of the synthetic design and outcome. Local hashes or timestamps are not independent preregistration evidence.
