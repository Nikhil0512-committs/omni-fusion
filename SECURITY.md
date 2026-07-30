# Security Policy

## Supported Versions
Only the latest main branch is currently supported for security updates.

## Architecture & Threat Model Mitigations

Omni-Fusion employs a defense-in-depth approach to secure clinical data, AI models, and healthcare integrations. The following outlines the key security measures integrated into the platform:

1. **Authentication & Identity Verification**
   - JWT validation is enforced on all API endpoints via FastAPI dependencies (`get_current_user`).
   - Doctor registration requires a valid medical registration number, enforcing strict role gating on the backend.

2. **Authorization & IDOR Prevention**
   - **Row Level Security (RLS)** is strictly applied to all Supabase tables (`profiles`, `predictions`, `reports`, `abdm_consents`), ensuring that database queries only return data belonging to the authenticated user.
   - Endpoint-level ownership checks prevent IDOR (Insecure Direct Object Reference) by ensuring that even if a valid UUID is guessed, backend validation confirms the caller owns or is clinically linked (via `doctor_patient_links`) to the resource.

3. **Rate Limiting (DDoS & Brute Force Mitigation)**
   - Expensive endpoints, such as AI model inference (`/predict`), LLM generation (`/copilot`), file uploads, and report generation, are restricted using `SlowAPI`.
   - WebSockets (e.g., Live Monitor) enforce rate limiting on the initial handshake.

4. **Storage Security**
   - Supabase storage buckets (e.g., `reports`) are strictly marked as `public = false`.
   - Access to artifacts requires short-lived signed URLs generated server-side, mitigating unauthorized bulk downloads or UUID guessing.

5. **AI Prompt Injection Guardrails**
   - Generative AI integrations (Gemini API) use explicit `system_instruction` boundaries to separate clinical logic and constraints from user-provided data.

6. **Server-Side Request Forgery (SSRF) Protection**
   - Any external webhook callbacks (e.g., ABDM network communications) are routed through a strict allow-list function blocking private, loopback, and non-approved top-level domains.

## Reporting a Vulnerability

If you discover a potential vulnerability, please do NOT file a public issue. Instead, contact the repository owner privately.
