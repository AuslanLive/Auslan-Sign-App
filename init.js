<script type="module">
  // Import the functions you need from the SDKs you need
  import { initializeApp } from "https://www.gstatic.com/firebasejs/10.14.1/firebase-app.js";
  import { getAnalytics } from "https://www.gstatic.com/firebasejs/10.14.1/firebase-analytics.js";
  // TODO: Add SDKs for Firebase products that you want to use
  // https://firebase.google.com/docs/web/setup#available-libraries

  // Your web app's Firebase configuration
  // For Firebase JS SDK v7.20.0 and later, measurementId is optional
  const firebaseConfig = {
    apiKey: "AIzaSyCLn2nnrYyGBOw75m3EITMoO6zXh-cBNug",
    authDomain: "auslan-194e5.firebaseapp.com",
    projectId: "auslan-194e5",
    storageBucket: "auslan-194e5.appspot.com",
    messagingSenderId: "257406282962",
    appId: "1:257406282962:web:cc54aa21e76ae22351110b",
    measurementId: "G-PM9MSMRT39"
  };

  // Initialize Firebase
  const app = initializeApp(firebaseConfig);
  const analytics = getAnalytics(app);
</script>