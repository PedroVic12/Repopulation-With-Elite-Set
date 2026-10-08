"""
Neste algoritmo temos o seguinte:

    Este algoritmo foi direcionado para trabalhar com a base Adendo A.2_Conjunto de Dados_DataSet.csv
    Dividir a base de dados com base na coluna 'role': Vamos dividir o DataFrame original em dois: um DataFrame de
    treinamento que consiste apenas em dados 'normais' e um DataFrame de teste que consiste em dados 'test-0'.
    Vamos usar o DataFrame de treinamento para treinar nosso autoencoder e o DataFrame de teste para avaliar seu
    desempenho.

    Treinar o Autoencoder: Com base no DataFrame de treinamento, vamos treinar nosso autoencoder. O objetivo é permitir
    que o autoencoder aprenda a reconstruir as operações normais com a menor perda possível.
        A opção pelo uso do autoencoder --> se deve ao fato de ser um algoritmo propício para detecção de anomalias
        (há outros), mas vamos começar por aqui. Outro fato importante é que se trata de um algoritmo de aprendizagem
        profunda e que não demanda que os dados sigam uma distribuição normal.

    Testar o Autoencoder: Após o treinamento, vamos aplicar o autoencoder aos dados de teste para gerar previsões. Vamos
    calcular o erro de reconstrução para cada observação e marcar as observações com erro de reconstrução acima de um
    certo limiar como anomalias. (isto pode ser ajustado vamos iniciar com +/- 3 sigmas).

    Obs.: o que estamos fazendo neste algoritmo:

        Estamos usando o teste de Shapiro-Wilk pode ser usado para verificar a normalidade dos dados.
        Este método não atendeu, pois se restringe a arquivos com menos de 5000 registros.
        Vamos usar o  teste de normalidade de Anderson-Darling que é uma versão modificada do teste de
        Kolmogorov-Smirnov e tem mais poder para uma ampla gama de alternativas e maior quantidade de registros.

        Utilizar a estrutura de modelo Sequential do Keras, que é mais simples e intuitiva (há outras para serem
        testadas).
        Não remove os outliers dos dados de treinamento, o que pode melhorar a capacidade do modelo de detectar
        anomalias.
        Classifica =>> observação será considerado como uma anomalia se seu erro de reconstrução for maior do que três
        vezes o desvio padrão (+/-) 3 sigmas. Este é um método muito comum utilizado para detectar outliers.
        Contar o número de anomalias na base de treinamento e de teste.
        Imprimir uma descrição estatística para cada variável nas observações que foram classificadas como anomalias.
        Isso pode nos dar algumas indicações sobre quais variáveis contribuíram para as anomalias. Esta parte do
        código foi suprimida na entrega, pois para a entrega apenas sinalizamos na saída os pontos sem anomalia (0) e
        com anomalia (1) no arquivo de saída.

    Importante: Esse código assume que seu conjunto de treinamento não contém anomalias (como normalmente é o caso ao
    treinar um autoencoder para detecção de anomalias). Caso o conjunto de treinamento contenha anomalias
    e quer que o modelo seja capaz de detectá-las, é preciso ajustar a forma como o limiar é calculado.
"""

# Importando as bibliotecas necessárias
import pandas as pd
import numpy as np
from keras.models import Sequential
from keras.layers import Dense
from scipy.stats import anderson


