<script setup lang="ts">
import { computed, ref } from 'vue';
import type { DatasetAudit } from './api';

const props = defineProps<{ audit: DatasetAudit; labels: string[] }>();
const selectedQueue = ref('All queues');
const stages = computed(() => {
  const a = props.audit;
  return [
    { label: 'Raw dataset', count: a.raw_rows, note: 'All source records' },
    {
      label: 'English-language tickets',
      count: a.english_rows,
      note: `${(a.raw_rows - a.english_rows).toLocaleString()} non-English records excluded`,
    },
    {
      label: 'Four supported queues',
      count: a.queue_filtered_rows,
      note: `${(a.english_rows - a.queue_filtered_rows).toLocaleString()} other-queue records excluded`,
    },
    {
      label: 'Nonempty ticket text',
      count: a.queue_filtered_rows - a.empty_text_removed,
      note: `${a.empty_text_removed.toLocaleString()} empty texts excluded`,
    },
    {
      label: 'Nonconflicting labels',
      count:
        a.queue_filtered_rows -
        a.empty_text_removed -
        a.conflicting_rows_removed,
      note: `${a.conflicting_rows_removed.toLocaleString()} conflicting-label rows excluded`,
    },
    {
      label: 'Unique cleaned tickets',
      count: a.cleaned_rows,
      note: `${a.duplicate_rows_removed.toLocaleString()} duplicate rows excluded`,
    },
  ];
});
const queues = computed(() =>
  props.labels.map((label) => ({
    label,
    count: props.audit.class_distribution[label] ?? 0,
    train: props.audit.train_distribution[label] ?? 0,
    test: props.audit.test_distribution[label] ?? 0,
  })),
);
const visibleQueues = computed(() =>
  selectedQueue.value === 'All queues'
    ? queues.value
    : queues.value.filter((q) => q.label === selectedQueue.value),
);
const maxCount = computed(() =>
  Math.max(1, ...queues.value.map((q) => q.count)),
);
const percent = (part: number, total: number) =>
  total ? `${((part / total) * 100).toFixed(1)}%` : '0.0%';
</script>

<template>
  <div class="dataset-explorer">
    <section class="dataset-panel">
      <div class="dataset-heading"><span>01 /</span> Cleaning Pipeline</div>
      <p class="dataset-muted">
        Counts are calculated during model training and exported with the
        evaluation metrics.
      </p>
      <div class="stages">
        <div v-for="(stage, index) in stages" :key="stage.label" class="stage">
          <div class="stage-top">
            <span
              >{{ String(index + 1).padStart(2, '0') }} ·
              {{ stage.label }}</span
            ><strong>{{ stage.count.toLocaleString() }}</strong>
          </div>
          <div class="stage-track">
            <div
              class="stage-fill"
              :style="{ width: percent(stage.count, audit.raw_rows) }"
            ></div>
          </div>
          <small>{{ stage.note }}</small>
        </div>
      </div>
    </section>

    <section class="dataset-panel">
      <div class="dataset-heading"><span>02 /</span> Class Distribution</div>
      <p class="dataset-muted">
        The final dataset is imbalanced. Technical Support is the largest queue.
      </p>
      <label class="filter-label" for="dataset-queue">QUEUE FILTER</label>
      <select id="dataset-queue" v-model="selectedQueue" class="queue-select">
        <option>All queues</option>
        <option v-for="label in labels" :key="label">{{ label }}</option>
      </select>
      <div v-for="q in visibleQueues" :key="q.label" class="queue-item">
        <div class="queue-top">
          <span>{{ q.label }}</span
          ><strong
            >{{ q.count.toLocaleString() }}
            <small>({{ percent(q.count, audit.cleaned_rows) }})</small></strong
          >
        </div>
        <div class="queue-track">
          <div
            class="queue-fill"
            :style="{ width: percent(q.count, maxCount) }"
          ></div>
        </div>
        <small
          >{{ q.train.toLocaleString() }} train ·
          {{ q.test.toLocaleString() }} test</small
        >
      </div>
    </section>

    <section class="dataset-panel dataset-wide">
      <div class="dataset-heading"><span>03 /</span> Stratified Holdout</div>
      <p class="dataset-muted">
        A fixed 80/20 split preserves queue proportions. Model selection uses
        five-fold stratified cross-validation on the training partition only.
      </p>
      <div
        class="split-bar"
        role="img"
        :aria-label="`${audit.train_rows} training tickets and ${audit.test_rows} test tickets`"
      >
        <div
          class="split-train"
          :style="{ width: percent(audit.train_rows, audit.cleaned_rows) }"
        >
          TRAIN
        </div>
        <div
          class="split-test"
          :style="{ width: percent(audit.test_rows, audit.cleaned_rows) }"
        >
          TEST
        </div>
      </div>
      <div class="split-legend">
        <span
          ><b>{{ audit.train_rows.toLocaleString() }}</b> training tickets</span
        ><span
          ><b>{{ audit.test_rows.toLocaleString() }}</b> held-out test
          tickets</span
        >
      </div>
      <div class="methodology">
        <span>RANDOM STATE: 2026</span><span>STRATIFIED: YES</span
        ><span>CV FOLDS: 5</span><span>SELECTION METRIC: MACRO-F1</span>
      </div>
      <p class="dataset-muted">
        The held-out test set is used for final evaluation, not for selecting
        the winning model. The pipeline fits TF-IDF inside each training fold to
        avoid leakage.
      </p>
    </section>
  </div>
