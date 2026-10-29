# Five-input prediction experiment

The home page now collects net income after tax, total assets, total liabilities,
shareholders' equity and retained earnings, all in the same unit and period.
POST /experimental/accounting-predict calculates seven conventional raw ratios
and sends them to model/SHIELD_RF_7Features_SMOTE050_8020_CV5.joblib.
The model feature order is read from the artifact and checked against all seven
expected feature names. Debt ratio is sent as a fraction, not multiplied by 100.
Losses, negative equity and ratios outside [0,1] are preserved. Missing/non-finite
figures and zero denominators are rejected. The response uses threshold 0.5.

This is deliberately an experimental reaction test, not an assertion that the
ratios reproduce the dataset's unknown encoding. No scaling is guessed. Scores
are not calibrated bankruptcy probabilities. These runs do not generate lending
advice, risk severity bands, or persistent assessment logs.

The previous 20-feature workspace remains at /dataset-assessment. The original
/predict route and original model configuration remain available.

Run the existing backend and frontend as usual. The experimental model is loaded
lazily on its first request. The supplied artifact was saved with scikit-learn
1.9.0; the current local runtime is 1.6.1 and emits version warnings. The local
smoke test returned 0.6832823659513447 for the example shown in the new UI, but
matching the training dependency versions is required for reproducible inference.

Verification: backend/tests/test_experimental_accounting.py covers ratio values,
losses/negative equity, invalid denominators, non-finite values and model column /
positive-class ordering. Frontend TypeScript compilation passed. Production build
attempt failed on unavailable fonts.googleapis.com and an EPERM build directory
error; a successful production build and browser end-to-end verification are not
claimed.

Update: the original dashboard is now restored at /. Its input panel contains
only the five raw accounting amounts. POST /accounting-predict runs backend ratio
calculation, the seven-feature RF, SHAP and the existing results/advisory/log flow.
The previous 20-feature workspace remains at /dataset-assessment. A separate
calculator page is no longer used. Unit tests and TypeScript checks pass; a real
model API test returned HTTP 200 with seven SHAP entries and 68.33% for the example.
The zero-equity case returned HTTP 422. Advisory network calls were replaced with
the existing local fallback during the API verification. Encoding and dependency
version limitations described above still apply.

Latest update: / now accepts seven direct dataset-encoded feature values in [0,1].
The five accounting amount form is replaced. POST /ratios-predict passes these
seven values unchanged to the saved seven-feature RF in artifact column order.
There is no ratio calculation, additional scaling or clipping in this flow.
The workspace storage key is versioned so old five-input results cannot reappear.
The original assessment layout, SHAP, advisory and log flow are retained.
