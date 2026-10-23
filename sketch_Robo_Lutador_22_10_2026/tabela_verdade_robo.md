|   E3_Stop |   E2_Start |   E1_Inimigo |   E0_Borda |   S_Frente |   S_Re |   S_Parar | Estado_Robo                    |
|----------:|-----------:|-------------:|-----------:|-----------:|-------:|----------:|:-------------------------------|
|         0 |          0 |            0 |          0 |          0 |      0 |         1 | ESTADO_PARADO                  |
|         0 |          0 |            0 |          1 |          0 |      1 |         0 | ESTADO_ESQUIVAR_BORDA          |
|         0 |          0 |            1 |          0 |          0 |      0 |         1 | ESTADO_PARADO                  |
|         0 |          0 |            1 |          1 |          0 |      1 |         0 | ESTADO_ESQUIVAR_BORDA          |
|         0 |          1 |            0 |          0 |          0 |      1 |         0 | ESTADO_BUSCAR                  |
|         0 |          1 |            0 |          1 |          0 |      1 |         0 | ESTADO_ESQUIVAR_BORDA          |
|         0 |          1 |            1 |          0 |          1 |      0 |         0 | ESTADO_ATACAR                  |
|         0 |          1 |            1 |          1 |          0 |      1 |         0 | ESTADO_ESQUIVAR_BORDA          |
|         1 |          0 |            0 |          0 |          0 |      0 |         1 | ESTADO_PARADO_DEFINITIVO (FIM) |
|         1 |          0 |            0 |          1 |          0 |      0 |         1 | ESTADO_PARADO_DEFINITIVO (FIM) |
|         1 |          0 |            1 |          0 |          0 |      0 |         1 | ESTADO_PARADO_DEFINITIVO (FIM) |
|         1 |          0 |            1 |          1 |          0 |      0 |         1 | ESTADO_PARADO_DEFINITIVO (FIM) |
|         1 |          1 |            0 |          0 |          0 |      0 |         1 | ESTADO_PARADO_DEFINITIVO (FIM) |
|         1 |          1 |            0 |          1 |          0 |      0 |         1 | ESTADO_PARADO_DEFINITIVO (FIM) |
|         1 |          1 |            1 |          0 |          0 |      0 |         1 | ESTADO_PARADO_DEFINITIVO (FIM) |
|         1 |          1 |            1 |          1 |          0 |      0 |         1 | ESTADO_PARADO_DEFINITIVO (FIM) |