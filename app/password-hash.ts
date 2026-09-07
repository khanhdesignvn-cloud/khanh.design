export type PasswordHashConfig = {
  rounds: number;
  salt: Uint8Array;
  expectedHex: string;
};

const MIN_ROUNDS = 100_000;
const MAX_ROUNDS = 1_000_000;

function decodeHex(value: string): Uint8Array | null {
  if (!/^[a-f0-9]+$/i.test(value) || value.length % 2 !== 0) return null;
  return new Uint8Array(value.match(/../g)!.map((pair) => Number.parseInt(pair, 16)));
}

export function parsePasswordHash(stored: string | undefined): PasswordHashConfig | null {
  if (!stored) return null;
  const parts = stored.split(":");
  if (parts.length !== 3 || !/^\d+$/.test(parts[0])) return null;
  const rounds = Number(parts[0]);
  const salt = decodeHex(parts[1]);
  const expected = decodeHex(parts[2]);
  if (!Number.isSafeInteger(rounds) || rounds < MIN_ROUNDS || rounds > MAX_ROUNDS) return null;
  if (!salt || salt.byteLength < 16 || salt.byteLength > 64) return null;
  if (!expected || expected.byteLength !== 32) return null;
  return { rounds, salt, expectedHex: parts[2].toLowerCase() };
}