</template>

<style scoped>
.dataset-explorer {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px;
}
.dataset-panel {
  background: #101d18;
  border: 1px solid #294538;
  border-radius: 12px;
  padding: 24px;
  min-width: 0;
}
.dataset-wide {
  grid-column: 1/-1;
}
.dataset-heading {
  font-size: 17px;
  font-weight: 750;
  color: #e7f6eb;
}
.dataset-heading span {
  color: #a4ff39;
}
.dataset-muted {
  color: #91aa9c;
  font-size: 13px;
  line-height: 1.6;
  margin: 8px 0 20px;
}
.stages {
  display: grid;
  gap: 18px;
}
.stage-top,
.queue-top,
.split-legend {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  color: #e7f6eb;
  font-size: 13px;
}
.stage-top strong,
.queue-top strong {
  color: #a4ff39;
  font-variant-numeric: tabular-nums;
}
.stage-track,
.queue-track {
  height: 8px;
  background: #26392e;
  border-radius: 100px;
  overflow: hidden;
  margin: 8px 0 5px;
}
.stage-fill,
.queue-fill {
  height: 100%;
  background: linear-gradient(90deg, #407e46, #a4ff39);
  border-radius: 100px;
}
.stage small,
.queue-item > small,
.queue-top small {
  color: #91aa9c;
  font-size: 11px;
}
.filter-label {
  display: block;
  color: #91aa9c;
  font-size: 11px;
  letter-spacing: 1px;
  margin-bottom: 7px;
}
.queue-select {
  width: 100%;
  background: #16281f;
  border: 1px solid #365440;
  color: #e7f6eb;
  padding: 10px;
  border-radius: 6px;
  margin-bottom: 20px;
}
.queue-item {
  margin-bottom: 18px;
}
.split-bar {
  display: flex;
  height: 42px;
  border-radius: 6px;
  overflow: hidden;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 1px;
}
.split-train {
  background: #a4ff39;
  color: #102016;
  display: flex;
  align-items: center;
  justify-content: center;
}
.split-test {
  background: #467f5a;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
}
.split-legend {
  margin: 12px 0 20px;
  color: #91aa9c;
}
.split-legend b {
  color: #e7f6eb;
}
.methodology {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin: 18px 0;
}
.methodology span {
  border: 1px solid #365440;
  border-radius: 4px;
  padding: 8px 10px;
  color: #b8d9c1;
  font-size: 11px;
  letter-spacing: 0.3px;
}
@media (max-width: 850px) {
  .dataset-explorer {
    grid-template-columns: 1fr;
  }
  .dataset-wide {
    grid-column: auto;
  }
}
</style>
