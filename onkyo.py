import eiscp

def try_get_devices():
    devices = {}
    try:
        for receiver in eiscp.eISCP.discover(timeout=5):
            devices[receiver.identifier] = receiver.host
    except Exception as e:
        print(f"### Error getting Onkyo devices: {e}")
    return devices

def try_turn_on(receiver_ip_address):
    try:
        with eiscp.eISCP(receiver_ip_address) as receiver:
            main_power_result = receiver.command('main.power=query')
            if isinstance(main_power_result, tuple):
                if main_power_result[1][1]=="off":
                    receiver.command('power on')
    except Exception as e:
        print(f"### Error turning on Onkyo: {e}")

def try_turn_off(receiver_ip_address):
    try:
        with eiscp.eISCP(receiver_ip_address) as receiver:
            main_power_result = receiver.command('main.power=query')
            if isinstance(main_power_result[1], tuple):
                if main_power_result[1][1]=="on":
                    receiver.command('power off')
            elif main_power_result[1]=="on":
                receiver.command('power off')
    except Exception as e:
        print(f"### Error turning off Onkyo: {e}")

def try_set_source(receiver_ip_address, source):
    try:
        with eiscp.eISCP(receiver_ip_address) as receiver:
            main_power_result = receiver.command(f'main.source={source}')
    except Exception as e:
        print(f"### Error setting Onkyo source: {e}")

def try_set_volume(receiver_ip_address, volume):
    try:
        with eiscp.eISCP(receiver_ip_address) as receiver:
            main_power_result = receiver.command(f'main.volume={volume}')
    except Exception as e:
        print(f"### Error setting Onkyo volume: {e}")
