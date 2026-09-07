import {integer,sqliteTable,text} from 'drizzle-orm/sqlite-core';
export const workspace=sqliteTable('workspace',{id:text('id').primaryKey(),payload:text('payload').notNull(),revision:integer('revision').notNull().default(0)});

export const loginLimits=sqliteTable('login_limits',{id:text('id').primaryKey(),attempts:integer('attempts').notNull(),startedAt:integer('started_at').notNull()});
