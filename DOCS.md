# EASUN RWB1 Local Bridge

Faz o teu inversor EASUN (dongle **RWB1** / cloud **Siseli**) funcionar **100 % local** no Home Assistant — sem cloud e sem internet. O add-on imita os serviços da cloud (DNS + bootstrap HTTP + broker) e publica os dados do inversor como sensores.

## Como funciona

O dongle, ao arrancar, precisa de 3 coisas da "cloud": resolver um domínio por **DNS**, fazer um **bootstrap HTTP** (hora + onde está o broker) e depois ligar-se por **MQTT**. Este add-on fornece as três, apontando o dongle ao teu Pi:

```
          ┌─ DNS  :8553 → responde "siseli" com o IP do Pi
dongle ───┤  HTTP :80   → bootstrap (hora, nº série, broker = Pi)
          └─ MQTT :1883  → Mosquitto; o add-on confirma as mensagens,
                           descodifica o Modbus e cria os sensores no HA
```

Os dados nunca saem da tua rede.

---

## Pré-requisitos

1. **Add-on Mosquitto broker** instalado e a correr.
2. O **dongle e o Pi na mesma sub-rede** (ex.: `192.168.10.x`).
3. Uma forma de **encaminhar o DNS do dongle para o Pi** no router (ver secção "Router").

---

## Instalação (add-on local)

1. Copia a pasta `easun_rwb1/` para `\addons\` do teu Home Assistant
   (via o add-on *Samba share* ou *Terminal & SSH*; o caminho no disco é
   `/addons/easun_rwb1/`).
2. **Definições → Add-ons → Add-on Store → ⋮ → Check for updates.**
   O add-on **EASUN RWB1 Local Bridge** aparece em *Local add-ons*.
3. Abre-o e clica **Install** (a primeira compilação demora alguns minutos).

---

## Configuração

Todas as opções se definem no separador **Configuration** do add-on.

| Opção | O que é | Valor típico |
|---|---|---|
| `pi_ip` | IP do Pi na tua LAN. Deixa **vazio** para deteção automática. | `192.168.10.251` |
| `mqtt_host` | Onde está o Mosquitto. | `127.0.0.1` |
| `mqtt_port` | Porta do Mosquitto. | `1883` |
| `mqtt_user` | **Utilizador** com que o add-on se liga ao Mosquitto. | ver abaixo |
| `mqtt_password` | **Password** desse utilizador. | ver abaixo |
| `override_substr` | Domínios a redirecionar para o Pi (por substring). | `siseli` |
| `dns_port` | Porta onde o add-on ouve DNS no Pi (porta alta, para não ocupar o `53`). | `8553` |
| `dns_upstream` | DNS para onde reencaminhar as outras perguntas. | `1.1.1.1` |
| `refresh_interval` | Segundos entre pedidos de leitura ao dongle (0 = desliga). | `20` |
| `report_period_ms` | Período de envio autónomo que o add-on diz ao dongle. | `60000` |
| `dev_sn` | Nº de série devolvido no bootstrap (pode ficar o predefinido). | `REDACTED-SERIAL` |
| `log_level` | Detalhe do log (`debug` ajuda no arranque). | `info` |

### Mosquitto: criar o utilizador do add-on

Em **Definições → Pessoas → Utilizadores**, cria um utilizador (ex.: `rwb1`) e usa
esse nome/password em `mqtt_user` / `mqtt_password`. (O Mosquitto do HA aceita
utilizadores do Home Assistant por predefinição.)

### Mosquitto: aceitar o **dongle**

O dongle liga-se ao Mosquitto com estas credenciais (fixas, do próprio dongle):

- **utilizador:** o teu *DtuID* (o número que aparece na app Siseli / interface do dongle)
- **password:** o *hash* do dongle

Adiciona-as ao Mosquitto. No add-on **Mosquitto broker → Configuration**:

```yaml
logins:
  - username: "<O_TEU_DtuID>"
    password: "<O_HASH_DO_DONGLE>"
```

> Não sabes o hash? Com o add-on em `log_level: debug` e o dongle a tentar ligar,
> o Mosquitto regista a tentativa de login com o utilizador (DtuID). Em último
> caso, ativa temporariamente `anonymous: true` no Mosquitto só para arrancar.

---

## Router — encaminhar o DNS do dongle para o Pi

O dongle usa um **servidor DNS fixo** (ignora o DHCP), por isso é preciso desviar
o DNS dele no router. Como no firmware original as regras não persistem, usa o
teu mecanismo habitual (script em `/jffs/scripts/` reaplicado pelo Pi).

O dongle pergunta DNS na porta **53**, mas o add-on ouve numa **porta alta
(`8553`)** para não ocupar o `53` no Pi. Por isso a regra do router reescreve o
destino para `IP_PI:8553`.

Regras a aplicar no router (substitui o IP do dongle e do Pi):

```sh
iptables -t nat -A PREROUTING  -s <IP_DONGLE> -p udp --dport 53 -j DNAT --to-destination <IP_PI>:8553
iptables -t nat -A POSTROUTING -d <IP_PI> -p udp --dport 8553 -j MASQUERADE
```

Exemplo: `<IP_DONGLE>=192.168.10.134`, `<IP_PI>=192.168.10.251`.

> Se mudares a opção `dns_port` no add-on, usa o mesmo valor nas duas regras.

> **Porquê só o DNS?** Depois de o DNS responder "siseli → IP do Pi", o dongle
> liga-se ao Pi **diretamente** (mesma sub-rede) nas portas 80 e 1883, que o Pi
> já serve. Não são precisas mais regras.

---

## Arrancar e verificar

1. Inicia o add-on e abre o separador **Log**. Deves ver `DNS a ouvir :8553`,
   `HTTP a ouvir :80` e `MQTT ligado`.
2. **Reinicia o dongle** (corta-lhe a energia ~30 s).
3. No Log, por esta ordem: `HTTP checkin` → `HTTP findSingle` →
   `HTTP servers/mqtt` → `Sensores publicados...`.
4. Em **Definições → Dispositivos e Serviços → MQTT** aparece o dispositivo
   **EASUN RWB1** com os sensores (bateria, PV, saída, potências, SOC…).

---

## Resolução de problemas

- **Sem `HTTP checkin` no log:** o DNS do dongle não está a chegar ao Pi.
  Confirma as regras do router e que a porta 53 do Pi está acessível.
- **Chega HTTP mas não há dados:** o dongle não está a ligar ao Mosquitto —
  confirma o login do dongle no Mosquitto (secção acima).
- **Sensores sem valores / a zero:** normal se o inversor tiver PV/rede
  desligados; confirma a bateria e a saída, que estão sempre presentes.
- **Porta 80 ocupada:** garante que não tens outro servidor HTTP no Pi. O DNS já
  usa a porta alta `8553`, por isso não colide com um DNS no `53` (ex.: AdGuard).
- **`DNS a ouvir` não aparece:** a `dns_port` pode estar ocupada; muda-a nas
  opções e ajusta a regra do router em conformidade.

---

## Repor o funcionamento com a cloud

Remove as regras do router (`-D` em vez de `-A`) e para o add-on. O dongle, ao
reiniciar, volta a resolver os domínios reais e liga-se à cloud Siseli.
