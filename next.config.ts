import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Vinext inspects multipart POSTs before API route dispatch. Allow the
  // upload route's 50 MiB file plus multipart overhead through this guard.
  // The route still enforces auth, MIME validation and its own byte limit.
  experimental: { serverActions: { bodySizeLimit: '51mb' } },
};

export default nextConfig;
