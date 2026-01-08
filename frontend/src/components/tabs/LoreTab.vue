<template>
  <div class="lore-tab">
    <!-- Bastion Section -->
    <section class="bastion">
      <h2>Bastion Progress</h2>
      <p><strong>Progress:</strong> {{ bastionProgress.currentPieces }} / {{ bastionProgress.totalPieces }}</p>
      <p><strong>Next Step:</strong> {{ bastionProgress.nextStep || "To be determined" }}</p>
    </section>

    <hr />

    <!-- People Section -->
    <section class="people">
      <h2>People</h2>
      <ul>
        <li
          v-for="person in people"
          :key="person.name"
        >
          <strong>{{ person.name }}</strong>: {{ person.description }}
        </li>
      </ul>
    </section>

    <hr />

    <!-- Places Section -->
    <section class="places">
      <h2>Places</h2>
      <ul>
        <li
          v-for="place in places"
          :key="place.name"
        >
          <strong>{{ place.name }}</strong>: {{ place.description }}
        </li>
      </ul>
    </section>
  </div>
</template>

<script>
export default {
  name: "LoreTab",
  data() {
    return {
      bastionProgress: {
        currentPieces: 0,
        totalPieces: 7,
        nextStep: "Find a sage who knows about the Bastion fragments.",
      },
      people: [
        { name: "Elandor", description: "A wandering sage with knowledge of the Bastion." },
        { name: "Lady Ravenna", description: "A noblewoman with ties to the lost Bastion lore." },
      ],
      places: [
        { name: "Whispering Woods", description: "A dense forest where a fragment is rumored to be hidden." },
        { name: "Eldara Keep", description: "An abandoned keep holding ancient secrets." },
      ],
    };
  },
};
</script>

<style scoped>
/* Layout and adjustments for styling */
</style>