from datetime import datetime, timedelta

# Custom Calendar Configuration
MONTH_NAMES = ["HER", "POS", "ARE", "APH", "ART",
               "HRM", "APO", "DIO", "DEM", "HES",
               "HEP", "ATH", "ZEU", "PER"]

def read_time_from_file(file_path):
    try:
        with open(file_path, 'r') as file:
            time_data = file.readline()
            return int(time_data.strip())
    except IOError as e:
        print(f"Error reading file: {e}")
        return None
    except ValueError as e:
        print(f"Error converting file data to integer: {e}")
        return None

def minecraft_time_to_custom_calendar_time(ticks):
    # Adjust the ratio for 420-day year
    seconds_per_tick = 24 * 60 * 60 / 24000
    total_seconds = ticks * seconds_per_tick
    total_seconds += 6 * 60 * 60  # Add 6 hours
    total_days = int(total_seconds // (24 * 60 * 60))

    # Calculate the custom calendar date
    year = total_days // 420 + 20  # Starting from year 20
    day_of_year = total_days % 420
    month_index = int(day_of_year // 30)
    month_day = day_of_year % 30 + 1  # Day of the month
    week = (month_day - 1) // 6 + 1
    day_of_week = (month_day - 1) % 6 + 1

    # Calculate time of day
    hours = int(total_seconds % (24 * 60 * 60) // 3600)
    minutes = int(total_seconds % 3600 // 60)

    # Format the custom date-time string
    date_str = f"{month_day:02d} {MONTH_NAMES[month_index]} {year}"
    time_str = f"{hours:02d}:{minutes:02d}"
    time_str = time_str.rjust(len(date_str))
    return f"{date_str}\n\n{time_str}"

def current():
    time_ticks = read_time_from_file('/app/data/time.txt')
    if time_ticks is not None:
        return minecraft_time_to_custom_calendar_time(time_ticks)
    else:
        return None

def current_format():
    current_time = current()
    if current_time is not None:
        return current_time
    else:
        return "Time data not available"
