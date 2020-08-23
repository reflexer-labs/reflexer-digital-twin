def did_deviation_update(error, latest_devation_type):
    if (error >= 0 and latest_devation_type == -1):
        return False
    elif (error < 0 and latest_devation_type == 1):
        return False
    else:
        return True
