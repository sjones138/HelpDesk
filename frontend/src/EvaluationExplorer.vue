<script setup lang="ts">
import { computed, ref } from 'vue';
import type { Metrics } from './api';

const props = defineProps<{ metrics: Metrics; view: 'models' | 'errors' }>();

const metric = ref<'macro_f1' | 'accuracy' | 'weighted_f1'>('macro_f1');

const selectedModel = ref<'original' | 'tuned'>('original');

const activeTestMetrics = computed(() =>
  selectedModel.value === 'tuned' && props.metrics.tuned_svm
    ? props.metrics.tuned_svm.test_metrics
    : props.metrics.test_metrics,
);

const activePerClass = computed(() =>
  selectedModel.value === 'tuned' && props.metrics.tuned_svm
    ? props.metrics.tuned_svm.per_class
    : props.metrics.per_class,
);

const predictionComparison = computed(
    () => props.metrics.tuned_svm?.prediction_comparison
);

const actual = ref('All');

const predicted = ref('All');

const query = ref('');

const limit = ref(25);

const normalize = ref(false);

const pct = (value: number) => `${(value * 100).toFixed(2)}%`;

const metricNames = {
  macro_f1: 'Macro-F1',
  accuracy: 'Accuracy',
  weighted_f1: 'Weighted-F1',
};

const ranked = computed(() =>
  [...props.metrics.cv_results].sort(
    (a, b) => b[metric.value] - a[metric.value],
  ),
);

const maxScore = computed(() =>
  Math.max(0.01, ...ranked.value.map((r) => r[metric.value])),
);

const activeErrors = computed(() =>
    selectedModel.value === 'tuned' && props.metrics.tuned_svm
        ? props.metrics.tuned_svm.errors
        : props.metrics.errors
);

const filtered = computed(() => activeErrors.value.filter(e =>
    (actual.value === 'All' || e.true_queue === actual.value) &&
    (predicted.value === 'All' || e.predicted_queue === predicted.value) &&
    (
        e.ticket_text + ' ' + e.true_queue + ' ' + e.predicted_queue
    ).toLowerCase().includes(query.value.toLowerCase())
));

const visible = computed(() => filtered.value.slice(0, limit.value));

const matrix = computed(() =>
  selectedModel.value === 'tuned' && props.metrics.tuned_svm
    ? props.metrics.tuned_svm.confusion_matrix
    : props.metrics.confusion_matrix,
);
const maxCell = computed(() => Math.max(1, ...matrix.value.flat()));

const rowSum = (row: number[]) => row.reduce((a, b) => a + b, 0);

const cellValue = (n: number, row: number[]) =>
  normalize.value
    ? `${((100 * n) / Math.max(1, rowSum(row))).toFixed(1)}%`
    : n.toLocaleString();

const cellStyle = (n: number, row: number[]) => ({
  backgroundColor: `rgba(164,255,57,${0.07 + 0.68 * (normalize.value ? n / Math.max(1, rowSum(row)) : n / maxCell.value)})`,
});

const clearFilters = () => {
  actual.value = 'All';
  predicted.value = 'All';
  query.value = '';
  limit.value = 25;
};
</script>

