<template>
  <div class="character-tab">
    <!-- Top Section -->
    <section class="char-details">
      <div class="char-image">
        <label for="char-pic" class="upload-label">
          <input type="file" id="char-pic" @change="uploadPic" />
          <img v-if="charImage" :src="charImage" alt="Character" />
          <div v-else class="upload-placeholder">Upload Image</div>
        </label>
      </div>
      <div class="char-info">
        <label>
          <strong>Name:</strong>
          <input v-model="charName" type="text" placeholder="Character Name" />
        </label>
        <label>
          <strong>Title:</strong>
          <input v-model="charTitle" type="text" placeholder="Character Title" />
        </label>
        <label>
          <strong>Description:</strong>
          <textarea
            v-model="charDescription"
            placeholder="Character Description"
            rows="5"
          ></textarea>
        </label>
      </div>
    </section>

    <!-- Main Section -->
    <div class="char-content">
      <!-- Left: Skills -->
      <div class="skills">
        <h3>Skills</h3>
        <ul>
          <li
            v-for="skill in skills"
            :key="skill.name"
            class="skill-item"
          >
            <strong>{{ skill.name }}</strong>: {{ skill.value }}
          </li>
        </ul>
      </div>

      <!-- Right: Spells -->
      <div class="spells">
        <h3>Spells</h3>
        <ul>
          <li
            v-for="spell in spells"
            :key="spell.name"
            class="spell-item"
          >
            <div class="spell-header">
              <strong>{{ spell.name }}</strong> <span>({{ spell.manaCost }} Mana)</span>
            </div>
            <p>{{ spell.description }}</p>
            <p><em>Mechanics: {{ spell.mechanics }}</em></p>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "CharacterTab",
  data() {
    return {
      // Character Details
      charImage: null, // For uploaded image
      charName: "Amara Silvermoon", // Default character name
      charTitle: "Knight of the Vexal", // Default title
      charDescription: "A brave warrior chosen to bear the power of the Vexal.",

      // Skills (mock data for now)
      skills: [
        { name: "One-Handed", value: "30" },
        { name: "Two-Handed", value: "15" },
        { name: "Archery", value: "20" },
        { name: "Persuasion", value: "25" },
        { name: "Athletics", value: "28" },
      ],

      // Spells (mock data for now)
      spells: [
        {
          name: "Fireball",
          manaCost: 25,
          description: "Hurl a ball of fire to deal massive damage.",
          mechanics: "Deals 50 fire damage in a 5-meter radius.",
        },
        {
          name: "Heal",
          manaCost: 15,
          description: "Restore health to yourself or an ally.",
          mechanics: "Restores 30 HP.",
        },
        {
          name: "Shield",
          manaCost: 20,
          description: "Create a temporary magical shield around yourself.",
          mechanics: "Absorbs 40 incoming damage for 5 seconds.",
        },
      ],
    };
  },
  methods: {
    uploadPic(event) {
      const file = event.target.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = (e) => {
          this.charImage = e.target.result;
        };
        reader.readAsDataURL(file);
      }
    },
  },
};
</script>

<style scoped>
/* General Structure */
.character-tab {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* Character Details Section */
.char-details {
  display: flex;
  align-items: center;
  gap: 20px;
}
.char-image {
  width: 150px;
  height: 150px;
}
.upload-label {
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 100%;
  border: 2px dashed #555;
  border-radius: 10px;
  overflow: hidden;
  cursor: pointer;
  background: #1e1e1e;
}
.upload-placeholder {
  color: #777;
  text-align: center;
  font-size: 0.9rem;
}
input[type="file"] {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  opacity: 0;
  cursor: pointer;
}
img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.char-info label {
  display: block;
  margin-bottom: 10px;
}
textarea {
  width: 100%;
  resize: none;
  border: 1px solid #444;
  background: #1e1e1e;
  color: white;
  padding: 10px;
  border-radius: 5px;
}

/* Main Content Section */
.char-content {
  display: flex;
  gap: 20px;
}
.skills,
.spells {
  flex: 1;
  background: #1e1e1e;
  padding: 15px;
  border-radius: 5px;
}
.skills h3,
.spells h3 {
  margin-bottom: 10px;
  border-bottom: 1px solid #444;
  padding-bottom: 5px;
}
.skill-item,
.spell-item {
  margin-bottom: 15px;
}
.spell-item .spell-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>