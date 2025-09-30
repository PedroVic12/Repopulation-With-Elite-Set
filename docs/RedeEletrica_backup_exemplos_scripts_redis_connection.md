# redis_connection.py

```python
from redis import Redis
import redis

options = {
    'host': 'localhost',   # ajuste para seu host
    'port': 6379,
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
    
    def insert_hash(self,key: str, field: str, value: str) -> None:
        self.__redis_con.hset(key, field, value)
    def get_hash(self,key:str, field:str)->None:
        value = self.__redis_con.hget(key, value).decode("utf-8") if value else None
        return value        

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
    
    def list_database(self) -> list:
        return self.__connection.keys()

                

def main():
    conn = RedisConnect().connect()
    repo = RedisRepository(conn)
    repo.insert('test_key', 'test_value')
    value = repo.get('test_key')

def get_hora_atual():
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
def use_hash_redis():
    redis_connection = RedisConnect().connect()
    redis_repository = RedisRepository(redis_connection)
    
    
    
    last_hour = get_hora_atual()
    redis_repository.insert_hash(last_hour, 'field1', 'value1')
    value = redis_repository.get(last_hour)
    print(f"Valor do campo 'field1' no hash '{last_hour}': {value}")
    
    
    # Listar todas as chaves no Redis
    keys = redis_connection.keys()
    print("Chaves no Redis:")
    for key in keys:
        print(key.decode('utf-8'))
        
        
    # Listar todos os hashes
    hashes = redis_connection.hgetall(last_hour)
    print(f"Campos no hash '{last_hour}':")
    for field, value in hashes.items():
        print(f"{field.decode('utf-8')}: {value.decode('utf-8')}")  
    
    
    
if __name__ == "__main__":
    #main()
    use_hash_redis()
```