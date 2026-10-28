# EASUN RWB1 Local Bridge (add-on local do Home Assistant)

Lê o inversor EASUN (dongle **RWB1** / cloud **Siseli**) **100 % localmente**, sem
cloud e sem internet, e publica os dados como sensores no Home Assistant.

O add-on substitui os serviços da cloud de que o dongle depende no arranque:

- **DNS (:8553)** — responde aos domínios `*.siseli.com` com o IP do Pi
  (porta alta para não ocupar o `53`; o router reescreve o `53` do dongle p/ `8553`).
- **HTTP (:80)** — serve o bootstrap (`/dtu/checkin`, `/dtu/devices/findSingle`,
  `/dtu/servers/mqtt`), apontando o broker ao Pi e fornecendo a hora.
- **MQTT** — liga-se ao Mosquitto como cliente, confirma (ack) as mensagens do
  dongle, descodifica as tramas **Modbus** (little-endian) e cria os sensores
  via **MQTT discovery**.

## Instalação rápida

1. Copia esta pasta para `/addons/easun_rwb1/` no Home Assistant.
2. Add-on Store → *Check for updates* → instala **EASUN RWB1 Local Bridge**.
3. Configura `mqtt_user`/`mqtt_password` (e vê o resto em **Documentation**).
4. Configura o Mosquitto para aceitar o dongle e o router para desviar o DNS
   do dongle para o Pi (passos detalhados na página **Documentation**/`DOCS.md`).

As instruções completas, opções e resolução de problemas estão em **`DOCS.md`**
(separador *Documentation* do add-on).

## Estrutura

```
easun_rwb1/
  config.yaml     # manifesto do add-on (portas, opções configuráveis)
  build.yaml      # imagens base por arquitetura
  Dockerfile      # Python 3 + paho-mqtt
  app/service.py  # DNS + HTTP + cliente MQTT (acks, descodificação, discovery)
  DOCS.md         # página de instruções
  README.md
```

> Versão 0.1.0 — baseada em captura e validação do protocolo real do RWB1.
> Confirma o primeiro arranque pelo Log do add-on.

## Licença

[MIT](LICENSE) © 2026 João Santos.

Projeto independente, sem qualquer afiliação com a EASUN ou a Siseli. O protocolo
foi obtido por engenharia reversa do próprio dongle para fins de interoperabilidade
e uso local. Usa por tua conta e risco.
