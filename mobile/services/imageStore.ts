/**
 * In-memory image store to pass selected/captured image URIs between
 * screens without pushing megabytes of base64 data into URL query parameters.
 */

let currentImageUri: string | null = null;

export function setCapturedImageUri(uri: string): void {
  currentImageUri = uri;
}

export function getCapturedImageUri(): string | null {
  return currentImageUri;
}

export function clearCapturedImageUri(): void {
  currentImageUri = null;
}
