<template>
  <div :class="type" class="buff-badge">
    {{ name }} ({{ timer }} turns)
  </div>
</template>

<script>
export default {
  props: {
    name: String,
    type: String,
    timer: Number
  }
};
</script>

<style scoped>
.buff-badge {
  padding: 5px 10px;
  border-radius: 3px;
  font-size: 0.85rem;
  font-weight: bold;
  margin-bottom: 5px;
  text-transform: capitalize;
}
.buff {
  background-color: #28a745;
  color: white;
}
.debuff {
  background-color: #ff4b4b;
  color: white;
}
</style>