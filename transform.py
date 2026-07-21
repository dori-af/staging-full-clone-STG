#!/usr/bin/env python3
"""
Transform devhub's guides/apis markdown into the Bi-Directional Sync
folder structure (category folders + _order.yaml), matching the current
production sidebar hierarchy, and write it into ./docs (run from inside
staging-full-clone-STG).
"""
import os
import shutil
import json
import base64
import urllib.request
import urllib.error
import yaml

DEVHUB_ROOT = "../devhub/docs"
DEST_ROOT = "docs"
SOURCE_SUBDIRS = ["guides", "apis"]
SKIP_NAMES = {".DS_Store", ".gitkeep"}

README_API_KEY = os.environ.get("README_API_KEY")
README_API_BRANCH = os.environ.get("README_API_BRANCH", "stable")
README_API_BASE = "https://api.readme.com/v2"


def fetch_from_readme_api(slug):
    """Fall back to the live production ReadMe API (v2, Bearer auth) for a
    slug that has no matching file in devhub. Returns a dict with
    title/excerpt/body/hidden on success, or None on any failure."""
    if not README_API_KEY:
        return None
    url = f"{README_API_BASE}/branches/{README_API_BRANCH}/guides/{slug}"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {README_API_KEY}")
    req.add_header("Accept", "application/json")
    req.add_header("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        data = payload.get("data", payload)
        content = data.get("content") or {}
        excerpt = content.get("excerpt")
        body = content.get("body") or content.get("markdown") or content.get("value") or ""
        return {
            "title": data.get("title"),
            "excerpt": excerpt,
            "body": body,
            "hidden": data.get("hidden", False),
        }
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = e.read().decode("utf-8")[:200]
        except Exception:
            pass
        print(f"  API fetch failed for '{slug}': HTTP {e.code} {detail}")
        return None
    except Exception as e:
        print(f"  API fetch failed for '{slug}': {e}")
        return None


def split_frontmatter(content):
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            fm_raw = parts[1]
            body = parts[2].lstrip("\n")
            try:
                fm = yaml.safe_load(fm_raw) or {}
            except yaml.YAMLError:
                fm = {}
            return fm, body
    return {}, content


def build_source_index():
    index = {}
    flagged = []
    for sub in SOURCE_SUBDIRS:
        base = os.path.join(DEVHUB_ROOT, sub)
        for dirpath, dirnames, filenames in os.walk(base):
            for fname in filenames:
                if fname in SKIP_NAMES:
                    continue
                path = os.path.join(dirpath, fname)
                ext = os.path.splitext(fname)[1].lower()
                if ext in (".yaml", ".yml", ".json", ".html"):
                    flagged.append(path)
                    continue
                if ext != ".md":
                    continue
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                except Exception as e:
                    print(f"WARN: could not read {path}: {e}")
                    continue
                fm, body = split_frontmatter(content)
                slug = fm.get("slug") or os.path.splitext(fname)[0]
                if slug in index:
                    print(f"WARN: duplicate slug '{slug}' at {path} (keeping {index[slug]['path']})")
                    continue
                index[slug] = {
                    "path": path,
                    "dir": dirpath,
                    "fname": fname,
                    "frontmatter": fm,
                    "body": body,
                }
    return index, flagged


# Each node: (slug, title, hidden, children_or_None)
TREE = [
    ("AppsFlyer SDKs", [
        ("getting-started", "Getting started", False, [
            ("dj-getting-started", "Developer Journey", False, None),
            ("integrate-sdk-with-ai", "Integrate SDK with AI", False, None),
            ("sdk-installation", "SDK installation", False, None),
            ("sdk-integration", "SDK integration", False, None),
            ("integration-testing", "Integration testing", False, None),
            ("in-app-events-sdk", "In-app events", False, None),
            ("conversion-data", "Conversion data", False, None),
            ("push-notifications", "Push notifications", False, None),
            ("uninstall-measurement", "Uninstall measurement", False, None),
            ("gs-ad-revenue", "Ad revenue", False, None),
            ("purchase-and-subscription-validation", "Purchase and subscription validation", False, None),
            ("preserve-user-privacy-1", "Preserve user privacy", False, None),
            ("send-consent-for-dma-compliance", "Send consent for DMA compliance", False, None),
            ("accordion", "Images cache", True, None),
            ("purchase-connector", "Purchase connector", True, None),
            ("coming-back-soon", "Coming back soon...", True, None),
            ("common-data-structures", "Common data structures", True, [
                ("direct-deep-linking-1", "Input parameters", True, None),
                ("android-sample-payloads", "Android sample payloads", True, None),
                ("ios-sample-payloads", "iOS sample payloads", True, None),
            ]),
        ]),
        ("android-sdk", "Android SDK", False, [
            ("preserve-user-privacy", "Preserve user privacy", True, None),
            ("android-sdk-7", "Android SDK 7", False, [
                ("migrate-android-sdk-to-v7", "Migrate Android SDK to V7", False, None),
                ("install-android-sdk-7", "Install Android SDK 7", False, None),
                ("integrate-android-sdk-7", "Integrate Android SDK 7", False, None),
            ]),
            ("install-android-sdk", "Install SDK", False, None),
            ("integrate-android-sdk", "Integrate SDK", False, None),
            ("testing-android", "Test integration", False, [
                ("manual-testing-android", "Manual testing", True, None),
            ]),
            ("in-app-events-android", "In-app events", False, None),
            ("conversion-data-android", "Conversion data", False, None),
            ("push-notifications-android", "Push notifications", False, None),
            ("ad-revenue-1", "Ad revenue", False, [
                ("temp-1", "temp", True, None),
            ]),
            ("uninstall-measurement-android", "Uninstall measurement", False, None),
            ("purchase-validation-android", "Purchase and subscription validation", False, [
                ("validate-and-log-purchase-android", "Validate and log purchase", False, None),
                ("purchase-connector-android", "Purchase connector", False, None),
            ]),
            ("oaid", "OAID", False, None),
            ("preserve-user-privacy-android", "Preserve user privacy", False, None),
            ("android-send-consent-for-dma-compliance", "Send consent for DMA compliance", False, [
                ("temp-2", "temp", True, None),
            ]),
            ("android-release-notes", "Android Release Notes", False, None),
            ("purchase-validation", "Purchase validation", True, None),
            ("branch-migration-android", "Branch Migration Navigator on Android", True, None),
            ("branch-migration-ios", "Branch Migration Navigator on iOS", True, None),
            ("android-legacy-security-plugin", "Android legacy security plugin", True, None),
            ("android-security-plugin", "Android security plugin", True, None),
        ]),
        ("ios-sdk", "iOS SDK", False, [
            ("ios-release-notes", "iOS Release Notes", False, None),
            ("ios-sdk-7", "iOS SDK 7", False, [
                ("migrate-ios-sdk-to-v7", "Migrate iOS SDK to V7", False, None),
                ("install-ios-sdk-7", "Install iOS SDK 7", False, None),
                ("integrate-ios-sdk-7", "Integrate iOS SDK 7", False, None),
            ]),
            ("install-ios-sdk", "Install SDK", False, None),
            ("integrate-ios-sdk", "Integrate SDK", False, None),
            ("testing-ios", "Test integration", False, [
                ("manual-testing-ios", "Manual testing", True, None),
            ]),
            ("in-app-events-ios", "In-app events", False, None),
            ("conversion-data-ios", "Conversion data", False, None),
            ("push-notifications-ios", "Push notifications", False, None),
            ("uninstall-measurement-ios", "Uninstall measurement", False, None),
            ("ad-revenue-2", "Ad revenue", False, None),
            ("purchase-validation-ios", "Purchase and subscription validation", False, [
                ("validate-and-log-purchase-ios", "Validate and log purchase", False, None),
                ("purchase-connector-ios", "Purchase connector", False, None),
            ]),
            ("preserve-user-privacy-ios", "Preserve user privacy", False, None),
            ("ios-send-consent-for-dma-compliance", "Send consent for DMA compliance", False, None),
        ]),
        ("android-sdk-reference", "Android SDK reference", False, [
            ("android-sdk-reference-appsflyerlib", "AppsFlyerLib", False, None),
            ("android-sdk-reference-deeplinklistener", "DeepLinkListener", False, None),
            ("android-sdk-reference-deeplink", "DeepLink", False, None),
            ("android-sdk-reference-deeplinkresult", "DeepLinkResult", False, None),
            ("android-sdk-reference-appsflyerconversionlistener", "AppsFlyerConversionListener", False, None),
            ("android-sdk-reference-appsflyerinapppurchasevalidatorlistener", "AppsFlyerInAppPurchaseValidatorListener (LEGACY)", False, None),
            ("android-sdk-reference-sharecrosspromotionhelper", "CrossPromotionHelper", False, None),
            ("android-sdk-reference-shareinvitehelper", "ShareInviteHelper", False, None),
            ("android-sdk-reference-linkgenerator", "LinkGenerator", False, None),
            ("android-sdk-reference-appsflyerrequestlistener", "AppsFlyerRequestListener", False, None),
            ("appsflyeradrevenue", "AppsFlyerAdRevenue [LEGACY]", False, None),
            ("android-sdk-reference-appsflyerinapppurchasevalidationcallback", "AppsFlyerInAppPurchaseValidationCallback", False, None),
            ("android-sdk-reference-appsflyerconsent", "AppsFlyerConsent", False, None),
            ("temp", "temp", True, None),
            ("appsflyerinapppurchasevalidationcallback", "AppsFlyerInAppPurchaseValidationCallback", True, None),
        ]),
        ("ios-sdk-reference", "iOS SDK reference", False, [
            ("ios-sdk-reference-appsflyerlib", "AppsFlyerLib", False, None),
            ("ios-sdk-reference-appsflyerlibdelegate", "AppsFlyerLibDelegate", False, None),
            ("ios-sdk-reference-appsflyerdeeplink", "AppsFlyerDeepLink", False, None),
            ("ios-sdk-reference-appsflyerdeeplinkdelegate", "AppsFlyerDeepLinkDelegate", False, None),
            ("ios-sdk-reference-appsflyerdeeplinkresult", "AppsFlyerDeepLinkResult", False, None),
            ("ios-sdk-reference-appsflyercrosspromotionhelper", "AppsFlyerCrossPromotionHelper", False, None),
            ("ios-sdk-reference-appsflyershareinvitehelper", "AppsFlyerShareInviteHelper", False, None),
            ("ios-sdk-reference-appsflyerlinkgenerator", "AppsFlyerLinkGenerator", False, None),
            ("appsflyeradrevenue-1", "AppsFlyerAdRevenue [LEGACY]", False, None),
            ("temp-appsflyerlib", "temp - AppsFlyerLib", True, None),
            ("ios-sdk-reference-appsflyerconsent", "AppsFlyerConsent", False, None),
        ]),
        ("unity-plugin", "Unity Plugin", False, [
            ("installation", "Installation", False, None),
            ("introduction-unity", "Introduction", False, None),
            ("basicintegration", "Integration", False, None),
            ("testing", "Test Integration", False, None),
            ("inappevents", "In-App Events", False, None),
            ("conversion-data-unity", "Conversion data", False, None),
            ("dmaconsent", "Sending Consent Data for DMA Compliance", False, None),
            ("uninstallmeasurement", "Uninstall Measurement", False, None),
            ("deeplinkintegrate", "Deep Linking - Installation", False, None),
            ("unifieddeeplink", "Unified Deep Linking (UDL)", False, None),
            ("userinvite", "User Invite", False, None),
            ("troubleshooting", "Troubleshooting", False, None),
            ("pushnotifications", "Push Notifications", False, None),
            ("migrationguide", "Migration guide from v4", False, None),
            ("api", "API reference", False, None),
            ("ad-revenue-unity", "Ad revenue", False, None),
            ("purchaseconnectorunity", "Purchase Connector", True, None),
            ("purchase-subscription-validation-unity", "Purchase and subscription validation", False, [
                ("validate-and-log-unity", "Validate and log purchase", False, None),
                ("purchase-connector-unity", "Purchase connector", False, None),
            ]),
        ]),
        ("react-native-plugin", "React Native Plugin", False, [
            ("rn_installation", "Installation", False, None),
            ("rn_integration", "Integration", False, None),
            ("rn_expoinstallation", "Expo Installation", False, None),
            ("rn_testing", "Test integration", False, None),
            ("rn_inappevents", "In-App Events", False, None),
            ("rn_deeplinkintegrate", "Deep linking integration", False, None),
            ("rn_uninstallmeasurement", "Uninstall measurement", False, None),
            ("rn_unifieddeeplink", "Unified Deep Linking (UDL)", False, None),
            ("rn_expodeeplinkintegration", "Expo Deep linking integration", False, None),
            ("rn_userinvite", "User invite", False, None),
            ("rn_api", "API reference", False, None),
            ("rn_cmp", "Send consent for DMA compliance", False, None),
            ("rn_purchaseconnector", "Purchase Connector", False, None),
            ("rn_espintegration", "ESP (Email Service Provider) Integration", False, None),
        ]),
        ("unreal-engine-plugin", "Unreal Engine Plugin", False, [
            ("ue-installation", "Installation", True, None),
            ("ue-integration", "Integration", True, None),
            ("ue-deep-linking", "Deep Linking", True, None),
            ("ue-images-cache", "UE Images cache", True, None),
            ("deep-linking", "Deep linking", True, None),
            ("ue-api", "API reference", True, None),
        ]),
    ]),
    ("Deep Linking and OneLink", [
        ("dl_getting_started", "Getting started", False, None),
        ("dl_work_flow", "Deep Linking work flow", False, None),
        ("dl_android_overview", "Android", False, [
            ("dl_android_init_setup", "Android initial setup", False, None),
            ("dl_android_unified_deep_linking", "Android Unified Deep Linking", False, None),
            ("dl_android_ocds_ddl", "Android Extended Deferred Deep Linking", False, None),
            ("dl_android_dl_post_event", "Android Deep Linking post user event", False, None),
            ("dl_android_gcd_legacy", "Android Legacy APIs", False, None),
            ("dl_android_user_invite", "Android User Invite", False, None),
            ("dl_android_attr_params_based_click", "Android: Set parameters based on the clicked URL domain", False, None),
            ("dl_android_esp_2_setup", "Android Deep Linking ESP 2.0", False, None),
        ]),
        ("dl_ios_overview", "iOS", False, [
            ("dl_ios_init_setup", "iOS initial setup", False, None),
            ("dl_ios_unified_deep_linking", "iOS Unified Deep Linking", False, None),
            ("dl_ios_ocds_ddl", "iOS Extended Deferred Deep Linking", False, None),
            ("dl_ios_dl_post_event", "iOS Deep Linking post user event", False, None),
            ("dl_ios_gcd_legacy", "iOS Legacy APIs", False, None),
            ("dl_ios_user_invite", "iOS user invite", False, None),
            ("dl_ios_private_relay", "iOS deferred deep linking with iOS Private Relay", False, None),
            ("dl_ios_attr_params_based_click", "iOS: Set parameters based on the clicked URL domain", False, None),
            ("dl_ios_esp_2_setup", "iOS Deep Linking ESP 2.0", False, None),
        ]),
        ("dl_user_invite", "User invite attribution", False, None),
        ("dl_smart_script_v2", "Smart Script: Web tool", False, [
            ("create-direct-click-url", "Smart script for cross-platform", False, None),
            ("dl_legacy_smart_script_v1", "[Legacy] OneLink Smart Script V1", False, None),
            ("test-1", "test", True, None),
        ]),
        ("dl_smart_banner_migration_guide", "Smart Banner: Web tool", False, [
            ("dl_smart_banner_v2", "OneLink Smart Banner V2", False, None),
            ("dl_smart_banner_v1", "Smart Banner v1", True, None),
        ]),
    ]),
    ("Apple App Clips integration", [
        ("app-clip-sdk-integration", "App Clip SDK integration", False, [
            ("in-app-events", "In-app events for App Clips", False, None),
            ("app-clip-to-full-app-install", "App Clip-to-full app install configuration", False, None),
        ]),
        ("app-clip-overview", "Overview", False, None),
    ]),
    ("Gaming and CTV SDKs (BETA)", [
        ("c2s-integrations-overview", "Overview", False, None),
        ("set-customer-user-id", "Set Customer User ID", False, None),
        ("unity-steam", "Steam", False, [
            ("steam-vanilla", "Steam C++", False, None),
            ("unreal-steam", "Unreal Steam", False, None),
        ]),
        ("unity-epic", "Epic", False, [
            ("unreal-epic", "Unreal Epic", False, None),
            ("epic-vanilla", "Epic C++", False, None),
        ]),
        ("meta-quest2-unity", "Meta Quest (Oculus)", False, [
            ("meta-quest2-unreal", "Meta Quest 2 Unreal", False, None),
        ]),
        ("unity-nativepc", "Native", False, [
            ("unreal-nativepc", "Native PC Unreal", False, None),
            ("nativepc-vanilla", "Native PC C++", False, None),
        ]),
        ("roku-brighscript", "CTV", False, None),
        ("ctv-log-event-event-parameters", "Log Event - Event Parameters", False, None),
        ("google-play-games-on-pc", "Google Play Games on PC", False, None),
    ]),
    ("Auxiliary tools", [
        ("install-the-idfv-test-tool-app", "Install the IDFV test tool app", False, None),
    ]),
    ("Integrations", [
        ("google-icm-integration-odm-sdk", "Google ICM integration (ODM SDK)", True, None),
    ]),
    ("Server-to-server events API (for mobile)", [
        ("s2s-events-api3-overview", "Overview", False, None),
    ]),
    ("App list API", [
        ("app-list-ad-nets-overview", "Overview", False, None),
    ]),
    ("App management API V2.0", [
        ("app-management-v2-overview", "Overview", False, None),
        ("app-management-v2-errors", "Error messages", False, None),
        ("app-management-v2-formats", "Supported formats", False, None),
    ]),
    ("User management", [
        ("bulk-users-management-overview", "Overview", False, None),
    ]),
    ("Click Signing API", [
        ("click-sign-api-overview", "Overview", False, None),
    ]),
]


def make_frontmatter(title, excerpt, hidden, metadata=None):
    fm = {"title": title}
    if excerpt:
        fm["excerpt"] = excerpt
    fm["hidden"] = hidden
    if metadata:
        fm["metadata"] = metadata
    return "---\n" + yaml.safe_dump(fm, sort_keys=False, allow_unicode=True).strip() + "\n---\n\n"


def write_page(dest_path, slug, title, sidebar_hidden, source_index, missing_log, unlisted_log, api_fetched_log):
    entry = source_index.get(slug)
    hidden = sidebar_hidden
    metadata = None
    if entry:
        old_fm = entry["frontmatter"]
        content_field = old_fm.get("content")
        excerpt = content_field.get("excerpt") if isinstance(content_field, dict) else None
        if not excerpt:
            excerpt = old_fm.get("excerpt")
        body = entry["body"]
        metadata = old_fm.get("metadata")
        # Combine hidden signals: sidebar class, devhub's own `hidden` field,
        # and privacy.view == anyone_with_link (unlisted-by-link, treat as hidden
        # rather than silently making it fully public).
        if old_fm.get("hidden") is True:
            hidden = True
        priv = old_fm.get("privacy")
        if isinstance(priv, dict) and priv.get("view") == "anyone_with_link":
            hidden = True
            unlisted_log.append((slug, dest_path))
    else:
        api_result = fetch_from_readme_api(slug)
        fetched_body = (api_result or {}).get("body") or ""
        # Sanity check: a legitimate page body should never itself contain
        # another full frontmatter block. If it does, the API returned the
        # wrong page's content (slug collision/stale cache) -- discard it.
        if api_result and "\n---" in fetched_body[:2000] and fetched_body.lstrip().startswith("---"):
            print(f"  API fetch for '{slug}' returned a body with an embedded frontmatter block, discarding as bad data.")
            api_result = None
        if api_result:
            excerpt = api_result.get("excerpt")
            body = fetched_body
            if api_result.get("hidden"):
                hidden = True
            api_fetched_log.append((slug, dest_path))
        else:
            excerpt = None
            body = f"<!-- TODO: no source content found in devhub or via API for slug '{slug}'. Placeholder generated. -->\n"
            missing_log.append((slug, dest_path))
    with open(dest_path, "w", encoding="utf-8") as f:
        f.write(make_frontmatter(title, excerpt or "", hidden, metadata) + body)
    if entry:
        asset_dir = os.path.join(entry["dir"], os.path.splitext(entry["fname"])[0])
        if os.path.isdir(asset_dir):
            image_exts = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"}
            found_images = [
                f for f in os.listdir(asset_dir)
                if os.path.splitext(f)[1].lower() in image_exts
            ]
            if found_images:
                dest_asset_dir = os.path.join(
                    os.path.dirname(dest_path), os.path.splitext(os.path.basename(dest_path))[0]
                )
                os.makedirs(dest_asset_dir, exist_ok=True)
                for fname in found_images:
                    shutil.copy2(os.path.join(asset_dir, fname), os.path.join(dest_asset_dir, fname))


def process_children(children, parent_dir, source_index, missing_log, unlisted_log, api_fetched_log):
    order = []
    for slug, title, hidden, subchildren in children:
        order.append(slug)
        if subchildren:
            node_dir = os.path.join(parent_dir, slug)
            os.makedirs(node_dir, exist_ok=True)
            write_page(os.path.join(node_dir, "index.md"), slug, title, hidden, source_index, missing_log, unlisted_log, api_fetched_log)
            process_children(subchildren, node_dir, source_index, missing_log, unlisted_log, api_fetched_log)
        else:
            write_page(os.path.join(parent_dir, f"{slug}.md"), slug, title, hidden, source_index, missing_log, unlisted_log, api_fetched_log)
    with open(os.path.join(parent_dir, "_order.yaml"), "w", encoding="utf-8") as f:
        yaml.safe_dump(order, f, sort_keys=False, allow_unicode=True)


def main():
    if README_API_KEY:
        print(f"README_API_KEY found, will use branch '{README_API_BRANCH}' as a fallback for slugs missing from devhub.")
    else:
        print("No README_API_KEY set, missing slugs will get TODO placeholders instead.")

    source_index, flagged = build_source_index()
    missing_log = []
    unlisted_log = []
    api_fetched_log = []
    top_order = []
    for category_name, children in TREE:
        top_order.append(category_name)
        cat_dir = os.path.join(DEST_ROOT, category_name)
        os.makedirs(cat_dir, exist_ok=True)
        process_children(children, cat_dir, source_index, missing_log, unlisted_log, api_fetched_log)

    top_order_path = os.path.join(DEST_ROOT, "_order.yaml")
    with open(top_order_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(top_order, f, sort_keys=False, allow_unicode=True)

    lines = []
    lines.append(f"{len(source_index)} source files indexed from devhub.")
    lines.append(f"{len(api_fetched_log)} pages had no devhub file but were fetched live from the ReadMe API:")
    for slug, path in api_fetched_log:
        lines.append(f"  - {slug} -> {path}")
    lines.append(f"\n{len(missing_log)} pages had NO matching content anywhere (devhub or API), placeholders written:")
    for slug, path in missing_log:
        lines.append(f"  - {slug} -> {path}")
    lines.append(f"\n{len(unlisted_log)} pages were 'anyone_with_link' in devhub, marked hidden:true here:")
    for slug, path in unlisted_log:
        lines.append(f"  - {slug} -> {path}")
    lines.append(f"\n{len(flagged)} files skipped as OpenAPI/non-markdown (handle manually):")
    for path in flagged:
        lines.append(f"  - {path}")

    report = "\n".join(lines)
    print("\n" + report)
    with open("transform_report.txt", "w", encoding="utf-8") as f:
        f.write(report + "\n")
    print("\nFull report also written to transform_report.txt")


if __name__ == "__main__":
    main()
