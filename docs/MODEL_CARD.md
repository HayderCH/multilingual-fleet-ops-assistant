# Public intent classifier — model card

## Summary

`public-char-word-ngram-logistic-v1` is a compact intent classifier built for this
clean-room portfolio demonstration. It recognizes four allowlisted fleet intents:
vehicle location, engine hours, maintenance status and ticket creation.

The classifier is deliberately paired with a deterministic policy layer. Its scores
are supporting routing evidence; they never bypass entity checks, operation
allowlists or the confirmation required for a simulated state-changing action.

## Implementation and provenance

- **Estimator:** logistic regression over combined character and word TF-IDF features.
- **Languages/scripts:** French, basic English, Tunisian Arabic in Arabic script and
  Tunisian Arabizi.
- **Training set:** 912 rows generated from the transparent templates in
  `src/fleet_assistant/training_data.py`.
- **Evaluation set:** 32 hand-written synthetic cases in
  `src/fleet_assistant/data/public_benchmark.json`.
- **Client data:** none.
- **Private or inherited model artifacts:** none.

The artifact can be rebuilt with:

```bash
fleet-train-classifier
```

## Evaluation

The committed build correctly classifies all 32 cases in the controlled public
benchmark. This result verifies reproducibility and the expected demo paths only.
It must not be interpreted as production accuracy or evidence of generalization to
real fleet conversations.

For a real deployment, evaluation should use an independently collected,
de-identified test set covering spelling variation, code-switching, ambiguity,
unsupported requests, adversarial input and class imbalance. Thresholds should be
selected from that evaluation rather than copied from this demonstration.

## Intended use

- demonstrating multilingual intent classification and inspectable scores;
- exercising the public API and browser demo with synthetic vehicle records;
- serving as a reproducible baseline for a new, properly governed dataset.

## Out-of-scope use

- live vehicle control, safety decisions or driver monitoring;
- automatic execution without the policy and confirmation layer;
- claims about client, production or real-user performance;
- use with personal or confidential fleet data without a separate privacy review.

## Known limitations

- The vocabulary and intent set are intentionally narrow.
- The synthetic templates do not reproduce the full variety of natural speech.
- Probability scores from logistic regression are useful for ranking but are not a
  substitute for deployment-specific calibration.
- Arabic dialect and Arabizi spelling vary substantially by speaker and region.
- Unknown intents require conservative rejection or clarification in a production
  system.
