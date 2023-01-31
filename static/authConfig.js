const msalConfig = {
    auth: {
      clientId: "3b4200fb-c516-44f5-9d53-1fc6cc260ea7",
      authority: "https://login.microsoftonline.com/edf3958e-2be0-4191-a131-169e91c095a2",
      redirectUri: "https://localhost:1337/get_auth_token",
    },
    cache: {
      cacheLocation: "sessionStorage", // This configures where your cache will be stored
      storeAuthStateInCookie: false, // Set this to "true" if you're having issues on Internet Explorer 11 or Edge
    }
  };

  // Add scopes for the ID token to be used at Microsoft identity platform endpoints.
  const loginRequest = {
    scopes: ["openid", "profile", "User.Read"]
  };

  // Add scopes for the access token to be used at Microsoft Graph API endpoints.
  const tokenRequest = {
    scopes: ["User.ReadBasic.All"]
  };