from datetime import timedelta, datetime
import os
import redis
import json
from typing import Optional, Dict, Any
import logging


from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Benefícios de usar o Redis para gerenciamento de sessão:

# - Escalabilidade: O Redis é um armazenamento de dados em memória, tornando-o muito rápido para operações de leitura e escrita, o que é crucial para lidar com um grande número de usuários simultâneos.
# - Stateless da API: Ao armazenar o estado da sessão no Redis, seus servidores de API podem permanecer stateless, facilitando a escalabilidade horizontal (adicionar mais servidores).
# - Gerenciamento Centralizado de Sessão: O Redis fornece um local central para gerenciar as sessões dos usuários, permitindo ações como fazer logout de um usuário de todos os dispositivos ou implementar timeouts de sessão.
# - Aumento da Segurança: Comparar o token recebido com o armazenado no Redis adiciona uma camada extra de validação contra roubo ou manipulação de tokens.

#TODO -> Configure o Redis para expirar a sessão automaticamente após o tempo de expiração do JWT.

# TODO -> Criptografia de Dados Sensíveis: Criptografe os dados armazenados no Redis, como o token JWT.


ACCESS_TOKEN_EXPIRE_HOURS = 8
ACCESS_TOKEN_EXPIRE_MINUTES_INT = 60
DEFAULT_SESSION_EXPIRY_SECONDS = ACCESS_TOKEN_EXPIRE_HOURS * ACCESS_TOKEN_EXPIRE_MINUTES_INT * 60


