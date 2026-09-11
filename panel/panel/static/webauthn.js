async function parseOptions(url) {
  const res = await fetch(url, { credentials: "same-origin" });
  if (!res.ok) throw new Error("options failed");
  return res.json();
}

function b64urlToBuffer(value) {
  const pad = "=".repeat((4 - (value.length % 4)) % 4);
  const b64 = (value + pad).replace(/-/g, "+").replace(/_/g, "/");
  const raw = atob(b64);
  const out = new Uint8Array(raw.length);
  for (let i = 0; i < raw.length; i += 1) out[i] = raw.charCodeAt(i);
  return out.buffer;
}

function bufferToB64url(buffer) {
  const bytes = new Uint8Array(buffer);
  let str = "";
  for (let i = 0; i < bytes.length; i += 1) str += String.fromCharCode(bytes[i]);
  return btoa(str).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function reviveCreate(options) {
  options.challenge = b64urlToBuffer(options.challenge);
  options.user.id = b64urlToBuffer(options.user.id);
  return options;
}

function reviveRequest(options) {
  options.challenge = b64urlToBuffer(options.challenge);
  if (options.allowCredentials) {
    options.allowCredentials = options.allowCredentials.map((c) => ({
      ...c,
      id: b64urlToBuffer(c.id),
    }));
  }
  return options;
}

function serializeCredential(cred) {
  return {
    id: cred.id,
    rawId: bufferToB64url(cred.rawId),
    type: cred.type,
    response: {
      clientDataJSON: bufferToB64url(cred.response.clientDataJSON),
      attestationObject: cred.response.attestationObject
        ? bufferToB64url(cred.response.attestationObject)
        : undefined,
      authenticatorData: cred.response.authenticatorData
        ? bufferToB64url(cred.response.authenticatorData)
        : undefined,
      signature: cred.response.signature
        ? bufferToB64url(cred.response.signature)
        : undefined,
      userHandle: cred.response.userHandle
        ? bufferToB64url(cred.response.userHandle)
        : undefined,
    },
  };
}

document.getElementById("passkey-login")?.addEventListener("click", async () => {
  try {
    const options = reviveRequest(await parseOptions("/api/webauthn/login/options"));
    const cred = await navigator.credentials.get({ publicKey: options });
    const res = await fetch("/api/webauthn/login/verify", {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(serializeCredential(cred)),
    });
    if (!res.ok) throw new Error("verify failed");
    window.location.href = "/";
  } catch (err) {
    alert("Passkey login failed: " + err);
  }
});

document.getElementById("passkey-register")?.addEventListener("click", async () => {
  try {
    const options = reviveCreate(await parseOptions("/api/webauthn/register/options"));
    const cred = await navigator.credentials.create({ publicKey: options });
    const res = await fetch("/api/webauthn/register/verify", {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(serializeCredential(cred)),
    });
    if (!res.ok) throw new Error("register failed");
    alert("Passkey сохранён");
  } catch (err) {
    alert("Passkey register failed: " + err);
  }
});
