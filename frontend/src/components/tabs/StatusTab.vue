<template>
  <div class="status-tab">
    <div class="status-layout">
      <!-- Character Stats -->
      <div class="character-stats">
        <h2>Character</h2>
        <ul>
          <li><strong>Armor Class:</strong> {{ characterStats.armorClass }}</li>
          <li><strong>Noise:</strong> {{ characterStats.noise }}</li>
          <li><strong>Bulk:</strong> {{ characterStats.bulk }}</li>
        </ul>
      </div>

      <!-- Conditions -->
      <div class="conditions">
        <h2>Conditions</h2>
        <ul>
          <li
            v-for="condition in conditions"
            :key="condition.name"
            :class="[condition.type]"
          >
            <strong>{{ condition.name }}</strong>: {{ condition.description }}
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "StatusTab",
  data() {
    return {
      // Character Stats
      characterStats: {
        armorClass: 18,
        noise: 12,
        bulk: 55,
      },

      // Buffs and Debuffs for Testing
      conditions: [
        {
          name: "Blessed",
          type: "buff", // CSS class for styling
          description: "You feel the divine favor of your deity, increasing your attack rolls by +2.",
        },
        {
          name: "Poisoned",
          type: "debuff", // CSS class for styling
          description: "You are poisoned, taking 2 damage per turn.",
        },
        {
          name: "Exhausted",
          type: "debuff",
          description: "Your stamina is drained. Movement is halved.",
        },
      ],
    };
  },
};
</script>

<style scoped>
/* Layout setup for the Status Tab */
.status-layout {
  display: flex;
  gap: 20px;
}

/* Character Stats Section */
.character-stats {
  flex: 1;
  background: #1e1e1e;
  padding: 15px;
  border-radius: 5px;
}
.character-stats h2 {
  color: #4caf50;
  margin-bottom: 10px;
}
.character-stats ul {
  list-style-type: none;
  padding: 0;
}
.character-stats li {
  margin-bottom: 10px;
  font-size: 1rem;
}

/* Conditions Section */
.conditions {
  flex: 2;
  background: #1e1e1e;
  padding: 15px;
  border-radius: 5px;
}
.conditions h2 {
  color: #ff9800;
  margin-bottom: 10px;
}
.conditions ul {
  list-style-type: none;
  padding: 0;
}
.conditions li {
  background: #333;
  margin-bottom: 10px;
  padding: 10px;
  border-radius: 5px;
  font-size: 1rem;
}
/* Different styling for buffs vs debuffs */
.buff {
  border-left: 4px solid #4caf50; /* Green border for buffs */
}
.debuff {
  border-left: 4px solid #ff4b4b; /* Red border for debuffs */
}
</style>