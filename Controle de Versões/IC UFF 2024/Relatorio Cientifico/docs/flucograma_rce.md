```mermaid
graph TD
A[inicio] --> B[Entrar valores]
B --> C{Valor elevado?}
C --> |SIM| D[nao comprar]
C --> |NAO| E[comprar]
D --> F[fim]
E -->F[fim]
```
