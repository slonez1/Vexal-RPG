<template>
  <div class="stat">
    <label>{{ label }}</label>
    <div class="bar-container">
      <div class="bar-fill" :style="{ width: `${percent}%`, backgroundColor: color }"></div>
    </div>
    <small>{{ current }} / {{ max }}</small>
  </div>
</template>

<script>
export default {
  name: 'ProgressBar',
  props: {
    label: String,
    current: Number,
    max: Number,
    color: String,
  },
  computed: {
    percent() {
      return Math.min(100, Math.max(0, (this.current / this.max) * 100));
    },
  },
};
</script>

<style scoped>
.stat {
  margin-bottom: 20px;
}
.bar-container {
  height: 12px;
  background: #333;
  border-radius: 8px;
  overflow: hidden;
  margin: 5px 0;
}
.bar-fill {
  height: 100%;
  transition: width 0.5s ease;
}
</style>