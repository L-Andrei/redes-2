Lista de Problemas ou Limitações no servidor_chat.py:

1-Problema de segurança e duplicação de nomes:

O servidor acaba suportanto que duas conexões usem o mesmo nome causando problemas no comando whispers, além das menssagens não serem criptografadas.

2-Baixa escalabilidade:

Como o servidor ultiliza o modelo de threads pode acaba travando conforme o número de clientes cresce.

3-Falta de desconexão por inatividade:

Não identifica usuários com muito tempo de inatividade e que pode ocasionar em uma ocupação do servidor sem a utilização do mesmo.

4-Desconexões inesperadas não tratadas:

Caso o usuário não acabe usando o comando /quit o servidor acaba ficando confuso sobre o paradeiro do cliente.

Lista de Problemas ou Limitações no cliente_chat.py:

1-Não trata erros especificos:

O código utiliza try/exept genéricos, assim não tratando de maneira clara erros especificos como: ConnectionResetError, BrokenPipeError, KeyboardInterrupt, etc.

2-Falta de indetificação de falhas na comunicação:

O código não identifica falahs na comunicação ou possivel inatividade do cliente através de um comando como o settimeout(), por exemplo.

3-Problema de encerramento de threads:

O código do cliente não trata possiveis encerramento do programa por problemas exteriores.

4-Falta de tratamento para menssagens grandes:

Não trata menssagens maiores que o tamanha do buffer.
