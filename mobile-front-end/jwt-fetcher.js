"use strict";

// Please note that this class it not meant to be used in a production setting, it is simply
// an example of how one might create logic to fetch access tokens and perform token refreshes.

export class JwtFetcher {
  constructor() {
    this.accessToken = null;
    this.refreshToken = sessionStorage.getItem("sso-token") || null;

    this.expirationTimestamp = sessionStorage.getItem("sso-expire") || null;
  }

  getActiveToken() {
    if (!this.accessToken && !this.refreshToken) {
      return this.createTokenFromRedirectCode();
    }

    if (this.accessToken && !this.isExpired()) {
      return Promise.resolve(this.accessToken);
    }

    // since values are expired, we can clear stale token data
    sessionStorage.removeItem("sso-token");
    sessionStorage.removeItem("sso-expire");

    return this.regenerateToken();
  }

  async createTokenFromRedirectCode() {
    const code = new URLSearchParams(window.location.search).get("code");
    if (!code) {
      throw Error("Cannot create token if no redirect code is present!");
    }

    // Once we have our code, we need to retrieve the code verifier that we had saved from the previous
    // redirect.html file.
    const codeVerifier = sessionStorage.getItem("pkceVerifier");
    sessionStorage.removeItem("pkceVerifier");

    const body = new URLSearchParams();
    body.append("grant_type", "authorization_code");
    body.append("code", code);
    body.append("code_verifier", codeVerifier);
    body.append("client_id", "se-mobile-app");
    body.append("redirect_uri", encodeURI("http://localhost:8080"));

    const rawResponse = await fetch(
      "https://bsso.blpprofessional.com/as/token.oauth2",
      {
        method: "POST",
        mode: "cors",
        body,
      }
    );

    return this._handleTokenResponse(rawResponse);
  }

  async regenerateToken() {
    const body = new URLSearchParams();
    body.append("grant_type", "refresh_token");
    body.append("refresh_token", this.refreshToken);
    body.append("client_id", "se-mobile-app");

    // because we are getting new tokens, clear the currently
    // existing ones from memory
    this.accessToken = null;
    this.refreshToken = null;

    const response = await fetch(
      "https://bsso.blpprofessional.com/as/token.oauth2",
      {
        method: "POST",
        mode: "cors",
        body,
      }
    );

    return this._handleTokenResponse(response);
  }

  async _handleTokenResponse(fetchResponse) {
    const regenerated = await fetchResponse.json();
    if (regenerated.error) {
      throw Error(regenerated.error);
    }

    this.accessToken = regenerated.access_token;
    this.refreshToken = regenerated.refresh_token;
    this.expirationTimestamp =
      new Date().getTime() / 1000 + regenerated.expires_in;

    /* The below oauthResponse matches the following TypeScript-style interface
        interface OAuthToken {
          access_token: string;
          refresh_token: string;
          token_type: string;
          expires_in?: number;
        }
      */

    sessionStorage.setItem("sso-token", this.refreshToken);
    sessionStorage.setItem("sso-expire", this.expirationTimestamp);

    return this.accessToken;
  }

  isExpired() {
    const current = new Date().getTime() / 1000;
    return current > this.expirationTimestamp;
  }
}
