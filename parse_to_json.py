import os
import csv
import json
import time
import sqlite3

FILE_PATH = "C:\\Users\\Pavan G\\Downloads\\fs-watcher_DATA\\fs-watcher-test-files\\chassis_dyno-20250704T102708Z-1-001\\chassis_dyno\\245-kg\\Roll-000085.me"  
POSITION_TRACK_FILE = "last_position.txt"
CLOUD_ENDPOINT = "http://172.105.41.167/pvlabs/raw_data.php" 
SEND_INTERVAL = 5 # seconds

def add_to_database(list_of_json):
    conn=sqlite3.connect("TEST_JSON.db")
    cursor=conn.cursor()

    cursor.execute("""
            CREATE TABLE IF NOT EXISTS table2(
            data TEXT 
                                             )
""")

    # cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")                       #To view how many tables are present in the db
    # tables=cursor.fetchall()
    # print("Tables in Database")                                            
    # for table in tables:
    #     print(table[0])

    for json_data_db in list_of_json:
        cursor.execute("INSERT INTO table2 (data) VALUES (?)",(json.dumps(json_data_db),))       # To insert json data as a TEXT into db       
        conn.commit()
    conn.commit()


    # cursor.execute("SELECT COUNT(*) FROM table2")
    # row_count = cursor.fetchone()[0]                                                              # To view number of rows present in the db 
    # print("Number of rows in db:", row_count)

    cursor.execute("SELECT * FROM table2")
    view_data=cursor.fetchall()
    print(f"Number of Rows in table2:{len(view_data)}")
    # for data in view_data:                           # To print all the rows in the table
    #     print(data)
    conn.commit()
    
    # cursor.execute("DELETE FROM table2;")              # To Delete all the row of a table 
    # conn.commit()



main_list=[]
attributes_dict={}
class global_variable():
    header_row=''

def read_last_position():
    if not os.path.exists(POSITION_TRACK_FILE):
        return 0
    else:
        with open(POSITION_TRACK_FILE,'r') as f:
            return int(f.read().strip())

def write_last_position(pos):
    with open(POSITION_TRACK_FILE, 'w') as f:
        f.write(str(pos))

def read_new_lines(file_path, start_pos):
    with open(file_path, 'r') as f:
        f.seek(start_pos)
        lines = f.readlines()
        new_pos = f.tell()
    return lines, new_pos

def parse_csv_lines_to_json(lines):
    temp_list=[]
    if not lines:
        return []
    if last_pos == 0:
        reader = csv.DictReader(lines)
        return [row for row in reader]
    else:
        for val in lines:
            if  not (val.strip()=='\n' and val.strip()=='' and val.strip()=='\t'):
                attributes_dict={}
                attributes_dict[global_variable.header_row]=val.strip()
                temp_list.append(attributes_dict)
            else:
                continue
        return temp_list


# def send_to_cloud(main_list):
#     try:
#         for json_data in main_list:
#             response = requests.post(CLOUD_ENDPOINT, json=json_data)
#             response.raise_for_status()
#             print(f"Sent {len(json_data)} records successfully.")
#     except Exception as e:
#         print(f"Error sending data: {e}")


def json_list_conversion(json_data):
    for json_temp in json_data:
        for keys ,values in json_temp.items():
            if keys is None:
                continue
            else:
                global_variable.header_row=keys.strip()
                key_temp_list=keys.strip().split(";")
            if values is None:
                continue
            else:
                value_temp_list=values.strip().split(";")

            json_list_dict={}
            for key_val , value_val in zip(key_temp_list ,value_temp_list):
                try:
                    if key_val =='' or value_val == '':
                        continue                            
                    else:
                        json_list_dict[key_val.strip()]=float(value_val.strip())
                except ValueError:
                    json_list_dict[key_val.strip()]=value_val.strip()

            main_list.append(json_list_dict)


   
while True:
    try:                
        last_pos = read_last_position()
        lines, new_pos = read_new_lines(FILE_PATH, last_pos)
        if lines:
            json_data_dict = parse_csv_lines_to_json(lines)
            json_list_conversion(json_data_dict)
            # if main_list:
            #     send_to_cloud(main_list)
        print(f"Last postion of the file {last_pos}")
        write_last_position(new_pos)
        add_to_database(main_list)
        if new_pos != last_pos:
            for i in main_list:
                print(i)
        main_list=[]
        time.sleep(SEND_INTERVAL)

    except KeyboardInterrupt:
        print("END")
        write_last_position(0)
        break