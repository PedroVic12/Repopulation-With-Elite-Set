import sqlite3
import pandas as pd


class DatabaseManager:
    def __init__(self, db_name="data_exploration.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS Statistics (
            generation INTEGER,
            min_fitness REAL,
            avg_fitness REAL,
            max_fitness REAL,
            std_fitness REAL
        )
        """
        )
        self.conn.commit()

    def insert_statistics(
        self, generation, best_index, best_solution, best_variables, std_fitness
    ):
        self.cursor.execute(
            """
        INSERT INTO Statistics (generation, min_fitness, avg_fitness, max_fitness, std_fitness)
        VALUES (?, ?, ?, ?, ?)
        """,
            (generation, best_index, best_solution, best_variables, std_fitness),
        )
        self.conn.commit()

        print("Dados atualizados")

    def query(self):
        self.cursor.execute("SELECT * FROM Statistics")
        rows = self.cursor.fetchall()
        return pd.DataFrame(
            rows,
            columns=[
                "generation",
                "min_fitness",
                "avg_fitness",
                "max_fitness",
                "std_fitness",
            ],
        )

    def close(self):
        self.conn.close()


def main():
    # Create a new database
    db = DatabaseManager("database.db")
    db.create_tables()
    # Insert some data
    db.insert_statistics(1, 0.5, 0.6, 0.2, 9)

    db.insert_statistics(2, 0.4, 0.5, 0.2, 12)

    df = db.query()
    print(df)


main()
