# redis_db.py
from redis import Redis
import json

options = {
    'host': 'localhost',
    'port': 6389,
    'db': 0,
}

class RedisRepository:
    def __init__(self, redis_conn: Redis) -> None:
        self.__redis_con = redis_conn

    def insert(self, key: str, value: str) -> None:
        self.__redis_con.set(key, value)

    def get(self, key: str) -> str:
        value = self.__redis_con.get(key)
        return value.decode() if value else None

class RedisConnect:
    def __init__(self):
        self.__host = options.get('host', 'localhost')
        self.__port = options.get('port', 6379)
        self.__db = options.get('db', 0)
        self.__connection = None

    def connect(self) -> Redis:
        self.__connection = Redis(
            host=self.__host,
            port=self.__port,
            db=self.__db,
        )
        return self.__connection

    def get_connect(self) -> Redis:
        return self.__connection

# Funções utilitárias para cache de params.json
def cache_params_to_redis(redis_repo, params_path):
    with open(params_path, "r") as f:
        params_json = f.read()
    redis_repo.insert('params_json', params_json)

def get_params_from_redis(redis_repo):
    params_json = redis_repo.get('params_json')
    if params_json:
        return json.loads(params_json)
    return None

def load_params_with_redis(params_path):
    conn = RedisConnect().connect()
    repo = RedisRepository(conn)
    # Tenta buscar do Redis
    params = get_params_from_redis(repo)
    if params is None:
        # Se não existe, lê do arquivo e salva no Redis
        with open(params_path, "r") as f:
            params = json.load(f)
        repo.insert('params_json', json.dumps(params))
    return params

def main():
    import os
    base_dir = os.path.dirname(os.path.abspath(__file__))
    params_path = os.path.join(base_dir, "src", "params.json")
    # Salva no Redis se não existir
    params = load_params_with_redis(params_path)
    print("Parâmetros carregados do Redis ou arquivo:")
    print(params)
    # Exemplo de uso: acessar um parâmetro
    print("POP_SIZE =", params.get("POP_SIZE"))

if __name__ == "__main__":
    main()