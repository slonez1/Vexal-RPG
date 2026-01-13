<template>
  <main class="dashboard">
    <h1>Vexal RPG Dashboard</h1>

    <!-- Narrative Display -->
    <section class="narrative-display">
      <h2>Narrative</h2>
      <div class="narrative-log">
        <p v-for="(event, index) in narrativeLog" :key="index">
          {{ event }}
        </p>
      </div>
    </section>

    <!-- Action Input -->
    <section class="action-input">
      <h2>Your Action</h2>
      <form @submit.prevent="handleActionSubmit">
        <input 
          v-model="actionInput" 
          type="text" 
          placeholder="What do you want to do?"
        />
        <button type="submit">Submit</button>
      </form>
    </section>

    <!-- Control Buttons -->
    <section class="controls">
      <h2>Controls</h2>
      <button @click="advanceTime">Advance Time</button>
    </section>
  </main>
</template>

<script>
export default {
  name: "MainDashboard",
  data() {
    return {
      actionInput: "", // User action input
      narrativeLog: [ // Mock narrative log
        "Amara stands at the edge of the ruined temple, a whispering voice echoing in her mind.",
        "You hear footsteps approaching from the shadows.",
      ],
    };
  },
  methods: {
    handleActionSubmit() {
      if (!this.actionInput.trim()) {
        alert("Please enter an action.");
        return;
      }

      // Add user's action to the narrative log
      this.narrativeLog.push(`You: ${this.actionInput}`);

      // Simulate a narrative response
      this.simulateBackendResponse();

      // Clear input field
      this.actionInput = "";
    },
    simulateBackendResponse() {
      // Simulate a backend response by adding a mock narrative
      const mockResponses = [
        "The whispering grows louder, forming words: 'Seek the Bastion...'",
        "A shadowy figure steps forward, its hand outstretched.",
        "The air grows heavy; you sense an ominous presence.",
      ];
      // Pick a random mock response
      const randomIndex = Math.floor(Math.random() * mockResponses.length);
      const response = mockResponses[randomIndex];

      // Add the response to the narrative log
      this.narrativeLog.push(response);
    },
    advanceTime() {
      // Simulate advancing game time
      this.narrativeLog.push("The day draws to a close as the sun sets beyond the horizon.");
    },
  },
};
</script>

<style scoped>
.dashboard {
  flex: 1;
  padding: 20px;
}

/* Narrative Section */
.narrative-display {
  margin-bottom: 20px;
}
.narrative-log {
  background: #1e1e1e;
  padding: 10px;
  border-radius: 8px;
  height: 200px;
  overflow-y: auto;
}
.narrative-log p {
  margin: 5px 0;
  color: #ccc;
}

/* Action Input */
.action-input {
  margin-bottom: 20px;
}
input[type="text"] {
  width: calc(100% - 100px);
  padding: 10px;
  margin-right: 10px;
  border: 1px solid #333;
  background: #121212;
  color: white;
}
button {
  padding: 10px 20px;
  background-color: #4caf50;
  color: white;
  border: none;
  cursor: pointer;
}
button:hover {
  background-color: #45a049;
}

/* Control Buttons */
.controls button {
  margin-right: 10px;
  padding: 10px 20px;
  background-color: #007bff;
  color: white;
  border: none;
  cursor: pointer;
}
.controls button:hover {
  background-color: #0069d9;
}
</style>