from datetime import datetime, timedelta

def read_time_from_file(file_path):
    try:
        with open(file_path, 'r') as file:
            time_data = file.readline()
            return int(time_data.strip().split('=')[1])
    except IOError as e:
        print(f"Error reading file: {e}")
        return None

def minecraft_time_to_real_time(ticks):
    # There are 24000 ticks in a Minecraft day which is equivalent to 24 hours
    seconds_per_tick = 24 * 60 * 60 / 24000
    real_time_seconds = ticks * seconds_per_tick

    # Minecraft day 1, 6:00 AM corresponds to the 0th tick
    start_time = datetime(year=1, month=1, day=1, hour=6)
    return start_time + timedelta(seconds=real_time_seconds)

def current():
    time_ticks = read_time_from_file('path/to/time.txt')  # Update this with the correct path
    if time_ticks is not None:
        return minecraft_time_to_real_time(time_ticks)
    else:
        return None

def current_format():
    current_time = current()
    if current_time is not None:
        date = current_time.strftime("%d %b %Y ANP")
        time = current_time.strftime("%H:%M")
        time = time.rjust(len(date))
        return f"{date}\n\n{time}"
    else:
        return "Time data not available"
