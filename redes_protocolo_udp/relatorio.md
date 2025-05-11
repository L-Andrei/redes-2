Atividade 1:

![Testes dos scripts do servidor e cliente](img/servidor_cliente_chat.png)

Atividade 2:

![Transferencia do arquivo de 10 KB](img/transferencia1.png)
![Transferencia da imagem com 1.5 MB](img/transferencia2.png)
![Tranferencia do pdf com 10 MD](img/transferencia3.png)

Comparação TCP vs UDP:

Cenário 1:

Resumo da transferência UDP:
Arquivo: arquivo_5mb.txt
Tamanho: 5120.00 KB
Fragmentos: 5243 (0 falhas)
Retransmissões totais: 0 (0.0% dos fragmentos)
Tempo total: 1.79 segundos
Taxa média: 2.79 MB/s

Resumo da transferência TCP:
Tamanho enviado: 5120.00 KB
Tempo total: 0.03 segundos
Taxa de transferência: 154853.95 KB/s

OBS.: Os testes foram feitos no mesmo computador já que não possuo dois computadores em casa.

Cenário 2(5% de perda de pacote):

Resumo da transferência UDP:
Arquivo: arquivo_5mb.txt
Tamanho: 5120.00 KB
Fragmentos: 5243 (0 falhas)
Retransmissões totais: 0 (0.0% dos fragmentos)
Tempo total: 1.97 segundos
Taxa média: 2.54 MB/s

Resumo da tranferência TCP:
Tamanho enviado: 5120.00 KB
Tempo total: 0.10 segundos
Taxa de transferência: 52580.92 KB/s


