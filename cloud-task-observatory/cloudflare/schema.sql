-- 云端监控数据库：只存任务事件与经裁剪的公开安全元数据
CREATE TABLE IF NOT EXISTS events (
  event_id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  task_id TEXT NOT NULL,
  run_id TEXT NOT NULL,
  source_id TEXT NOT NULL,
  seq INTEGER NOT NULL,
  status TEXT NOT NULL,
  occurred_at TEXT NOT NULL,
  received_at TEXT NOT NULL,
  title TEXT,
  owner TEXT,
  dependencies_json TEXT NOT NULL DEFAULT '[]',
  message TEXT,
  resume_point TEXT,
  evidence_json TEXT NOT NULL DEFAULT '[]',
  UNIQUE(project_id, source_id, run_id, seq)
);
CREATE INDEX IF NOT EXISTS idx_project_events ON events(project_id, received_at DESC);
CREATE INDEX IF NOT EXISTS idx_project_task ON events(project_id, task_id, received_at DESC);
CREATE TABLE IF NOT EXISTS sources (
  source_id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  last_seen_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_source_project ON sources(project_id);