<template>
  <div class="eval-root" v-if="view === 'models'">
    <section class="eval-panel">
      <div class="eval-heading">
        <div>
          <h2><span>03 /</span> Held-Out Test Performance</h2>
          <p>
            Evaluated on {{ metrics.test_rows.toLocaleString() }}
            previously held-out tickets.
          </p>
        </div>

        <label class="eval-control">
          SELECT MODEL
          <select v-model="selectedModel">
            <option value="original">Original Linear SVM</option>
            <option value="tuned" :disabled="!metrics.tuned_svm">
              Tuned Linear SVM
            </option>
          </select>
        </label>
      </div>
      <div class="eval-bars">
        <div class="eval-bar-row" v-for="r in ranked" :key="r.model">
          <div class="eval-model-name">
            {{ r.model }}
            <span v-if="r.model === metrics.selected_model" class="eval-winner"
              >SELECTED</span
            >
          </div>
          <div class="eval-track">
            <div
              class="eval-fill"
              :style="{ width: `${(100 * r[metric]) / maxScore}%` }"
            ></div>
          </div>
          <strong>{{ pct(r[metric]) }}</strong>
        </div>
      </div>
      <p class="eval-note">
        The selected model was chosen by cross-validation Macro-F1, regardless
        of the metric currently displayed.
      </p>
    </section>
    <section class="eval-panel">
      <h2><span>02 /</span> Cross-Validation Results</h2>
      <p>
        Mean scores and standard deviation across five folds. These are not
        held-out test results.
      </p>
      <div class="eval-scroll">
        <table>
          <thead>
            <tr>
              <th>MODEL</th>
              <th>ACCURACY ± SD</th>
              <th>MACRO-F1 ± SD</th>
              <th>WEIGHTED-F1 ± SD</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in metrics.cv_results" :key="r.model">
              <td>{{ r.model }}</td>
              <td>
                {{ r.accuracy.toFixed(4) }} ± {{ r.accuracy_std.toFixed(4) }}
              </td>
              <td>
                {{ r.macro_f1.toFixed(4) }} ± {{ r.macro_f1_std.toFixed(4) }}
              </td>
              <td>
                {{ r.weighted_f1.toFixed(4) }} ±
                {{ r.weighted_f1_std.toFixed(4) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
    <section class="eval-panel">
      <h2><span>03 /</span> Held-Out Test Performance</h2>
      <p>
        Evaluated after model selection, on
        {{ metrics.test_rows.toLocaleString() }} previously held-out tickets.
      </p>
      <div class="eval-stats">
        <div>
          <small>ACCURACY</small>
          <strong>{{ pct(activeTestMetrics.accuracy) }}</strong>
        </div>

        <div>
          <small>MACRO-F1</small>
          <strong>{{ activeTestMetrics.macro_f1.toFixed(4) }}</strong>
        </div>

        <div>
          <small>WEIGHTED-F1</small>
          <strong>{{ activeTestMetrics.weighted_f1.toFixed(4) }}</strong>
        </div>
      </div>
      <div class="eval-scroll">
        <table>
          <thead>
            <tr>
              <th>QUEUE</th>
              <th>PRECISION</th>
              <th>RECALL</th>
              <th>F1</th>
              <th>SUPPORT</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="label in metrics.labels" :key="label">
              <td>{{ label }}</td>
              <td>{{ pct(activePerClass[label].precision) }}</td>
              <td>{{ pct(activePerClass[label].recall) }}</td>
              <td>{{ pct(activePerClass[label]['f1-score']) }}</td>
              <td>{{ activePerClass[label].support.toLocaleString() }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
    <section v-if="predictionComparison" class="eval-panel">
      <h2><span>04 /</span> Prediction Comparison</h2>

      <p>
        Comparing the original and tuned Linear SVM on the same
        {{ metrics.test_rows.toLocaleString() }} held-out tickets.
        Tuning changes which tickets are classified correctly,
        even when overall accuracy remains similar.
      </p>

      <div class="eval-stats comparison-stats">
        <div>
          <small>FIXED BY TUNING</small>
          <strong>{{ predictionComparison.fixed_by_tuning.toLocaleString() }}</strong>
        </div>

        <div>
          <small>BROKEN BY TUNING</small>
          <strong>{{ predictionComparison.broken_by_tuning.toLocaleString() }}</strong>
        </div>

        <div>
          <small>NET CHANGE</small>
          <strong>
            {{
              predictionComparison.fixed_by_tuning -
              predictionComparison.broken_by_tuning > 0 ? '+' : ''
            }}{{
              predictionComparison.fixed_by_tuning -
              predictionComparison.broken_by_tuning
            }}
          </strong>
        </div>
      </div>

      <div class="comparison-bar">
        <div
            class="comparison-both-correct"
            :style="{
        width: `${100 * predictionComparison.both_correct / metrics.test_rows}%`
      }"
            title="Both models correct"
        ></div>

        <div
            class="comparison-fixed"
            :style="{
        width: `${100 * predictionComparison.fixed_by_tuning / metrics.test_rows}%`
      }"
            title="Fixed by tuning"
        ></div>

        <div
            class="comparison-broken"
            :style="{
        width: `${100 * predictionComparison.broken_by_tuning / metrics.test_rows}%`
      }"
            title="Broken by tuning"
        ></div>

        <div
            class="comparison-both-wrong"
            :style="{
        width: `${100 * predictionComparison.both_wrong / metrics.test_rows}%`
      }"
            title="Both models wrong"
        ></div>
      </div>

      <div class="comparison-legend">
        <span><i class="legend-correct"></i> Both correct</span>
        <span><i class="legend-fixed"></i> Fixed by tuning</span>
        <span><i class="legend-broken"></i> Broken by tuning</span>
        <span><i class="legend-wrong"></i> Both wrong</span>
      </div>

      <p class="eval-note">
        The tuned SVM improved macro-F1 from
        {{ metrics.test_metrics.macro_f1.toFixed(4) }}
        to
        {{ metrics.tuned_svm!.test_metrics.macro_f1.toFixed(4) }},
        while overall accuracy changed only slightly.
        A higher macro-F1 indicates more balanced performance
        across the four support queues.
      </p>
    </section>
    <section v-if="metrics.tuned_svm" class="eval-panel">
      <h2><span>05 /</span> Hyperparameter Optimization</h2>

      <p>
        GridSearchCV evaluated 32 hyperparameter combinations using
        five-fold stratified cross-validation on the training data.
        The configuration below achieved the highest mean validation Macro-F1.
      </p>

      <div class="eval-method">
        <div>
          <small>REGULARIZATION (C)</small>
          <strong>{{ metrics.tuned_svm.best_params.classifier__C }}</strong>
        </div>

        <div>
          <small>CLASS WEIGHT</small>
          <strong>
            {{ metrics.tuned_svm.best_params.classifier__class_weight ?? 'None' }}
          </strong>
        </div>

        <div>
          <small>N-GRAM RANGE</small>
          <strong>
            {{ metrics.tuned_svm.best_params.tfidf__ngram_range.join('–') }}
          </strong>
        </div>

        <div>
          <small>MINIMUM DOCUMENT FREQUENCY</small>
          <strong>{{ metrics.tuned_svm.best_params.tfidf__min_df }}</strong>
        </div>

        <div>
          <small>BEST CROSS-VALIDATION MACRO-F1</small>
          <strong>{{ metrics.tuned_svm.best_cv_macro_f1.toFixed(4) }}</strong>
        </div>
      </div>

      <p class="eval-note">
        Hyperparameters were selected using training-set cross-validation.
        Final performance was evaluated separately on the held-out test set.
        The best grid-search score is a model-selection score, not an
        independent estimate of generalization performance.
      </p>
    </section>
    <section class="eval-panel">
      <h2><span>06 /</span> Experimental Setup</h2>
      <p>
        TF-IDF features are fitted inside each cross-validation fold to avoid
        training/validation leakage.
      </p>
      <div class="eval-method">
        <div>
          <small>VECTORIZATION</small
          ><strong>TF-IDF · unigrams + bigrams</strong>
        </div>
        <div>
          <small>VOCABULARY LIMIT</small
          ><strong>10,000 features · min_df=2</strong>
        </div>
        <div>
          <small>MODEL SELECTION</small
          ><strong>Highest mean CV Macro-F1</strong>
        </div>
        <div>
          <small>VALIDATION</small><strong>5 stratified folds · seed 42</strong>
        </div>
        <div>
          <small>HOLDOUT</small><strong>20% stratified · seed 2026</strong>
        </div>
      </div>
    </section>
  </div>
  <div class="eval-root" v-else>
    <section class="eval-panel">
      <div class="eval-heading">
        <div>
          <h2><span>00 /</span> Evaluation Model</h2>
          <p>
            Select which trained model's held-out confusion matrix you want to
            examine.
          </p>
        </div>

        <label class="eval-control">
          SELECT MODEL
          <select v-model="selectedModel">
            <option value="original">Original Linear SVM</option>
            <option value="tuned" :disabled="!metrics.tuned_svm">
              Tuned Linear SVM
            </option>
          </select>
        </label>
      </div>
    </section>
    <section class="eval-panel">
      <div class="eval-heading">
        <div>
          <h2><span>01 /</span> Confusion Matrix</h2>
          <p>
            Held-out test set · rows are actual queues, columns are predicted queues.
            Currently showing the
            {{ selectedModel === 'tuned' ? 'Tuned Linear SVM' : 'Original Linear SVM' }}.
            Select a cell to filter examples.
          </p>
        </div>
        <label class="eval-check"
          ><input type="checkbox" v-model="normalize" /> ROW PERCENTAGES</label
        >
      </div>
      <div class="eval-scroll">
        <table class="eval-matrix">
          <thead>
            <tr>
              <th>ACTUAL ↓ / PREDICTED →</th>
              <th v-for="label in metrics.labels" :key="label">{{ label }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, i) in matrix" :key="metrics.labels[i]">
              <th>{{ metrics.labels[i] }}</th>
              <td v-for="(n, j) in row" :key="j">
                <button
                  type="button"
                  class="eval-cell"
                  :class="{
                    'eval-selected':
                      actual === metrics.labels[i] &&
                      predicted === metrics.labels[j],
                  }"
                  :style="cellStyle(n, row)"
                  @click="
                    actual = metrics.labels[i];
                    predicted = metrics.labels[j];
                    limit = 25;
                  "
                >
                  {{ cellValue(n, row) }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <p class="eval-note">
        Diagonal cells represent correct predictions, while off-diagonal
        cells represent routing errors. Clicking a cell filters the
        misclassified ticket examples below. All examples correspond
        to the currently selected model.
      </p>
    </section>
    <section class="eval-panel">
      <h2><span>02 /</span> Misclassified Ticket Explorer</h2>
      <p>
        Showing {{ visible.length.toLocaleString() }} of
        {{ filtered.length.toLocaleString() }} matching errors, from
        {{ activeErrors.length.toLocaleString() }} exported held-out test
        errors.
      </p>
      <div class="eval-filters">
        <label
          >ACTUAL QUEUE<select v-model="actual" @change="limit = 25">
            <option>All</option>
            <option v-for="l in metrics.labels" :key="l">{{ l }}</option>
          </select></label
        ><label
          >PREDICTED QUEUE<select v-model="predicted" @change="limit = 25">
            <option>All</option>
            <option v-for="l in metrics.labels" :key="l">{{ l }}</option>
          </select></label
        ><label class="eval-search"
          >SEARCH TICKET TEXT<input
            v-model="query"
            placeholder="Search errors..."
            @input="limit = 25" /></label
        ><button class="eval-reset" @click="clearFilters">CLEAR FILTERS</button>
      </div>
      <div class="eval-scroll">
        <table>
          <thead>
            <tr>
              <th>TICKET EXCERPT</th>
              <th>ACTUAL</th>
              <th>PREDICTED</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(e, i) in visible" :key="i">
              <td class="eval-excerpt">{{ e.ticket_text }}</td>
              <td>{{ e.true_queue }}</td>
              <td class="eval-wrong">{{ e.predicted_queue }}</td>
            </tr>
            <tr v-if="!visible.length">
              <td colspan="3">No misclassified tickets match these filters.</td>
            </tr>
          </tbody>
        </table>
      </div>
      <button
        v-if="visible.length < filtered.length"
        class="eval-more"
        @click="limit += 25"
      >
        LOAD 25 MORE
      </button>
      <p class="eval-note">
        Examples are excerpts of public dataset records and may contain
        sensitive-looking text. Review before sharing screenshots. Filters do
        not change the trained model or its evaluation metrics.
      </p>
    </section>
  </div>
</template>

<style scoped>
.eval-root {
  display: grid;
  gap: 20px;
}
.eval-panel {
  background: #101c17;
  border: 1px solid #284234;
  border-radius: 12px;
  padding: 24px;
  color: #d8e9df;
}
.eval-panel h2 {
  margin: 0 0 8px;
  font-size: 17px;
  color: #f2fff5;
}
.eval-panel h2 span {
  color: #a4ff39;
}
.eval-panel p {
  color: #94ae9f;
  font-size: 13px;
  line-height: 1.55;
}
.eval-heading {
  display: flex;
  justify-content: space-between;
  align-items: start;
  gap: 16px;
  flex-wrap: wrap;
}
.eval-control,
.eval-check,
.eval-filters label {
  font-size: 11px;
  letter-spacing: 0.06em;
  color: #a5bcaf;
}
.eval-control select,
.eval-filters select,
.eval-filters input {
  display: block;
  margin-top: 7px;
  min-width: 150px;
  width: 100%;
  background: #0b1510;
  border: 1px solid #365745;
  border-radius: 6px;
  padding: 10px;
  color: #e6f7eb;
  font: inherit;
  letter-spacing: normal;
}
.eval-check {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}
.eval-check input {
  accent-color: #a4ff39;
}
.eval-bars {
  display: grid;
  gap: 16px;
  margin-top: 24px;
}
.eval-bar-row {
  display: grid;
  grid-template-columns: 190px 1fr 85px;
  align-items: center;
  gap: 14px;
  font-size: 13px;
}
.eval-model-name {
  font-weight: 600;
}
.eval-winner {
  font-size: 9px;
  color: #a4ff39;
  margin-left: 5px;
}
.eval-track {
  height: 15px;
  background: #21352a;
  border-radius: 3px;
  overflow: hidden;
}
.eval-fill {
  height: 100%;
  background: linear-gradient(90deg, #477b39, #a4ff39);
  border-radius: 3px;
}
.eval-bar-row strong {
  text-align: right;
  color: #a4ff39;
}
.eval-note {
  font-size: 12px !important;
  margin-top: 18px !important;
}
.eval-scroll {
  overflow-x: auto;
  margin-top: 16px;
}
.eval-scroll table {
  border-collapse: collapse;
  width: 100%;
  font-size: 12px;
  min-width: 600px;
}
.eval-scroll th,
.eval-scroll td {
  text-align: left;
  padding: 12px 10px;
  border-bottom: 1px solid #284234;
  vertical-align: top;
}
.eval-scroll th {
  color: #a4c6b0;
  font-size: 10px;
  letter-spacing: 0.05em;
}
.eval-scroll td {
  color: #d6e9dc;
}
.eval-stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin: 20px 0;
}
.eval-stats > div,
.eval-method > div {
  border: 1px solid #2b4938;
  background: #13241a;
  border-radius: 7px;
  padding: 16px;
  display: grid;
  gap: 8px;
}
.eval-stats small,
.eval-method small {
  color: #8faf9b;
  font-size: 10px;
  letter-spacing: 0.06em;
}
.eval-stats strong {
  font-size: 23px;
  color: #a4ff39;
}
.eval-method {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 10px;
  margin-top: 18px;
}
.eval-method strong {
  font-size: 12px;
}
.eval-matrix {
  table-layout: fixed;
}
.eval-matrix th:first-child {
  width: 175px;
}
.eval-matrix td {
  padding: 4px !important;
}
.eval-cell {
  width: 100%;
  min-height: 52px;
  border: 1px solid transparent;
  border-radius: 5px;
  color: #efffea;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
}
.eval-cell:hover,
.eval-cell.eval-selected {
  border-color: #a4ff39;
  outline: 1px solid #a4ff39;
}
.eval-filters {
  display: flex;
  gap: 12px;
  align-items: end;
  flex-wrap: wrap;
  margin: 20px 0;
}
.eval-filters label {
  flex: 1;
  min-width: 150px;
}
.eval-filters .eval-search {
  flex: 2;
  min-width: 200px;
}
.eval-reset,
.eval-more {
  background: #233d2d;
  border: 1px solid #4e8055;
  color: #caff9d;
  border-radius: 6px;
  padding: 11px 14px;
  cursor: pointer;
  font-size: 11px;
  font-weight: 700;
}
.eval-more {
  margin-top: 15px;
}
.eval-excerpt {
  min-width: 310px;
  max-width: 650px;
  overflow-wrap: anywhere;
  line-height: 1.55;
}
.eval-wrong {
  color: #ffae9d !important;
}
@media (max-width: 700px) {
  .eval-panel {
    padding: 16px;
  }
  .eval-bar-row {
    grid-template-columns: 1fr 70px;
    gap: 8px;
  }
  .eval-model-name {
    grid-column: 1/-1;
  }
  .eval-stats {
    grid-template-columns: 1fr;
  }
  .eval-bar-row strong {
    font-size: 12px;
  }
}
/* Prediction comparison dashboard */

.comparison-stats {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.comparison-bar {
  display: flex;
  width: 100%;
  height: 24px;
  overflow: hidden;
  border-radius: 6px;
  margin-top: 24px;
  background: #233d2d;
}

.comparison-both-correct {
  background: #477b39;
}

.comparison-fixed {
  background: #a4ff39;
}

.comparison-broken {
  background: #e98b75;
}

.comparison-both-wrong {
  background: #52665a;
}

.comparison-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 18px;
  margin-top: 14px;
  color: #a5bcaf;
  font-size: 11px;
}

.comparison-legend span {
  display: flex;
  align-items: center;
  gap: 7px;
}

.comparison-legend i {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 2px;
}

.legend-correct { background: #477b39; }
.legend-fixed { background: #a4ff39; }
.legend-broken { background: #e98b75; }
.legend-wrong { background: #52665a; }

@media (max-width: 700px) {
  .comparison-stats {
    grid-template-columns: 1fr;
  }
}
</style>
