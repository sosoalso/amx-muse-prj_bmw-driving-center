# ---------------------------------------------------------------------------- #
import asyncio
import binascii
import json

from buttonhandler import ButtonHandler
from lib_tp import (
    tp_add_watcher,
    tp_set_button,
    tp_set_button_in_range,
    tp_set_button_text_unicode,
    tp_set_page,
)
from mojo import context
from networkmanager import UdpClient
from uimenu import UIMenu
from userdata import UserData

# ---------------------------------------------------------------------------- #
user_data = UserData()
# ---------------------------------------------------------------------------- #
DV_MUSE = context.devices.get("idevice")
# ---------------------------------------------------------------------------- #
DV_RELAY = DV_MUSE.relay
# ---------------------------------------------------------------------------- #
DV_SERIAL_BLU = DV_MUSE.serial[1]
# ---------------------------------------------------------------------------- #
DV_SERIAL_LIGHTING = DV_MUSE.serial[2]
# ---------------------------------------------------------------------------- #
# DV_LED_02 = context.devices.get("novastar-h-03")
DV_LED_02 = UdpClient("DV_LED_02", "192.168.1.72", 6000)
# ---------------------------------------------------------------------------- #
# DV_TP_10001 = context.devices.get("AMX-10001")
# DV_TP_10002 = context.devices.get("AMX-10002")
# DV_TP_10003 = context.devices.get("AMX-10003")
DV_TP_10004 = context.devices.get("AMX-10004")
DV_TP_10005 = context.devices.get("AMX-10005")
# ---------------------------------------------------------------------------- #
# TP_LIST = [DV_TP_10001, DV_TP_10002, DV_TP_10003, DV_TP_10004]
TP_LIST = [DV_TP_10004, DV_TP_10005]
# ---------------------------------------------------------------------------- #
# ui_menu_10001 = UIMenu(DV_TP_10001)
# ui_menu_10002 = UIMenu(DV_TP_10002)
# ui_menu_10003 = UIMenu(DV_TP_10003)
ui_menu_10004 = UIMenu(DV_TP_10004)
ui_menu_10004 = UIMenu(DV_TP_10005)


# ---------------------------------------------------------------------------- #
def set_relay(idx_ch, state):
    DV_RELAY[idx_ch].state.value = state


# ---------------------------------------------------------------------------- #
def power_on_button_event():
    asyncio.run(power_on_event(wait_time=100))


# ---------------------------------------------------------------------------- #
def power_off_button_event():
    asyncio.run(power_off_event(wait_time=100))


# ---------------------------------------------------------------------------- #
async def power_on_event(wait_time):
    for tp in TP_LIST:
        tp_set_button_text_unicode(tp, 1, 1, "시스템 구동중...")
        tp_set_page(tp, "02")
    set_relay(1, True)
    # ---------------------------------------------------------------------------- #
    for i in range(wait_time + 1):
        await asyncio.sleep(0.1)
    await asyncio.sleep(1.0)
    for tp in TP_LIST:
        tp_set_page(tp, "01")


# ---------------------------------------------------------------------------- #
async def power_off_event(wait_time):
    for tp in TP_LIST:
        tp_set_button_text_unicode(tp, 1, 1, "시스템 종료중...")
        tp_set_page(tp, "02")
    set_relay(1, False)
    for i in range(wait_time + 1):
        await asyncio.sleep(0.1)
    await asyncio.sleep(1.0)
    for tp in TP_LIST:
        tp_set_page(tp, "01")


# ---------------------------------------------------------------------------- #
def tp_add_main_menu_btn(evt):
    tp = evt.source
    btn_power_on = ButtonHandler()
    btn_power_off = ButtonHandler()
    btn_power_on.add_event_handler("push", power_on_button_event)
    btn_power_off.add_event_handler("push", power_off_button_event)
    tp_add_watcher(tp, 1, 1, btn_power_on.handle_event)
    tp_add_watcher(tp, 1, 2, btn_power_off.handle_event)


def ui_refresh_relay_state(*args):
    value = DV_RELAY[0].state.value
    for tp in TP_LIST:
        tp_set_button(tp, 1, 1, value)


# ---------------------------------------------------------------------------- #
DV_RELAY[0].state.watch(ui_refresh_relay_state)
# ---------------------------------------------------------------------------- #
# SECTION - BLU
# ---------------------------------------------------------------------------- #
blu_last_recall_preset_index = int(user_data.get_value("blu_last_recall_preset_index") or 0)


# ---------------------------------------------------------------------------- #
def blu_recall_preset(preset_index, *args):
    global blu_last_recall_preset_index
    # DV_SERIAL_BLU.send(bytes([0x02, 0x8C, 0x00, 0x00, 0x00, blu_last_recall_preset_index + 0x8B, 0x03]))
    if preset_index == 1:
        DV_SERIAL_BLU.send(binascii.unhexlify("028C000000008C03"))
    elif preset_index == 2:
        DV_SERIAL_BLU.send(binascii.unhexlify("028C000000018D03"))
    elif preset_index == 3:
        DV_SERIAL_BLU.send(binascii.unhexlify("028C000000028E03"))
    elif preset_index == 4:
        DV_SERIAL_BLU.send(binascii.unhexlify("028C000000038F03"))
    blu_last_recall_preset_index = preset_index
    user_data.set_value("blu_last_recall_preset_index", blu_last_recall_preset_index)
    # user_data.set_default_option("blu_last_recall_preset_index", blu_last_recall_preset_index)
    print(blu_last_recall_preset_index)
    ui_refresh_blu_recall_preset_button()


