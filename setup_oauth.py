"""
setup_oauth.py — Run this ONCE on your local machine to get YouTube OAuth credentials.
Then paste the output into GitHub Secrets as YOUTUBE_OAUTH_CREDENTIALS.

Usage:
  1. Download your OAuth2 client_secret.json from Google Cloud Console
  2. Run: python setup_oauth.py --client-secrets client_secret.json
  3. A browser will open — sign in with the YouTube channel owner's Google account
  4. Copy the JSON output into GitHub → Settings → Secrets → YOUTUBE_OAUTH_CREDENTIALS
"""

import json
import argparse
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--client-secrets",
        default="client_secret.json",
        help="Path to client_secret.json from Google Cloud Console"
    )
    args = parser.parse_args()

    print("🔐 Starting OAuth2 flow for YouTube...")
    print("   A browser will open — sign in with the YouTube channel owner's account\n")

    flow = InstalledAppFlow.from_client_secrets_file(args.client_secrets, SCOPES)
    creds = flow.run_local_server(port=0)

    output = {
        "token":         creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri":     creds.token_uri,
        "client_id":     creds.client_id,
        "client_secret": creds.client_secret,
        "scopes":        list(creds.scopes),
    }

    print("\n✅ OAuth2 credentials obtained!\n")
    print("=" * 60)
    print("Copy the JSON below into GitHub Secrets as:")
    print("  YOUTUBE_OAUTH_CREDENTIALS")
    print("=" * 60)
    print(json.dumps(output, indent=2))
    print("=" * 60)

    with open("youtube_credentials.json", "w") as f:
        json.dump(output, f, indent=2)
    print("\n💾 Also saved to: youtube_credentials.json (don't commit this!)")


if __name__ == "__main__":
    main()
