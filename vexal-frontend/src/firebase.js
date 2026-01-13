// Firebase App (the core Firebase SDK) is always required
import { initializeApp } from "firebase/app";
import { getFirestore } from "firebase/firestore";

// Your Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyD1usqjZao9ymkSOQfd_SOe8a7O0nRsHqQ",
  authDomain: "fir-vexal-rpg.firebaseapp.com",
  projectId: "fir-vexal-rpg",
  storageBucket: "fir-vexal-rpg.firebasestorage.app",
  messagingSenderId: "284749962684",
  appId: "1:284749962684:web:8537509df4597568729fb9"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Firestore
const db = getFirestore(app);

export { db };