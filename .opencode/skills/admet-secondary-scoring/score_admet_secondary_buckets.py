#!/usr/bin/env python3
"""Score non-NR/SR ADMET-AI outputs into three heuristic buckets."""

import argparse
import json
from pathlib import Path


def load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def clamp01(value):
    return max(0.0, min(1.0, float(value)))


def safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def level(score, thresholds):
    if score is None:
        return "unknown"
    if score >= thresholds["high"]:
        return "high"
    if score >= thresholds["moderate_low"]:
        return "moderate"
    return "low"


def transform(value, rule):
    fn = rule["transform"]
    if fn == "identity":
        return clamp01(value)
    if fn == "one_minus":
        return clamp01(1.0 - float(value))
    if fn == "binary_inverse":
        return 0.0 if value == rule.get("positive_value", 1) else 1.0
    if fn == "piecewise":
        breaks = rule["breakpoints"]
        scores = rule["scores"]
        # Piecewise function is always in 4 pieces (3 breakpoints). Could switch to a for loop to be more flexible there.
        if value < breaks[0]:
            return scores[0]
        if value < breaks[1]:
            return scores[1]
        if value < breaks[2]:
            return scores[2]
        return scores[3]
    raise ValueError(f"Unsupported transform: {fn}")


def ignored_key(key, cfg):
    return any(key.startswith(p) for p in cfg["ignored_key_prefixes"]) or any(
        key.endswith(s) for s in cfg["ignored_key_suffixes"]
    )


def score_family(record, family_cfg, thresholds):
    items, num, den = [], 0.0, 0.0
    for rule in family_cfg["rules"]:
        raw = safe_float(record.get(rule["key"]))
        if raw is None:
            continue
        score = transform(raw, rule)
        weight = float(rule["weight"])
        items.append({"key": rule["key"], "raw": raw, "normalized": round(score, 3)})
        num += weight * score
        den += weight
    # Might look confusing, but this is so that the weights don't necessarily need to sum to 1
    fam_score = round(num / den, 3) if den else None
    return {
        "bucket": family_cfg["bucket"],
        "summary": family_cfg["summary"],
        "score": fam_score,
        "level": level(fam_score, thresholds),
        "evidence": items,
    }


def bucket_scores(family_results, thresholds):
    by_bucket = {}
    for result in family_results.values():
        if result["score"] is None:
            continue
        by_bucket.setdefault(result["bucket"], []).append(result["score"])
    return {
        bucket: {
            "score": round(sum(scores) / len(scores), 3),
            "level": level(sum(scores) / len(scores), thresholds),
        }
        for bucket, scores in by_bucket.items()
    }


def annotate(family_results, groups, thresholds):
    out = {}
    for label, families in groups.items():
        hits = []
        for family in families:
            score = family_results.get(family, {}).get("score")
            if score is not None and score >= thresholds["moderate_low"]:
                hits.append(
                    {"family": family, "score": score, "level": level(score, thresholds)}
                )
        out[label] = sorted(hits, key=lambda x: x["score"], reverse=True)
    return out


def analyze_record(record, cfg):
    families = {
        name: score_family(record, family_cfg, cfg["thresholds"])
        for name, family_cfg in cfg["families"].items()
    }
    used = {
        rule["key"]
        for family_cfg in cfg["families"].values()
        for rule in family_cfg["rules"]
        if rule["key"] in record
    }
    ignored = sorted(k for k in record if ignored_key(k, cfg))
    excluded = sorted(k for k in record if k in cfg["excluded_keys"])
    unmapped = sorted(
        k
        for k in record
        if k not in used
        and k not in excluded
        and k not in ignored
    )
    return {
        "family_scores": families,
        "bucket_scores": bucket_scores(families, cfg["thresholds"]),
        "annotations": annotate(families, cfg["annotation_groups"], cfg["thresholds"]),
        "excluded_keys_present": excluded,
        "ignored_keys_present": ignored,
        "unmapped_keys_present": unmapped,
    }


def analyze_key_catalog(keys, cfg):
    used = {
        rule["key"]
        for family_cfg in cfg["families"].values()
        for rule in family_cfg["rules"]
    }
    return {
        "mapped_by_family": {
            name: [rule["key"] for rule in family_cfg["rules"] if rule["key"] in keys]
            for name, family_cfg in cfg["families"].items()
        },
        "excluded_keys_present": sorted(k for k in keys if k in cfg["excluded_keys"]),
        "ignored_keys_present": sorted(k for k in keys if ignored_key(k, cfg)),
        "unmapped_keys_present": sorted(
            k
            for k in keys
            if k not in used
            and k not in cfg["excluded_keys"]
            and not ignored_key(k, cfg)
        ),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Bucket non-NR/SR ADMET-AI outputs into exposure modifiers, liability phenotypes, and chemistry-quality signals."
    )
    parser.add_argument("predictions_json", help="ADMET-AI predictions as a dict, list of dicts, or list of keys.")
    parser.add_argument("mapping_json", help="Bucket mapping configuration JSON.")
    parser.add_argument("-o", "--output", help="Optional output JSON path.")
    args = parser.parse_args()

    payload = load_json(args.predictions_json)
    cfg = load_json(args.mapping_json)

    if isinstance(payload, list) and all(isinstance(x, str) for x in payload):
        result = {"mode": "key_catalog", "results": analyze_key_catalog(payload, cfg)}
    else:
        records = payload if isinstance(payload, list) else [payload]
        result = {
            "mode": "scored_records",
            "results": [analyze_record(record, cfg) for record in records],
        }

    text = json.dumps(result, indent=2)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text)


if __name__ == "__main__":
    main()