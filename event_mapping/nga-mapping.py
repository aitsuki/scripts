server_events = []

with open("nga-events.data") as f:
    for line in f:
        line = line.rstrip()
        server_events.append(line)

with open("nga-events-gen.data", "w+") as f:
    for event in server_events:
        event = event.replace("NGP", "GenC")
        event = event.replace("_exit", "_999")
        event = event.replace("_Click_", "_Bt_")
        event = event.replace("_Request_", "_win_")
        event = event.replace("_Error_", "_fail_")
        event = event.replace("_Input_", "_ent_")
        event = event.replace("_Upload_", "_app_")
        f.write(event + "\n")