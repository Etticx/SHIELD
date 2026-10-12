# SHIELD: Three-minute storytelling script

Keep the same static slide on screen throughout. The timings are rehearsal targets, not automatic slide changes. Read only the spoken paragraphs below.

## 0:00–0:30 — The business owner

Imagine you run a small bakery. Every morning, you open the doors, serve your customers, and hope the business keeps growing. Now you need a loan to buy a new oven. You bring your financial records to the bank. Behind those numbers are your savings, your staff, and your plans for the future. How can the bank understand the financial risk behind your application?

## 0:30–1:00 — The research question

That question led to my final year project, SHIELD: SME Health Indicator and Evaluator for Loan Decisions. My research asks whether machine learning can help assess bankruptcy risk while making its predictions understandable. A missed warning can expose the bank to losses. A false alarm can make a viable business look risky. Both mistakes matter, so a useful system needs careful evaluation.

## 1:00–1:40 — Financial records and risk estimate

I worked with historical company financial data and used Information Gain to select twenty financial indicators. It ranks indicators by how much information they provide about bankruptcy. These include profitability and borrowing measures. I then trained a Random Forest model, which combines the decisions of many decision trees to produce a risk estimate. Bankruptcy cases are relatively rare in the data, so I also investigated balancing the training examples and adjusting the point at which the model raises a warning.

## 1:40–2:10 — Reasons behind the estimate

But a risk number alone leaves the loan officer asking, why? SHIELD uses an explanation method called SHAP to highlight which financial indicators push the model’s estimate up or down. The web prototype presents that estimate alongside the explanation. For our bakery owner, this gives the officer specific financial signals to investigate and discuss, while the officer remains responsible for the lending decision.

## 2:10–2:45 — The finding and its trade-off

In one exploratory experiment, the model flagged thirty-five of forty-four bankrupt companies. It also flagged eighty-six companies that were not bankrupt. That shows the trade-off: catching more warning signs can bring more false alarms. Because the evaluation data had already been reused during development, these findings are preliminary. Further testing on fresh data, including data relevant to Malaysian SMEs, is needed before practical use.

## 2:45–3:00 — The human purpose

My aim is to help loan officers make more informed decisions, with financial evidence they can question and understand. For a business owner asking for that new oven, the decision should come with reasons. Thank you.

## Rehearsal notes

The script contains 369 spoken words. Aim for around 130–135 words per minute, with brief pauses. Rehearse with a timer: individual delivery speed varies. Finish comfortably before three minutes.

- Pause after the opening question and let the audience picture the bakery.
- Say “SHIELD” like the ordinary word. Say “SHAP” like “shap”.
- Emphasise “thirty-five of forty-four”, then give the false-alarm figure equal clarity.
- Use the slide as a memory aid: financial records, risk estimate, explanation, then the finding. Keep eye contact during the closing.
- Check the event rules for slide count, aspect ratio and presenter identification before submission. This file uses one static 16:9 slide with no animations.

## Optional cut if your rehearsal runs long

Omit “These include profitability and borrowing measures.” and “The web prototype presents that estimate alongside the explanation.” Keep the research limitation and false-alarm figure.

## Evidence behind the result

SOURCES AND INTERPRETATION

Project identity and prototype: README.md and UPDATE.md in the SHIELD workspace. Random Forest and SHAP implementation confirmed in backend/main.py.

Exploratory experiment: reports/focused_improvement/ba8ead7ba47c9dce/holdout_results.csv, row RF_SMOTE025_LEAF3 / Frozen OOF threshold 0.27969295288128426. TP=35, FN=9, FP=86, TN=1234. Bankrupt-class recall=35/44=79.545%; precision=35/121=28.926%. These are results of an exploratory research candidate, not a claim about the deployed prototype.

frozen_choice.json and run_config.json label the holdout as historically reused and exploratory. Do not call it independent test evidence or validated Malaysian SME performance. Current project documentation names a foreign bankruptcy dataset; geographic origin was not independently verified for this presentation.

The bakery owner is an imagined scenario. No claim is made that SHIELD has assessed a real bakery, improved lending outcomes, or demonstrated future-warning lead time.

Financial records are twenty selected indicators in the IG20 experiment. SHAP explains model contributions, not causal relationships.

Illustration: generated with the built-in ImageGen tool for this presentation. Fictional person and business. Asset: presentations/.build-shield-3min/business-owner.png.
