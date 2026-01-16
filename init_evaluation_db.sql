CREATE TABLE IF NOT EXISTS evaluation_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    overall_score REAL NOT NULL,
    passed BOOLEAN NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Sample data for testing
INSERT INTO evaluation_results (agent_id, task_id, overall_score, passed) VALUES
('5rd585cb-b9a7-4bcd-b7a7-7368ffe06a13', 'task_1', 1.0, 1),
('5rd585cb-b9a7-4bcd-b7a7-7368ffe06a13', 'task_2', 1.0, 1),
('5rd585cb-b9a7-4bcd-b7a7-7368ffe06a13', 'task_3', 0.5, 0);
