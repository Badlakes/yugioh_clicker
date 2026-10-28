# Duel Links Bot — protótipo Python visual

Protótipo inicial de interface e reconhecimento visual. Ainda **não vem com imagens reais do jogo** nem com os fluxos do Portão/evento validados; é necessário configurar os recortes da sua própria tela antes de habilitar cliques reais.

## Instalar

Windows + Python 3.10 ou superior:

```powershell
py -m pip install pyautogui opencv-python pillow
```

Execute:

```powershell
py main.py
```

## Como criar a lista de imagens

1. Abra o Duel Links em janela, com resolução/escala fixas.
2. Quando um botão estiver visível, use `Win + Shift + S` para recortar **somente o botão** (inclua a borda/ícone característico, mas evite animações e fundos variáveis).
3. Salve os recortes em `imagens/portao/`, `imagens/personagens/` ou `imagens/evento/`.
4. Abra `workflows.json` e substitua os nomes de exemplo pelos nomes dos arquivos reais.
5. Cada etapa tem:
   - `label`: nome exibido no log;
   - `image`: caminho relativo ao diretório do projeto;
   - `timeout_seconds`: quanto tempo procurar pela imagem;
   - `wait_after_seconds`: quanto esperar depois de encontrar/clicar.
6. Primeiro rode com **“Ativar cliques reais” desmarcado**. Confira os logs e veja se as imagens são encontradas corretamente.
7. Só depois, teste com cliques reais e supervisão.

## Como os loops funcionam

Cada fluxo é uma lista ordenada de etapas. O bot espera cada imagem, e então passa à próxima. Quando completa a lista, recomeça o fluxo selecionado, respeitando o limite de tempo. Se uma imagem não aparecer dentro do timeout, o fluxo para aquela passagem em vez de clicar às cegas.

Isso é apenas um esqueleto: telas de duelo, vitória/derrota, recompensas, seleção de personagem e telas inesperadas precisam ser modeladas como estados/etapas reais antes de usar por longos períodos. Não coloque botões de telas diferentes em sequência sem confirmar a transição esperada.

## Segurança e parada

- O modo de simulação é o padrão.
- Para interromper: clique em **Parar**.
- Também pode mover o mouse para o canto superior esquerdo da tela para acionar o FAILSAFE do PyAutoGUI.
- Não execute como administrador.
- Automação pode contrariar as regras do jogo e acarretar penalidades na conta.


## Imagens de referência recebidas

Foram recortadas de `image.png` as referências `portao_azul.png`, `portao_vermelho.png`, `voltar.png`, `fechar.png`, `ok.png`, `rush_duel.png` e `draw.png`, dentro de `imagens/`.

O fluxo do Portão agora procura **o portão azul OU o vermelho**. Isso demonstra detecção de alternativas, mas não significa que esse recorte já corresponda perfeitamente à tela ao vivo. O recorte de referência precisa aparecer em tamanho e aparência semelhantes na tela real. Faça primeiro o teste em modo simulação.

Para adicionar alternativas a uma etapa em `workflows.json`, use:
```json
{
  "label": "Botão azul ou vermelho",
  "images": ["imagens/portao_azul.png", "imagens/portao_vermelho.png"],
  "timeout_seconds": 15,
  "wait_after_seconds": 2
}
```


## Atualização: tela do Portão enviada pelo usuário

Foi adicionado `imagens/rush_duel_tela_portao.png`, recortado do botão Rush Duel da captura enviada. O fluxo `portao` agora procura esse botão nessa tela. Isso evita repetir o reconhecimento do desenho do portal, que pode aparecer como arte de fundo e gerar falsos positivos.

A etapa só confirma e clica (quando o modo de cliques reais está ativado) no botão Rush Duel. Ainda não automatiza o duelo nem as telas de recompensa. Teste primeiro em modo de simulação e confira se o ponto encontrado cai exatamente sobre o botão.


## Atualização: tela após a fala do personagem

Adicionado `imagens/auto_duel_tela_personagem.png`, recortado do botão Auto-Duel na captura enviada. O fluxo do Portão agora tem duas etapas: localizar Rush Duel na tela anterior e depois esperar até 60 segundos pelo botão Auto-Duel após a fala/transição.

Importante: no modo simulação o bot não clica e, portanto, não provoca a transição de tela. Para validar apenas o reconhecimento do Auto-Duel, inicie o teste estando já na tela que mostra esse botão, mas a primeira etapa (Rush Duel) não será encontrada. A sequência completa deve ser testada a partir da tela anterior com cliques reais, sob supervisão. O bot ainda não está pronto para automatizar o duelo ou as recompensas.

O protótipo agora para o teste quando uma etapa não é reconhecida, em vez de repetir continuamente o mesmo fluxo incompleto.
