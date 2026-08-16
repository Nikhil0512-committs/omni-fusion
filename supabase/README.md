# Supabase Configuration

This directory contains the database schema and configuration for the Omni-Fusion project.

**Project Ref:** [PENDING USER INPUT]
**Region:** [PENDING USER INPUT]

*Note: Do not place any secret keys in this file or any committed file. The anon/service keys must reside strictly in `.env` and `.env.local`.*

## Storage Bucket
The project requires a Supabase Storage bucket named `reports`. 
- **Type:** Private (or Public, depending on security requirements. We recommend Private, with the backend signing URLs, but if no authentication is used, Public is acceptable for now.)

