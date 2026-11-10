<script setup lang="ts">
import { ref, onMounted, computed, nextTick } from 'vue';
import * as echarts from 'echarts';
import DatasetExplorer from './DatasetExplorer.vue';
import EvaluationExplorer from './EvaluationExplorer.vue';
import ResponsibleAI from './ResponsibleAI.vue';
import {
  getMetrics,
  classify,
  submitFeedback,
  type Metrics,
  type Prediction,
} from './api';
type Tab =
  'overview' | 'dataset' | 'classify' | 'models' | 'errors' | 'responsible';
const tab = ref<Tab>('overview');
const metrics = ref<Metrics | null>(null);
const loadError = ref('');
const ticket = ref(
  'I cannot connect to the company VPN after changing my password.',
);
const prediction = ref<Prediction | null>(null);
const busy = ref(false);
const message = ref('');
const correction = ref('');
const errorFilter = ref('');
const examples = [
  'I cannot connect to the company VPN after changing my password.',
  'My laptop crashes when I start the application.',
  'The product I purchased is missing a component.',
  'I need to update the billing address on my account.',
];
const fmt = (v: number) => `${(v * 100).toFixed(2)}%`;
const filteredErrors = computed(
  () =>
    metrics.value?.errors
      .filter((e) =>
        (e.ticket_text + ' ' + e.true_queue + ' ' + e.predicted_queue)
          .toLowerCase()
          .includes(errorFilter.value.toLowerCase()),
      )
      .slice(0, 100) ?? [],
);
async function load() {
  try {
    metrics.value = await getMetrics();
    await nextTick();
    drawCharts();
  } catch (e) {
    loadError.value =
      'Metrics unavailable. Run the training export script, then refresh.';
  }
}
async function run() {
  if (ticket.value.trim().length < 3) return;
  busy.value = true;
  correction.value = '';
  message.value = '';
  prediction.value = null;
  try {
    prediction.value = await classify(ticket.value);
    correction.value = '';
  } catch (e) {
    message.value =
      'Classification unavailable. Check that the Django server and trained artifacts are ready.';
  } finally {
    busy.value = false;
  }
}
async function saveFeedback() {
  if (
    !prediction.value ||
    !correction.value ||
    correction.value === prediction.value.queue
  )
    return;
  message.value = '';
  try {
    await submitFeedback(
      ticket.value,
      prediction.value.queue,
      correction.value,
    );
    message.value =
      'Correction saved for human review. Model not automatically retrained.';
  } catch (e) {
    message.value = 'Could not save feedback.';
  }
}
function switchTab(t: Tab) {
  tab.value = t;
  nextTick(drawCharts);
}
function drawCharts() {
  if (!metrics.value) return;
  const m = metrics.value;
  const bar = document.getElementById('model-chart');
  if (bar) {
    const chart = echarts.init(bar);
    chart.setOption({
      backgroundColor: 'transparent',
      tooltip: { trigger: 'axis' },
      grid: { left: 120, right: 20, top: 20, bottom: 45 },
      xAxis: {
        type: 'value',
        max: 1,
        axisLabel: { color: '#82988d' },
        splitLine: { lineStyle: { color: '#21352d' } },
      },
      yAxis: {
        type: 'category',
        data: m.cv_results.map((r) => r.model),
        axisLabel: { color: '#b5d1c2' },
        axisLine: { show: false },
      },
      series: [
        {
          type: 'bar',
          data: m.cv_results.map((r) => r.macro_f1),
          itemStyle: { color: '#a4ff39' },
          barWidth: 18,
        },
      ],
    });
    window.addEventListener('resize', () => chart.resize(), { once: true });
  }
  const heat = document.getElementById('matrix-chart');
  if (heat) {
    const chart = echarts.init(heat);
    const data = m.confusion_matrix.flatMap((row, i) =>
      row.map((v, j) => [j, i, v]),
    );
    chart.setOption({
      tooltip: { position: 'top' },
      grid: { left: 110, right: 25, top: 10, bottom: 75 },
      xAxis: {
        type: 'category',
        data: m.labels,
        axisLabel: { color: '#b5d1c2', rotate: 25, fontSize: 10 },
      },
      yAxis: {
        type: 'category',
        data: m.labels,
        axisLabel: { color: '#b5d1c2', fontSize: 10 },
      },
      visualMap: {
        min: 0,
        max: Math.max(...data.map((d) => Number(d[2])), 1),
        calculable: false,
        show: false,
        inRange: { color: ['#15251d', '#4f8d3a', '#a4ff39'] },
      },
      series: [
        {
          type: 'heatmap',
          data,
          label: { show: true, color: '#ffffff' },
          emphasis: { itemStyle: { shadowBlur: 10, shadowColor: '#a4ff39' } },
        },
      ],
    });
    window.addEventListener('resize', () => chart.resize(), { once: true });
  }
}
onMounted(load);
</script>
<template>
  <div class="shell">
    <aside class="sidebar">
      <div class="logo">
        <span class="logo-mark">⌁</span> HELP<span>DESK</span
        ><small>TICKET INTELLIGENCE // 01</small>
      </div>
      <div class="nav-label">// NAVIGATION</div>
      <button
        v-for="item in [
          { id: 'overview', name: 'Command Center', icon: '▦' },
          { id: 'dataset', name: 'Dataset Explorer', icon: '▤' },
          { id: 'classify', name: 'Live Classifier', icon: '⌘' },
          { id: 'models', name: 'Model Laboratory', icon: '◈' },
          { id: 'errors', name: 'Error Explorer', icon: '⚠' },
          { id: 'responsible', name: 'Responsible AI', icon: '◇' },
        ]"
        :key="item.id"
        class="nav"
        :class="{ active: tab === item.id }"
        @click="switchTab(item.id as Tab)"
      >
        <span>{{ item.icon }}</span
        >{{ item.name }}
      </button>
      <div class="sidebar-bottom">
        <span class="pulse"></span> SYSTEM
        {{ metrics ? 'OPERATIONAL' : 'AWAITING MODEL'
        }}<small>ICS 652 // MACHINE LEARNING</small>
      </div>
    </aside>
    <main>
      <header>
        <div class="breadcrumb">
          HELPDESK <span>/</span> {{ tab.toUpperCase() }}
        </div>
        <div class="header-right">
          <span class="tag">● LOCAL ENVIRONMENT</span
          ><span class="avatar">HD</span>
        </div>
      </header>
      <div class="content">
        <div class="eyebrow">
          //
          {{
            tab === 'overview'
              ? 'SYSTEM OVERVIEW'
              : tab === 'dataset'
                ? 'DATA PREPARATION'
                : tab === 'classify'
                  ? 'INFERENCE ENGINE'
                  : tab === 'models'
                    ? 'EXPERIMENTAL ANALYSIS'
                    : tab === 'errors'
                      ? 'MODEL DIAGNOSTICS'
                      : 'RESPONSIBLE AI'
          }}
        </div>
        <h1>
          {{
            tab === 'overview'
              ? 'Ticket Intelligence'
              : tab === 'dataset'
                ? 'Dataset Explorer'
                : tab === 'classify'
                  ? 'Live Classification'
                  : tab === 'models'
                    ? 'Model Laboratory'
                    : tab === 'errors'
                      ? 'Error Explorer'
                      : 'Responsible AI'
          }}<span class="cursor">_</span>
        </h1>
        <p class="subtitle">
          {{
            tab === 'overview'
              ? 'Classical machine learning meets support queue automation.'
              : tab === 'dataset'
                ? 'Explore dataset cleaning, class balance, and the stratified train/test split.'
                : tab === 'classify'
                  ? 'Submit a ticket. Inspect the predicted route and supporting terms.'
                  : tab === 'models'
                    ? 'Five-fold cross-validation, honest metrics, reproducible experiments.'
                    : tab === 'errors'
                      ? 'Investigate failures and overlapping ticket categories.'
                      : 'Understand model scope, limitations, privacy, and human oversight.'
          }}
        </p>
        <div v-if="loadError" class="notice">{{ loadError }}</div>
        <template v-if="tab === 'overview'"
          ><div class="stats">
            <div class="stat">
              <label>SELECTED MODEL</label
              ><strong>{{ metrics?.selected_model ?? '—' }}</strong
              ><small>HIGHEST CV MACRO-F1</small>
            </div>
            <div class="stat">
              <label>TEST ACCURACY</label
              ><strong>{{
                metrics?.test_metrics ? fmt(metrics.test_metrics.accuracy) : '—'
              }}</strong
              ><small>HELD-OUT TEST SET</small>
            </div>
            <div class="stat">
              <label>MACRO-F1</label
              ><strong>{{
                metrics?.test_metrics
                  ? metrics.test_metrics.macro_f1.toFixed(4)
                  : '—'
              }}</strong
              ><small>ALL CLASSES WEIGHTED EQUALLY</small>
            </div>
            <div class="stat">
              <label>DATASET SIZE</label
              ><strong>{{ metrics?.dataset_rows ?? '—' }}</strong
              ><small>CLEANED ENGLISH TICKETS</small>
            </div>
          </div>
          <div class="panel-grid">
            <section class="panel">
              <h2><span>01 /</span> Model Comparison</h2>
              <p>Cross-validation Macro-F1 · training split only</p>
              <div id="model-chart" class="chart"></div>
            </section>
            <section class="panel">
              <h2><span>02 /</span> Routing Architecture</h2>
              <p>Inference pipeline · deterministic feature extraction</p>
              <div class="pipeline">
                <div>INCOMING TICKET <b>TEXT INPUT</b></div>
                <i>↓</i>
                <div>TF-IDF VECTORIZATION <b>10K FEATURES</b></div>
                <i>↓</i>
                <div>
                  {{ metrics?.selected_model ?? 'CLASSIFIER' }} <b>INFERENCE</b>
                </div>
                <i>↓</i>
                <div>SUPPORT QUEUE <b>HUMAN REVIEW</b></div>
              </div>
            </section>
          </div>
          <section class="panel full">
            <h2><span>03 /</span> Confusion Matrix</h2>
            <p>Rows = actual queue · columns = predicted queue</p>
            <div id="matrix-chart" class="chart large"></div></section
        ></template>
        <template v-if="tab === 'dataset'"
          ><DatasetExplorer
            v-if="metrics?.dataset_audit"
            :audit="metrics.dataset_audit"
            :labels="metrics.labels"
          />
          <div v-else class="notice">
            Dataset audit unavailable. Rerun the training export and restart
            Django.
          </div></template
        >
        <template v-if="tab === 'classify'"
          ><div class="panel-grid">
            <section class="panel">
              <h2><span>01 /</span> Ticket Input</h2>
              <p>Text is processed by the exported scikit-learn pipeline.</p>
              <textarea
                v-model="ticket"
                maxlength="5000"
                placeholder="Enter a support ticket..."
              ></textarea>
              <div class="form-footer">
                <span>{{ ticket.length }} / 5000 CHARS</span
                ><button
                  class="primary"
                  :disabled="busy || ticket.trim().length < 3"
                  @click="run"
                >
                  {{ busy ? 'PROCESSING...' : '▶ RUN CLASSIFIER' }}
                </button>
              </div>
              <div class="samples">
                <label>QUICK LOAD //</label
                ><button
                  v-for="(sample, i) in examples"
                  :key="i"
                  @click="
                    ticket = sample;
                    prediction = null;
                    correction = '';
                    message = '';
                  "
                >
                  EXAMPLE_0{{ i + 1 }} ↗
                </button>
              </div>
            </section>
            <section class="panel">
              <h2><span>02 /</span> Inference Output</h2>
              <p>Prediction scores are not calibrated probabilities.</p>
              <div v-if="prediction" class="prediction">
                <label>ROUTING DESTINATION</label
                ><strong>{{ prediction.queue }}</strong>
                <div class="status">
                  ● MODEL PREDICTION · REVIEW RECOMMENDED
                </div>
                <h3>POSITIVE FEATURE CONTRIBUTIONS</h3>
                <div v-if="prediction.contributions.length">
                  <div
                    class="term"
                    v-for="term in prediction.contributions"
                    :key="term.term"
                  >
                    <span>{{ term.term }}</span>
                    <div class="term-bar">
                      <i
                        :style="{
                          width:
                            (term.weight /
                              (prediction.contributions[0]?.weight || 1)) *
                              100 +
                            '%',
                        }"
                      ></i>
                    </div>
                    <small>{{ term.weight.toFixed(3) }}</small>
                  </div>
                </div>
                <p v-else>
                  No positive contributing terms available for this prediction.
                </p>
                <div class="feedback">
                  <label>INCORRECT ROUTE? SUBMIT CORRECTION</label
                  ><select v-model="correction">
                    <option value="" disabled>SELECT CORRECT QUEUE</option>
                    <option
                      v-for="label in metrics?.labels ?? [
                        'Customer Service',
                        'Technical Support',
                        'IT Support',
                        'Product Support',
                      ]"
                      :key="label"
                    >
                      {{ label }}
                    </option></select
                  ><button
                    class="secondary"
                    :disabled="!correction || correction === prediction.queue"
                    @click="saveFeedback"
                  >
                    SAVE CORRECTION
                  </button>
                </div>
              </div>
              <div v-else class="empty">
                &gt; AWAITING INPUT<span class="cursor">_</span
                ><small>CLASSIFICATION OUTPUT WILL APPEAR HERE</small>
              </div>
              <div v-if="message" class="notice">{{ message }}</div>
            </section>
          </div></template
        >
        <template v-if="tab === 'responsible'"
          ><ResponsibleAI v-if="metrics" :metrics="metrics"
        /></template>
        <template v-if="tab === 'models' || tab === 'errors'"
          ><EvaluationExplorer v-if="metrics" :metrics="metrics" :view="tab"
        /></template>
        <footer>
          HELPDESK // RESEARCH DEMONSTRATION
          <span>ASSISTIVE ROUTING ONLY · HUMAN OVERSIGHT REQUIRED</span>
        </footer>
      </div>
    </main>
  </div>
</template>
