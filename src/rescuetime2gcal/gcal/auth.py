import json

from oauthlib.oauth2 import WebApplicationClient
from requests_oauthlib import OAuth2Session

from rescuetime2gcal.gcal._consts import required_scopes


def print_refresh_token(client_id: str, client_secret: str):
    client = WebApplicationClient(client_id)
    session = OAuth2Session(
        client=client, scope=required_scopes, redirect_uri="http://localhost:8080"
    )

    authorization_url, _ = session.authorization_url("https://accounts.google.com/o/oauth2/auth")  # type: ignore
    print(
        f"""Please visit the following URL to authorize the application. Once you reach the localhost URL, the code will be after the `code=` section.

        E.g: `code=<CODE>&scope=...`

        {authorization_url}"""
    )

    authorization_code = input("Enter the authorization code: ")
    token = session.fetch_token(  # type: ignore
        "https://accounts.google.com/o/oauth2/token",
        client_secret=client_secret,
        code=authorization_code,
        authorization_response=authorization_url,
    )

    d = json.loads(json.dumps(token))
    print(f"Your refresh token is: {d['refresh_token']}")
