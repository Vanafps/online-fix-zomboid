# Project Zomboid Build 42+ NoSteam & Spacewar Online Fix

[English](#english) | [Русский](#русский)

---

## English

A complete solution for hosting and playing Project Zomboid (Build 42+) on pirated / NoSteam clients (using Steam AppID `480` - Spacewar). 

This project solves the issue of the local dedicated server not appearing or failing to connect due to Steam authentication limits when using a VPS relay, and adds custom server query support to the in-game multiplayer browser.

### Components

1. **VPS Tunnel Server (`src/server/zomboid_tunnel_server.py`)**: Runs on a public VPS, opens UDP ports (16261, 16262) for players, and tunnels all traffic over a single TCP connection to the host machine.
2. **Client Tunnel (`src/client/zomboid_tunnel_client.py`)**: Runs on the host machine running the dedicated server, connects to the VPS, and forwards traffic locally to port 16261/16262.
3. **UI Patch (`src/client/MultiplayerUI.lua`)**: Replaces the standard game file to inject custom servers from `servers.json`, query pings and players in the background, and dynamically update the server list.
4. **Scraper (`src/client/scrape_pirate_servers.py`)**: Dynamically queries public monitors (like wargm.ru) to find compatible NoSteam / Spacewar-friendly servers, filters out licensed `Steam=true` servers, and updates the local list.

---

### Installation & Setup

#### 1. VPS Setup (Server side)
Upload `src/server/zomboid_tunnel_server.py` to your public VPS and run it:
```bash
python zomboid_tunnel_server.py
```
*Note: Make sure TCP port 26261 and UDP ports 16261, 16262 are open in the VPS firewall.*

#### 2. Local Server Setup (Client side)
1. Run your Project Zomboid dedicated server locally on port 16261 (with `Steam=false` or using the `-nosteam` launch argument).
2. Edit `zomboid_tunnel_client.py` and replace `VPS_IP` with your VPS IP address.
3. Run the client tunnel on the server host machine:
   ```bash
   python zomboid_tunnel_client.py
   ```

#### 3. Client UI Patch (Player side)
1. Replace the file `media/lua/client/OptionScreens/MultiplayerUI.lua` in your game directory with the modified one from `src/client/MultiplayerUI.lua`.
2. Run `scrape_pirate_servers.py` once to generate a clean, pirate-friendly list in `C:\Users\<Username>\Zomboid\Lua\servers.json`.
3. Launch the game through Steam (using the Spacewar 480 overlay) and open the **INTERNET** tab. Your server and all other scraped NoSteam servers will appear automatically with active pings.

---

---

## Русский

Готовое решение для хостинга и игры в Project Zomboid (Build 42+) на пиратских / NoSteam клиентах (использующих Steam AppID `480` - Spacewar). 

Этот проект решает проблему, когда локальный выделенный сервер не отображается или не подключается из-за ограничений аутентификации Steam при трансляции через VPS, а также добавляет автоматический опрос пинга и игроков для пользовательских серверов во внутриигровом браузере.

### Компоненты

1. **VPS Туннель-Сервер (`src/server/zomboid_tunnel_server.py`)**: Запускается на VPS, открывает входящие UDP-порты (16261, 16262) для игроков и туннелирует трафик через одно TCP-соединение на домашний ПК.
2. **Клиент Туннеля (`src/client/zomboid_tunnel_client.py`)**: Запускается на домашнем ПК с выделенным сервером, подключается к VPS и перенаправляет трафик локально на порты 16261/16262.
3. **Патч Интерфейса (`src/client/MultiplayerUI.lua`)**: Заменяет стандартный файл игры. Позволяет загружать сервера из файла `servers.json`, опрашивать их пинг и игроков в фоновом режиме и динамически обновлять списки.
4. **Скрапер (`src/client/scrape_pirate_servers.py`)**: Сканирует публичные мониторинги (например, wargm.ru), опрашивает найденные серверы через сетевые A2S-запросы, отсеивает лицензионные серверы (`Steam=true`) и сохраняет только совместимые NoSteam / Spacewar серверы.

---

### Установка и Настройка

#### 1. Настройка VPS (Серверная часть)
Загрузите файл `src/server/zomboid_tunnel_server.py` на ваш VPS и запустите его:
```bash
python zomboid_tunnel_server.py
```
*Убедитесь, что TCP-порт 26261 и UDP-порты 16261, 16262 открыты в брандмауэре вашего VPS.*

#### 2. Настройка Локального Сервера (Клиентская часть туннеля)
1. Запустите выделенный сервер Project Zomboid локально на порту 16261 (настройте `Steam=false` в `servertest.ini` или запустите с флагом `-nosteam`).
2. Отредактируйте `zomboid_tunnel_client.py`, указав IP вашего VPS в переменной `VPS_IP`.
3. Запустите скрипт туннеля на машине, где крутится сервер:
   ```bash
   python zomboid_tunnel_client.py
   ```

#### 3. Патч Клиента (Для игроков)
1. Замените файл `media/lua/client/OptionScreens/MultiplayerUI.lua` в папке с вашей игрой на модифицированный файл из `src/client/MultiplayerUI.lua`.
2. Запустите скрипт `scrape_pirate_servers.py`, чтобы сгенерировать чистый список пиратских серверов в папке `C:\Users\<Имя_Пользователя>\Zomboid\Lua\servers.json`.
3. Запустите игру через Steam (под AppID 480) и откройте вкладку **«ИНТЕРНЕТ»**. Ваш сервер и другие NoSteam серверы будут автоматически отображаться с активным пингом и онлайном.