# Classe para detecção de anomalias usando autoencoder
class AnomalyDetector:
    def __init__(self, file_path):
        # Inicialização dos atributos e carregamento dos dados
        self.file_path = file_path
        self.df, self.df_train, self.df_test = self.load_and_prepare_data()
        self.input_dim = self.df_train.shape[1]
        self.model = self.create_model(self.input_dim)

    def load_and_prepare_data(self):
        # Carregar e preparar os dados: limpeza, substituição e divisão entre treino e teste
        df = pd.read_csv(self.file_path)
        df = df.replace(99999.99, np.nan)

        for column in df.select_dtypes(include=[np.number]).columns:
            df[column].fillna(df[column].mean(), inplace=True)

        df_train = df[df['role'] == 'normal'].select_dtypes(include=[np.number])
        df_test = df[df['role'] == 'test-0'].select_dtypes(include=[np.number])

        return df, df_train, df_test

    def check_normality(self):
        # Verifica a normalidade das colunas dos dados
        for column in self.df.select_dtypes(include=[np.number]).columns:
            result = anderson(self.df[column])
            stat = result.statistic
            critical_values = result.critical_values
            if stat > critical_values[-1]:
                print(f'Coluna {column} não segue uma distribuição normal')
            else:
                print(f'Coluna {column} segue uma distribuição normal')

    def create_model(self, input_dim, encoding_dim=14):
        # Criação do modelo autoencoder para detecção de anomalias
        model = Sequential()
        model.add(Dense(encoding_dim, activation="relu", input_shape=(input_dim,)))
        model.add(Dense(input_dim, activation='sigmoid'))
        model.compile(optimizer='adam', loss='mean_squared_error')
        return model

    def train_and_predict(self):
        # Treinamento do modelo e predição para conjuntos de treino e teste
        self.model.fit(self.df_train, self.df_train, epochs=50, batch_size=32, shuffle=True, validation_split=0.2)
        df_train_pred = self.model.predict(self.df_train)
        df_test_pred = self.model.predict(self.df_test)
        return df_train_pred, df_test_pred

    def calculate_reconstruction_error(self, df_train_pred, df_test_pred):
        # Calcula o erro de reconstrução e determina anomalias com base em um limite
        reconstruction_error_train = np.mean(np.power(self.df_train - df_train_pred, 2), axis=1)
        reconstruction_error_test = np.mean(np.power(self.df_test - df_test_pred, 2), axis=1)
        threshold = np.mean(reconstruction_error_train) + 3 * np.std(reconstruction_error_train)
        self.df_train['anomaly'] = (reconstruction_error_train > threshold).astype(int)
        self.df_test['anomaly'] = (reconstruction_error_test > threshold).astype(int)
        print(f"Número de anomalias na base de treinamento: {self.df_train['anomaly'].sum()}")
        print(f"Número de anomalias na base de teste: {self.df_test['anomaly'].sum()}")

    def report_anomalies(self):
        # Gera um relatório de anomalias com base em desvios padrão do conjunto de treinamento
        report = pd.DataFrame(columns=['offset_seconds', 'Registro'] + list(self.df_test.columns[:-1]) + ['TOTAL_Anom'])
        anom_stats = pd.DataFrame(columns=['Registro', 'Variable', 'Mean', 'Found Value', 'Deviation'])

        for index, row in self.df_test.iterrows():
            anomaly_row = [index, index]
            total_anom = 0
            for column in self.df_test.columns[:-1]:  # Excluindo coluna 'anomaly'
                if row[column] > self.df_train[column].mean() + 3 * self.df_train[column].std():
                    anomaly_row.append(1)
                    total_anom += 1
                    found_value = row[column]
                    mean_value = self.df_train[column].mean()
                    deviation = (found_value - mean_value) / self.df_train[column].std()
                    anom_stats.loc[len(anom_stats)] = [index, column, mean_value, found_value, deviation]
                else:
                    anomaly_row.append(0)
            anomaly_row.append(total_anom)
            report_temp = pd.DataFrame([anomaly_row], columns=report.columns)
            report = pd.concat([report, report_temp], ignore_index=True)

        anom_stats.to_excel('DADOS_SIMUL/EST_ANOM.xlsx', index=False)
        return report

    def run(self):
        # Método principal para executar todas as etapas: verificação de normalidade, treinamento, predição e
        # geração de relatório
        self.check_normality()
        df_train_pred, df_test_pred = self.train_and_predict()
        self.calculate_reconstruction_error(df_train_pred, df_test_pred)
        report = self.report_anomalies()
        report.to_excel('DADOS_SIMUL/FINAL_A2.xlsx', index=False, sheet_name='RELATÓRIO')


# Inicializa e executa o detector de anomalias
if __name__ == "__main__":
    # Instanciando o objeto
    detector = AnomalyDetector('/home/pedrov12/Documentos/GitHub/Electrical-System-Simulator/backend/novo_PETROBRAS_simulator/backend/DADOS/Adendo A.2_Conjunto de Dados_DataSet.csv')
    detector.run()
