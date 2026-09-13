/**
 * Image store to pass selected/captured image URIs between screens.
 * Uses in-memory variable + sessionStorage on Web so image URIs persist
 * across screen transitions and component remounts.
 */

let currentImageUri: string | null = null;

export function setCapturedImageUri(uri: string): void {
  currentImageUri = uri;
  if (typeof window !== "undefined" && window.sessionStorage) {
    try {
      window.sessionStorage.setItem("capturedImageUri", uri);
    } catch (e) {
      console.warn("[imageStore] could not save to sessionStorage:", e);
    }
  }
}

export function getCapturedImageUri(): string | null {
  if (currentImageUri) return currentImageUri;
  if (typeof window !== "undefined" && window.sessionStorage) {
    try {
      const stored = window.sessionStorage.getItem("capturedImageUri");
      if (stored) {
        currentImageUri = stored;
        return stored;
      }
    } catch (e) {}
  }
  return null;
}

export function clearCapturedImageUri(): void {
  currentImageUri = null;
  if (typeof window !== "undefined" && window.sessionStorage) {
    try {
      window.sessionStorage.removeItem("capturedImageUri");
    } catch (e) {}
  }
}
