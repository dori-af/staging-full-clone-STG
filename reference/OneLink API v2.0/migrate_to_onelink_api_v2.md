---
title: Migrate to OneLink API v.2.0
excerpt: Compare OneLink API v1 and v2.0 side by side and follow a recommended step-by-step plan to migrate your integration.
hidden: false
---

Use this document to understand what has changed in V2.0 and how to transition to the new version effectively:

- **[V1 to V2.0 version comparison](#onelink-api-version-1-and-version-2-side-by-side-comparison)**. This section outlines the changes and new features in V2.0

- **[Recommended migration plan](#recommended-migration-plan)**. This section provides a recommended multi-step migration plan and tips to support a phased rollout of the new version.

## OneLink API Version 1 and Version 2 Side by side comparison

Use the following table to compare OneLink API v1 with v2.0 across endpoints, behaviors, validation, quota, and other functional changes.

| Area | v1 (today) | v2.0 (GA) | Recommendations |
| --- | --- | --- | --- |
| **Base URL & versioning** | `https://onelink.appsflyer.com/shortlink/v1/{onelink-id}` | `https://onelink.appsflyer.com/api/v2.0/shortlinks/{onelink-id}` | Externalize the base path in config and update the client routing. |
| **Create link (endpoint)** | **POST** `/shortlink/v1/{onelink-id}`. The optional custom shortlink ID is a **query** parameter. → Response: plain **string URL** | **POST** `/api/v2.0/shortlinks/{onelink-id}`. The optional custom shortlink ID is a **body** parameter. → Response: JSON containing the short URL under `shortlink_url`. | Align to v2.0 request syntax, update parsing to read JSON and extract `shortlink_url`, and handle the stricter validation where invalid parameters now error clearly. |
| **Get link (endpoint)** | **GET** `/shortlink/v1/{onelink-id}?id={shortlink_id}`. Shortlink ID is a **query** parameter (easy to misread as optional). → Response: JSON of short-link parameters **only** | **GET** `/api/v2.0/shortlinks/{onelink-id}/{shortlink_id}`. Shortlink ID is a mandatory **path parameter**. → Response: JSON with **payload** + **expiry** + **TTL** | This improves maintainability, since the TTL window and expiry time can be read directly. Align to v2.0 syntax and update consumers to read the payload, expiry, and TTL. |
| **Update link (endpoint)** | **PUT** `/shortlink/v1/{onelink-id}?id={shortlink_id}`. → Response: plain **string URL** | **PUT** `/api/v2.0/shortlinks/{onelink-id}/{shortlink_id}`. → Response: JSON with short URL under `shortlink_url`. | Align to v2.0 request syntax, update parsing to read JSON and extract shortlink_url, and handle the stricter validation where invalid parameters now error clearly. |
| **Delete link (endpoint)** | **DELETE** `/shortlink/v1/{onelink-id}?id={shortlink_id}` | **DELETE** `/api/v2.0/shortlinks/{onelink-id}/{shortlink_id}` | Align to v2.0 request syntax. |
| **TTL model & value** | Max TTL **31 days**. TTL auto-renews on **click or update**, unless `renew_ttl=false`. | TTL configurable **up to 730 days**. Same auto-renew logic on **click or update**. Supports **non-renewing** (one-time) links via `renew_ttl=false`. | Per-link TTL control supports one-time links (login, temp promos) or evergreen printed QRs that can live ≥1 year and longer if active, without needing to revive or delete them. Set TTL policies per use case. |
| **QR code** | Typically done via 3rd-party tools. | **New:** GET **QR image** for an existing short link. | This feature is only available for links created through the OneLink API v2.0. Get QR returns 400 for short Links created via UI/Bulk/SDK. GET QR does not count toward the monthly quota. It can be used programmatically, including generating a link and immediately getting its QR. |
| **Monthly quota (account)** | One monthly quota shared across v1. Counted: **POST/PUT/DELETE**. | During migration: quota is doubled (you get the same quota for each version, v1.0 and v2.0). Counted: POST/PUT/DELETE. Not counted: GET QR. | Dual-run is safe during migration. After v1 sunset, only the standard v2.0 quota applies. |
| **Quota / usage visibility** | Visible only in the AppsFlyer UI. | OneLink API page provides a split view for both versions during migration, and includes a quota and usage API that returns the remaining monthly count. | You can add lightweight alerts off the quota API at thresholds such as 80% or 90%. |
| **Rate limit** | **500 rps** per account. | **1000 rps** per account. | If throttling is enabled on the client side, increase the cap and maintain exponential backoff for 429 responses. |
| **Error responses** | Often plain **string** errors. | Standard JSON errors (`code`, `message`, `details`). | Update error handling and logging to parse JSON for success and error, and map error codes to monitoring for faster triage. |
| **Validation** | Basic validation | Stricter parameter validation. | Parameters that worked in v1 may fail in v2.0. Fix formatting, encoding, and required fields at the source. |
| **Encoding of parameters** | Must encode parameters yourself. | OneLink handles encoding automatically. | If a URL parameter contains a query string, encode that query string (e.g., `&` and `?`) so the parameter value does not break parsing or logic. |
| **Authentication** | API token in the header. | API token in the header. | No change in authentication. Keep existing token management best practices. |

<br />

## Recommended migration plan

Use the following steps to guide your migration from OneLink API v1 to v2.0.

| Step | Name | Description |
| --- | --- | --- |
| **01** | **Usage Inventory** | Identify and list all locations calling the OneLink API. Includes CRM systems, mobile/web backend, internal link tools, landing pages, and call-center tools. Knowing where links are created or updated helps avoid surprises. |
| **02** | **Switch base URL** | Point the API client to the new version using a configuration flag or environment variable. This keeps rollback simple and avoids code duplication. |
| **03** | **Update request & response handling** | Update response handling to read JSON for both success and error responses. Adjust the request syntax changes, including the use of path/body parameters for the shortlink ID. |
| **04** | **Fix parameter validation issues** | Test common payloads. Stricter validation may reject parameters that previously passed. Adjust formatting, encoding, and dynamic fields. This is typically the main migration effort. |
| **05** | **Pilot one low-risk flow** | Run the updated integration in a safe or low-impact environment. Verify link creation, correct returns, end-to-end resolution, and proper handling of success and error responses before moving to higher-traffic flows. |
| **06** | **Gradually roll out** | Once the pilot is stable, migrate additional flows one at a time. v1 and v2 have parallel quotas, so gradual rollout will not throttle volume. |
| **07** | **Optimize after migration** | Once on the new version: use extended TTL for long-term links, replace external QR generators with the new QR endpoint, increase throttling limits to use the 1000 RPS rate, and set internal quota alerts using the Quota endpoint for proactive monitoring. |
