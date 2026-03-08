<script setup lang="ts">
import LegalShell from '../components/layout/LegalShell.vue'
</script>

<template>
  <LegalShell
    title="Privacy Policy"
    summary="This policy explains what ApplyPilot collects, why we collect it, and how uploaded resume data is handled."
    updated-on="March 8, 2026"
  >
    <section class="legal-section">
      <h2>Overview</h2>
      <p>
        ApplyPilot helps users upload resumes, analyze resume structure, optimize content against job targets, and
        export improved versions. We only use submitted information to operate, secure, and improve the service.
      </p>
    </section>

    <section class="legal-section">
      <h2>Information We Collect</h2>
      <ul>
        <li>Uploaded resume files and the text extracted from those files.</li>
        <li>Job descriptions, target role notes, and optimization instructions submitted through the workflow.</li>
        <li>Technical information such as browser type, device type, IP address, and basic usage logs.</li>
        <li>Messages sent to ApplyPilot support at hello@applypilot.com.</li>
      </ul>
    </section>

    <section class="legal-section">
      <h2>How We Use Information</h2>
      <ul>
        <li>To parse, analyze, optimize, and export resume content requested by the user.</li>
        <li>To maintain platform reliability, prevent abuse, and debug operational issues.</li>
        <li>To improve product quality, workflow design, and resume optimization performance.</li>
        <li>To respond to support requests, legal notices, or security incidents.</li>
      </ul>
    </section>

    <section class="legal-section">
      <h2>How We Share Information</h2>
      <p>
        ApplyPilot may share data with infrastructure, storage, analytics, or AI processing providers only when needed
        to operate the service. We may also disclose information if required by law, to protect users, or to enforce
        our Terms of Service.
      </p>
    </section>

    <section class="legal-section">
      <h2>Retention and Security</h2>
      <p>
        We retain information only as long as reasonably necessary for product operation, support, and compliance.
        ApplyPilot uses reasonable administrative and technical safeguards, but no internet service can guarantee
        absolute security.
      </p>
    </section>

    <section class="legal-section">
      <h2>Your Choices</h2>
      <p>
        You should only upload resumes or job content that you are permitted to share. To request deletion of support
        messages or launch-era workflow data, contact hello@applypilot.com.
      </p>
    </section>

    <section class="legal-section">
      <h2>Contact</h2>
      <p>Questions about this policy can be sent to hello@applypilot.com.</p>
    </section>
  </LegalShell>
</template>
