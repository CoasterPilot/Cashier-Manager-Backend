def read_config_value(filename, key):
    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            # leere Zeilen oder Kommentare überspringen
            if not line or line.startswith("#"):
                continue

            if line.startswith(key + "="):
                return line.split("=", 1)[1].strip()

    return None