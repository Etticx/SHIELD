SHIELD — approximate conversion experiment, 29 October 2026

What actually ran
Existing seven-feature Taiwanese-origin dataset (local Italian-labelled file),
existing RF SMOTE 0.5 / 80:20 / CV5 artifact, fixed cutoff 0.5.
No Polish data, no retraining, and no website modifications.
5,000 synthetic evaluation profiles, including 1,000 base profiles and four
matched changes per base. Separate seed123 synthetic raw reference sample.
Seven methods = identity plus minmax and quantile under three reference mixes.
35,000 predictions total. These are NOT 35,000 independent companies.

Important scope limitation
This is a SYNTHETIC REFERENCE simulation. No real external raw-ratio sample was
obtained or validated. Therefore it does not complete a real external-reference
validation of Claude's proposals. It demonstrates behaviour and sensitivity.

Mixed-reference results (400 strong / 400 weak synthetic base profiles)
                         Strong mean score    Weak mean score
Raw identity                  59.60%               60.79%
Synthetic minmax              49.52%               70.58%
Synthetic percentile           6.77%               34.94%

At the fixed 0.5 model cutoff:
Identity flags 318 strong and 400 weak profiles.
Minmax flags 160 strong and 400 weak profiles.
Percentile flags 0 strong and 65 weak profiles.
These are scenario flags, NOT false positives/true positives: no real outcomes.

Directional check: combined financial improvement, 1,000 paired cases
Identity: score fell 445, rose 244, unchanged within 0.2pp 311.
Minmax: score fell 523, rose 427, unchanged 50.
Percentile: score fell 779, rose 219, unchanged 2.
Directional expectations are heuristics, not financial outcome ground truth.

Sensitivity with the SAME 5,000 evaluation cases and SAME fixed RF
Changing mixed reference to strong-only reference:
Minmax changes 679 binary decisions (13.58%).
Percentile changes 2,664 binary decisions (53.28%).
Changing mixed reference to weak-only reference:
Minmax changes 2,135 decisions (42.70%).
Percentile changes 161 decisions (3.22%).
Reference groups differ in both composition and size. This is a stress test,
not an estimate of sensitivity to realistic Malaysian population differences.

Finding
Both conversions can make selected examples appear more plausible. Neither is
established as a reliable bridge to this RF. Percentile mapping improved some
directional checks, but reference choice strongly controls the predictions.
Do not replace the website's input conversion on this evidence.
Real external raw financial statements with known outcomes are still needed
to assess either proposal. Original normalization is not recovered.

Reproduction: venv/Scripts/python.exe tools/approximate_mapping_experiment.py
See metadata.json for model hash, raw bounds, exact feature order and warnings.
The model artifact/runtime sklearn versions differ; results are local-runtime
observations. FINDINGS.txt and summary.csv contain all group summaries.
all_35000_predictions.csv contains every input, mapped feature and score.