class RedisController:
    def __init__(
        self,
        host: str = os.getenv("REDIS_HOST", "localhost"),
        port: int = int(os.getenv("REDIS_PORT", 6379)),
        db: int = int(os.getenv("REDIS_DB", 0)),
    ):
        try:
            self.redis_client = redis.StrictRedis(
                host=host,
                port=port,
                db=db,
                decode_responses=True, # Importante
                socket_timeout=5,
                retry_on_timeout=True
            )
            self.session_expiry = DEFAULT_SESSION_EXPIRY_SECONDS 
            self.redis_client.ping()
            logger.info(f"Conectado ao Redis em {host}:{port}, DB: {db} com tempo de expirção em {self.session_expiry} segs")
        except redis.exceptions.ConnectionError as e:
            logger.error(f"Falha ao conectar ao Redis: {e}")
            raise ConnectionError(f"Não foi possível conectar ao Redis: {e}")


    #! Store token JWT
    def store_session_token(self, session_id: str, token: str, expiry_seconds: int) -> bool:
        """Armazena o SessionToken completo com expiração (SETEX)."""
        key = f"session_token_data:{session_id}"
        try:
            self.redis_client.setex(key, expiry_seconds, token)
            logger.debug(f"Token da sessão {session_id} armazenado no Redis com expiração de {expiry_seconds}s.")
            return True
        except Exception as e:
            logger.error(f"Erro ao armazenar token da sessão '{key}' no Redis: {e}")
            return False

    def get_stored_session_token(self, session_id: str) -> Optional[str]:
        """Recupera o SessionToken armazenado para um session_id."""
        key = f"session_token_data:{session_id}"
        try:
            return self.redis_client.get(key)
        except Exception as e:
            logger.error(f"Erro ao obter token da sessão '{key}' do Redis: {e}")
            return None
        
    def delete_session_token_data(self, session_id: str) -> int:
        """Deleta os dados (token) de uma sessão específica."""
        key = f"session_token_data:{session_id}"
        try:
            return self.redis_client.delete(key)
        except Exception as e:
            logger.error(f"Erro ao deletar token da sessão '{key}' do Redis: {e}")
            return 0



    #! Metodo para gerenciar sessões de usuários
    def set_session(self, user_id: str, token: str) -> bool:
        """Cria a sessão e retorna True se for bem sucedida, False caso contrário."""
        try:
            self.redis_client.setex(
                f"session:{user_id}",
                self.session_expiry,  # Já em segundos
                token  # Já é string, sem necessidade de JSON
            )
            print(f"Sessão do usuário: {user_id} armazenada!")
            return True
        except Exception as e:
            logger.error(f"Erro ao criar sessão para o usuário '{user_id}' no Redis: {e}")
            return False

    def get_session(self, user_id: str) -> Optional[str]:
        """Recupera o token da sessão armazenada no Redis (string pura)."""
        print("[DEBUG] Recuperando a session: ", user_id)
        return self.redis_client.get(f"session:{user_id}")  # Remove json.loads

    def get_session_data(self, user_id: str):
        """Retorna todos os dados da sessão"""
        return {
            "tokens_validos": self.redis_client.keys(f"session:{user_id}:*"),
            "ultimo_login": self.redis_client.get(f"user:{user_id}:last_login")
        }

    def delete_session(self, user_id: str):
        """Remove a sessão do usuário do Redis."""
        self.redis_client.delete(f"session:{user_id}")

    def session_exists(self, user_id: str) -> bool:
        """Verifica se a sessão do usuário existe no Redis."""
        return self.redis_client.exists(f"session:{user_id}") > 0


    #! Funções CRUD
    def set_value(self, key: str, value: Any, expires: int = DEFAULT_SESSION_EXPIRY_SECONDS):
        try:
            value_json = json.dumps(value)
            self.redis_client.setex(key, expires, value_json)
            return True
        except Exception as e:
            print(f"Erro ao definir valor no Redis: {e}")
            return False

    def get_value(self, key: str) -> Optional[Dict[str, Any]]:
        try:
            value_json = self.redis_client.get(key)
            return json.loads(value_json) if value_json else None
        except Exception as e:
            print(f"Erro ao recuperar valor do Redis: {e}")
            return None

    def delete_value(self, key: str):
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            print(f"Erro ao deletar valor do Redis: {e}")
            return False


    #! Funções dessign Patters Ollama
    def insert(self,key:str, value:any):
        self.redis_client.set(key, value)

    def get(self, key):
        """
        Obtém o valor de uma chave no Redis. Suporta diferentes tipos de dados.
        """
        try:
            key_type = self.redis_client.type(key)
            if key_type == "string":
                #return self.redis_client.get(key).decode("utf-8")
                return self.redis_client.get(key)
            elif key_type == "hash":
                return self.redis_client.hgetall(key)
            else:
                raise ValueError(f"Tipo de chave não suportado: {key_type}")
        except Exception as e:
            print(f"Erro ao obter a chave '{key}': {str(e)}")
            return None


    def insert_hash(self, key: str, field:str, value: any):
        self.redis_client.hset(key, field, value)


    def get_hash(self, key: str, field: str):
        value = self.redis_client.hget(key, field)
        if value:
            return value.decode(encoding="utf-8")


    def insert_hash_expired(self, key: str, field: str, value: any, ex: int):
        self.redis_client.hset(key, field, value)
        self.redis_client.expire(key, ex)


    def insert_expired(self, key: str, value: any, ex: int):
        self.redis_client.set(key, value, ex=ex)



    def run_redis_crud(self):
        key = "teste_usuario"
        data = {
            "user1": {
                "email": "admin@admin",
                "senha": "admin",
                "token": "123456"
            },

            "user2": {
                "email": "user@user",
                "senha": "user",
                "token": "654321"
            }
        }

        print("Inserindo dados no Redis...")
        self.set_value(key, data, 10)  # Expira em 10 segundos

        print("Recuperando dados...")
        value = self.get_value(key)
        print("Valor encontrado:", value)

        print("Deletando dados...")
        self.delete_value(key)

        print("Tentando recuperar após exclusão...")
        value = self.get_value(key)
        print("Valor encontrado após exclusão:", value)




def inserindo_hash_com_key_data_atual():
    redis_controller = RedisController()

    data_atual = datetime.now()
    data_formatada = data_atual.strftime("%Y-%m-%d")
    print(data_formatada)

    redis_controller.insert_hash_expired(data_formatada,"Login", "Senha", 40)
    redis_controller.insert_hash(data_formatada,"pedrovictor.rveras12@gmail.com_27ANOS_2025", "pedro")
    redis_controller.insert_hash(data_formatada,"admin@admin", "admin")

    #Vendos os resultado
    valores = redis_controller.get(data_formatada)
    print("Valores encontrados ",valores)


#inserindo_hash_com_key_data_atual()

# Testando o CRUD
def main_redis():
    redis_controller = RedisController()
    redis_controller.run_redis_crud()

main_redis()


#singleton controller
#redis_controller = RedisController()