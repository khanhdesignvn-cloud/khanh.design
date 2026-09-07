CREATE TABLE `admin_sessions` (
  `id` text PRIMARY KEY NOT NULL,
  `expires_at` integer NOT NULL
);
--> statement-breakpoint
CREATE INDEX `admin_sessions_expires_at_idx` ON `admin_sessions` (`expires_at`);
