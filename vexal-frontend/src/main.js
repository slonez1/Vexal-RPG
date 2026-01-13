import { createApp } from "vue";
import App from "./App.vue";
import axios from "axios";

const app = createApp(App);

// Global game state accessible to all components
app.config.globalProperties.$gameState = {
  state: null, // Placeholder for the game state
  async fetchState() {
    try {
      const response = await axios.get("http://127.0.0.1:8000/api/state");
      this.state = response.data;
      console.log("Game state fetched:", this.state);
    } catch (error) {
      console.error("Failed to fetch game state:", error);
    }
  },
};

app.mount("#app");