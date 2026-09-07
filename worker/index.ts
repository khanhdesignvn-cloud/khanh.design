/** Cloudflare Worker entry point for the khanh.design project manager. */
import handler from "vinext/server/app-router-entry";
import { withSecurityHeaders } from "../app/security-headers";

interface Env {
  ASSETS: Fetcher;
  DB: D1Database;
  BUCKET: R2Bucket;
}

interface ExecutionContext {
  waitUntil(promise: Promise<unknown>): void;
  passThroughOnException(): void;
}

const worker = {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    return withSecurityHeaders(await handler.fetch(request, env, ctx));
  },
};

export default worker;