# ---------------------------------------------------------------------------- #
def tp_add_blu_preset_recall_btn(evt):
    tp = evt.source
    for index in range(1, 2 + 1):
        preset_recall_btn = ButtonHandler()
        preset_recall_btn.add_event_handler("push", lambda preset_index=index: blu_recall_preset(preset_index))
        tp_add_watcher(tp, 5, index, preset_recall_btn.handle_event)


# ---------------------------------------------------------------------------- #
def ui_refresh_blu_recall_preset_button(*args):
    global blu_last_recall_preset_index
    for tp in TP_LIST:
        tp_set_button_in_range(tp, 5, 1, 4, blu_last_recall_preset_index)


# ---------------------------------------------------------------------------- #
# SECTION - NOVASTAR H SERIES
# ---------------------------------------------------------------------------- #
led_control_cmd_set_load_preset = [{"cmd": "W0605", "deviceId": 0, "screenId": 0, "presetId": 0}]
led_control_cmd_set_freeze = [{"cmd": "W041A", "screenId": 0, "enable": 0}]
# ---------------------------------------------------------------------------- #
led_last_preset_index = user_data.get_value("led_last_preset_index" or 0)


# ---------------------------------------------------------------------------- #
def led_set_freeze(deviceId, screenId, enable):
    cmd_json = led_control_cmd_set_load_preset.copy()
    cmd_json[0]["deviceId"] = deviceId
    cmd_json[0]["screenId"] = screenId
    if enable is True:
        cmd_json[0]["enable"] = 1
    else:
        cmd_json[0]["enable"] = 0
    DV_LED_02.send(json.dumps(cmd_json))
    context.log.info(f"led_set_freeze >> {cmd_json}")


# ---------------------------------------------------------------------------- #
def led_load_preset(deviceId, screenId, preset_index):
    global led_last_preset_index
    cmd_json = led_control_cmd_set_load_preset.copy()
    cmd_json[0]["deviceId"] = deviceId
    cmd_json[0]["screenId"] = screenId
    cmd_json[0]["presetId"] = preset_index - 1
    DV_LED_02.send(json.dumps(cmd_json))
    context.log.info(f"led_load_preset >> {cmd_json}")
    led_last_preset_index = preset_index
    user_data.set_value("led_last_preset_index", led_last_preset_index)
    ui_refresh_led_recall_preset_button()


# ---------------------------------------------------------------------------- #
def tp_add_led_preset_recall_btn(evt):
    tp = evt.source
    for index in range(1, 5 + 1):
        preset_recall_btn = ButtonHandler()
        preset_recall_btn.add_event_handler("push", lambda preset_index=index: led_load_preset(0, 0, preset_index))
        tp_add_watcher(tp, 5, 10 + index, preset_recall_btn.handle_event)


# ---------------------------------------------------------------------------- #
def ui_refresh_led_recall_preset_button(*args):
    for tp in TP_LIST:
        tp_set_button_in_range(tp, 5, 11, 5, led_last_preset_index)


# ---------------------------------------------------------------------------- #
# SECTION - LIGHTING
# ---------------------------------------------------------------------------- #
lighting_last_preset_index = user_data.get_value("lighting_last_preset_index") or 0


def lighting_make_command(preset_index):
    return f":1101A{preset_index:03d}00005"


# ---------------------------------------------------------------------------- #
def lighting_recall_preset(preset_index, *args):
    global lighting_last_preset_index
    print("lighting_recall_preset")
    lighting_last_preset_index = preset_index
    user_data.set_value("lighting_last_preset_index", lighting_last_preset_index)
    command = lighting_make_command(preset_index)
    DV_SERIAL_LIGHTING.send(command)
    ui_refresh_lighting_recall_preset_button()


# ---------------------------------------------------------------------------- #
def tp_add_lighting_preset_recall_btn(evt):
    tp = evt.source
    for index in range(1, 25 + 1):
        preset_recall_btn = ButtonHandler()
        preset_recall_btn.add_event_handler("push", lambda preset_index=index: lighting_recall_preset(preset_index))
        tp_add_watcher(tp, 5, index + 30, preset_recall_btn.handle_event)


# ---------------------------------------------------------------------------- #
def ui_refresh_lighting_recall_preset_button(*args):
    global blu_last_recall_preset_index
    for tp in TP_LIST:
        tp_set_button_in_range(tp, 5, 30 + 1, 30, lighting_last_preset_index)


# ---------------------------------------------------------------------------- #
# INFO - 하드웨어 설정
# ---------------------------------------------------------------------------- #
def set_serial_baud_rate(evt):
    DV_SERIAL_BLU.setCommParams("115200", 8, 1, "NONE", "232")
    DV_SERIAL_LIGHTING.setCommParams("9600", 8, 1, "NONE", "232")


DV_MUSE.online(set_serial_baud_rate)


# ---------------------------------------------------------------------------- #
# INFO - TP 이벤트 등록
# ---------------------------------------------------------------------------- #
def handle_tp_event(*args):
    for tp in TP_LIST:
        tp.online(tp_add_main_menu_btn)
        tp.online(tp_add_blu_preset_recall_btn)
        tp.online(tp_add_lighting_preset_recall_btn)
        tp.online(tp_add_led_preset_recall_btn)
        tp.online(ui_refresh_relay_state)
        tp.online(ui_refresh_blu_recall_preset_button)
        tp.online(ui_refresh_led_recall_preset_button)
        tp.online(ui_refresh_lighting_recall_preset_button)


DV_MUSE.online(handle_tp_event)
# ---------------------------------------------------------------------------- #
context.run(globals())
# ---------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------- #