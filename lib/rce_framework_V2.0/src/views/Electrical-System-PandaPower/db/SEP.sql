CREATE TABLE buses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    vnom REAL,          -- tensão nominal (kV)
    type TEXT           -- 'PQ', 'PV', 'ref'
);

CREATE TABLE lines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    from_bus INTEGER REFERENCES buses(id) ON DELETE CASCADE,
    to_bus INTEGER REFERENCES buses(id) ON DELETE CASCADE,
    r REAL,             -- resistência (pu)
    x REAL,             -- reatância (pu)
    b REAL              -- susceptância shunt (pu)
);

CREATE TABLE transformers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    from_bus INTEGER REFERENCES buses(id) ON DELETE CASCADE,
    to_bus INTEGER REFERENCES buses(id) ON DELETE CASCADE,
    r REAL,
    x REAL,
    tap_ratio REAL      -- relação de transformação (pu)
);
